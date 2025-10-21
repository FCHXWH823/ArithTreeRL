#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dataset Generation for LLM Finetuning/GRPO Training

This script generates a dataset where each sample consists of:
- Input: Current state representation (cell_map, level, size, etc.)
- Output: Optimization action that leads to an improved state

The dataset can be used for:
1. Supervised finetuning (SFT) to teach LLMs to propose optimization actions
2. Guided Reward Proximal Optimization (GRPO) training with OpenR1 framework
"""

import sys
import math
import random
import numpy as np
import argparse
import copy
import torch
import time
import os
import json
from typing import Dict, List, Tuple, Any


# Import State class and utilities from adder.py
# We'll use the same State class but in dataset generation mode
class DatasetState:
    """Extended State class for dataset generation"""
    
    def __init__(self, level, size, cell_map, level_map, min_map,
                 step_num, action, reward, input_bit):
        self.current_value = 0.0
        self.current_round_index = 0
        self.input_bit = input_bit
        self.cumulative_choices = []
        self.level = level
        self.cell_map = cell_map
        self.level_map = level_map
        self.min_map = min_map
        self.reward = reward
        self.size = size
        self.level_bound = int(math.log2(input_bit) + 1)
        
        assert self.cell_map.sum() - self.input_bit == self.size
        
        up_tri_mask = np.triu(torch.ones(self.input_bit, self.input_bit), k=1)
        self.prob = np.ones((2, self.input_bit, self.input_bit))
        self.prob[0] = np.where(self.cell_map >= 1.0, 0, self.prob[0])
        self.prob[0] = np.where(up_tri_mask >= 1.0, 0, self.prob[0])
        self.prob[1] = np.where(self.min_map <= 0.0, 0, self.prob[1])
        self.prob[1] = np.where(up_tri_mask >= 1.0, 0, self.prob[1])
        
        self.available_choice = int(self.prob[1].sum())
        self.available_choice_list = [0] * self.available_choice
        
        cnt = 0
        for i in range(input_bit):
            for j in range(input_bit):
                if self.prob[1, i, j] == 1:
                    self.available_choice_list[cnt] = self.input_bit ** 2 + i * self.input_bit + j
                    cnt += 1
        
        self.action = action
        self.step_num = step_num
    
    def to_text_representation(self) -> str:
        """Convert state to text representation for LLM input"""
        text_parts = []
        
        # Basic state information
        text_parts.append(f"Input Bits: {self.input_bit}")
        text_parts.append(f"Current Level: {self.level}")
        text_parts.append(f"Current Size: {self.size}")
        text_parts.append(f"Level Bound: {self.level_bound}")
        text_parts.append(f"Available Actions: {self.available_choice}")
        
        # Cell map representation (compact format)
        text_parts.append("\nCell Map:")
        for i in range(self.input_bit):
            row = []
            for j in range(self.input_bit):
                if self.cell_map[i, j] == 1:
                    row.append(f"({i},{j})")
            if row:
                text_parts.append(f"  Row {i}: {' '.join(row)}")
        
        # Available actions
        if self.available_choice > 0:
            text_parts.append("\nPossible Optimization Actions:")
            for idx, action in enumerate(self.available_choice_list[:10]):  # Show first 10
                x = (action % (self.input_bit ** 2)) // self.input_bit
                y = (action % (self.input_bit ** 2)) % self.input_bit
                text_parts.append(f"  Action {idx}: Remove cell at position ({x},{y})")
            if self.available_choice > 10:
                text_parts.append(f"  ... and {self.available_choice - 10} more actions")
        
        return "\n".join(text_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary format"""
        return {
            "input_bit": int(self.input_bit),
            "level": int(self.level),
            "size": int(self.size),
            "level_bound": int(self.level_bound),
            "available_choice": int(self.available_choice),
            "cell_map": self.cell_map.tolist(),
            "level_map": self.level_map.tolist(),
            "min_map": self.min_map.tolist(),
            "available_actions": [int(a) for a in self.available_choice_list],
            "step_num": int(self.step_num),
            "reward": float(self.reward)
        }
    
    def is_terminal(self):
        return self.available_choice == 0
    
    def legalize(self, cell_map, min_map, start_bit=1):
        """Same as adder.py legalize function"""
        for i in range(self.input_bit):
            min_map[i, 0] = 0
            min_map[i, i] = 0
        activate_x_list = [start_bit]
        for x in range(self.input_bit-1, 0, -1):
            last_y = x
            for y in range(x-1, -1, -1):
                if cell_map[x, y] == 1:
                    if cell_map[last_y-1, y] == 0:
                        assert last_y - 1 <= start_bit
                        next_bit = last_y - 1
                        cell_map[last_y-1, y] = 1
                        activate_x_list.append(next_bit)
                    if min_map[last_y-1, y] == 1:
                        min_map[last_y-1, y] = 0
                    last_y = y
        return cell_map, min_map, activate_x_list
    
    def update_level_map(self, cell_map, level_map, start_bit=1, activate_x_list=[]):
        """Same as adder.py update_level_map function"""
        activate_x_list.reverse()
        min_x = min(activate_x_list)
        for x in range(min_x, self.input_bit):
            level_map[x, :] = 0
            level_map[x, x] = 1
            last_y = x
            for y in range(x-1, -1, -1):
                if cell_map[x, y] == 1:
                    level_map[x, y] = max(level_map[x, last_y], level_map[last_y-1, y]) + 1
                    last_y = y
        return level_map
    
    def get_next_state_with_action(self, action: int):
        """Generate next state given a specific action"""
        if action not in self.available_choice_list:
            return None
        
        action_type = action // (self.input_bit ** 2)
        x = (action % (self.input_bit ** 2)) // self.input_bit
        y = (action % (self.input_bit ** 2)) % self.input_bit
        
        if self.min_map[x, y] != 1:
            return None
        
        next_cell_map = np.copy(self.cell_map)
        next_level_map = np.copy(self.level_map)
        next_min_map = np.copy(self.cell_map)
        
        next_cell_map[x, y] = 0
        next_min_map[x, y] = 0
        next_cell_map, next_min_map, activate_x_list = self.legalize(
            next_cell_map, next_min_map, start_bit=x
        )
        next_level_map = self.update_level_map(
            next_cell_map, next_level_map, start_bit=x, activate_x_list=activate_x_list
        )
        next_level = next_level_map.max()
        next_size = next_cell_map.sum() - self.input_bit
        next_step_num = self.step_num + 1
        
        # Check if action is valid (improves or maintains quality)
        # Condition from original adder.py: allow if:
        # 1. Level doesn't increase AND size doesn't increase (maintaining or improving both)
        # 2. Level decreases (even if size stays same)
        # 3. Level is within bound AND size doesn't increase
        if not ((next_level <= self.level and next_size <= self.size) or
                (next_level < self.level and next_size <= self.size) or
                (next_level <= self.level_bound and next_size <= self.size)):
            return None
        
        reward = -1 + self.input_bit * (next_level - self.level)
        next_state = DatasetState(
            next_level, next_size, next_cell_map, next_level_map, next_min_map,
            next_step_num, action, reward, self.input_bit
        )
        return next_state
    
    def get_all_valid_transitions(self) -> List[Tuple[int, 'DatasetState']]:
        """Get all valid action-nextstate pairs from current state"""
        transitions = []
        for action in self.available_choice_list[:]:  # Make a copy to iterate safely
            next_state = self.get_next_state_with_action(action)
            if next_state is not None:
                transitions.append((action, next_state))
        return transitions


def action_to_text(action: int, input_bit: int) -> str:
    """Convert action integer to text description"""
    action_type = action // (input_bit ** 2)
    x = (action % (input_bit ** 2)) // input_bit
    y = (action % (input_bit ** 2)) % input_bit
    return f"Remove cell at position ({x},{y})"


def action_to_dict(action: int, input_bit: int) -> Dict[str, Any]:
    """Convert action to dictionary format"""
    action_type = action // (input_bit ** 2)
    x = (action % (input_bit ** 2)) // input_bit
    y = (action % (input_bit ** 2)) % input_bit
    return {
        "action": int(action),
        "action_type": int(action_type),
        "position": {"x": int(x), "y": int(y)},
        "description": action_to_text(action, input_bit)
    }


def get_brent_kung_init(input_bit: int) -> DatasetState:
    """Initialize with Brent-Kung adder structure"""
    def update_level_map(cell_map, level_map, input_bit):
        level_map.fill(0)
        level_map[0, 0] = 1
        for x in range(1, input_bit):
            level_map[x, x] = 1
            last_y = x
            for y in range(x-1, -1, -1):
                if cell_map[x, y] == 1:
                    level_map[x, y] = max(level_map[x, last_y], level_map[last_y-1, y]) + 1
                    last_y = y
        return level_map

    cell_map = np.zeros((input_bit, input_bit))
    level_map = np.zeros((input_bit, input_bit))
    for i in range(input_bit):
        cell_map[i, i] = 1
        cell_map[i, 0] = 1
    t = 2
    while t < input_bit:
        for i in range(t-1, input_bit, t):
            cell_map[i, i-t+1] = 1
        t *= 2
    level_map = update_level_map(cell_map, level_map, input_bit)
    level = level_map.max()
    min_map = copy.deepcopy(cell_map)
    for i in range(input_bit):
        min_map[i, i] = 0
        min_map[i, 0] = 0
    size = cell_map.sum() - input_bit
    state = DatasetState(level, size, cell_map, level_map, min_map, 0, 0, 0, input_bit)
    return state


def get_normal_init(input_bit: int) -> DatasetState:
    """Initialize with normal (ripple-carry) adder structure"""
    cell_map = np.zeros((input_bit, input_bit))
    level_map = np.zeros((input_bit, input_bit))
    for i in range(input_bit):
        cell_map[i, i] = 1
        cell_map[i, 0] = 1
        level_map[i, i] = 1
        level_map[i, 0] = i+1
    level = level_map.max()
    min_map = copy.deepcopy(cell_map)
    for i in range(input_bit):
        min_map[i, i] = 0
        min_map[i, 0] = 0
    size = cell_map.sum() - input_bit
    state = DatasetState(level, size, cell_map, level_map, min_map, 0, 0, 0, input_bit)
    return state


def get_sklansky_init(input_bit: int) -> DatasetState:
    """Initialize with Sklansky adder structure"""
    cell_map = np.zeros((input_bit, input_bit))
    level_map = np.zeros((input_bit, input_bit))
    for i in range(input_bit):
        cell_map[i, i] = 1
        level_map[i, i] = 1
        t = i
        now = i
        x = 1
        level = 1
        while t > 0:
            if t % 2 == 1:
                last_now = now
                now -= x
                cell_map[i, now] = 1
                level_map[i, now] = max(level, level_map[last_now-1, now]) + 1
                level += 1
            t = t // 2
            x *= 2
    
    min_map = copy.deepcopy(cell_map)
    for i in range(input_bit):
        min_map[i, i] = 0
        min_map[i, 0] = 0
    
    for x in range(input_bit-1, 0, -1):
        last_y = x
        for y in range(x-1, -1, -1):
            if cell_map[x, y] == 1:
                min_map[last_y-1, y] = 0
                last_y = y
    
    level = level_map.max()
    size = cell_map.sum() - input_bit
    state = DatasetState(level, size, cell_map, level_map, min_map, 0, 0, 0, input_bit)
    return state


def generate_dataset(
    input_bit: int,
    num_trajectories: int,
    max_steps_per_trajectory: int,
    output_format: str = "jsonl",
    sample_strategy: str = "all_valid",
    level_bound_delta: int = 1,
    init_type: str = "sklansky"
) -> List[Dict[str, Any]]:
    """
    Generate dataset for finetuning/GRPO
    
    Args:
        input_bit: Number of bits for the adder
        num_trajectories: Number of optimization trajectories to generate
        max_steps_per_trajectory: Maximum steps per trajectory
        output_format: Format for output ("jsonl", "json")
        sample_strategy: How to sample actions ("all_valid", "random", "best")
        level_bound_delta: Additional level bound (0 = tight, higher = more relaxed)
        init_type: Initialization type ("sklansky", "brent_kung", "normal")
    
    Returns:
        List of dataset samples
    """
    dataset = []
    
    for traj_idx in range(num_trajectories):
        print(f"Generating trajectory {traj_idx + 1}/{num_trajectories}...")
        
        # Initialize state based on init_type
        if init_type == "sklansky":
            current_state = get_sklansky_init(input_bit)
        elif init_type == "brent_kung":
            current_state = get_brent_kung_init(input_bit)
        elif init_type == "normal":
            current_state = get_normal_init(input_bit)
        else:
            raise ValueError(f"Unknown init_type: {init_type}")
        
        # Update level_bound
        current_state.level_bound = int(math.log2(input_bit) + 1 + level_bound_delta)
        
        for step in range(max_steps_per_trajectory):
            if current_state.is_terminal():
                print(f"  Trajectory {traj_idx + 1} terminated at step {step}")
                break
            
            # Get all valid transitions from current state
            transitions = current_state.get_all_valid_transitions()
            
            if not transitions:
                print(f"  No valid transitions at step {step}")
                break
            
            if sample_strategy == "all_valid":
                # Generate one sample for each valid action
                for action, next_state in transitions:
                    sample = {
                        "trajectory_id": traj_idx,
                        "step": step,
                        "state": current_state.to_dict(),
                        "state_text": current_state.to_text_representation(),
                        "action": action_to_dict(action, input_bit),
                        "next_state": next_state.to_dict(),
                        "improvement": {
                            "level_change": int(next_state.level - current_state.level),
                            "size_change": int(next_state.size - current_state.size),
                            "reward": float(next_state.reward)
                        }
                    }
                    dataset.append(sample)
                
                # Move to best next state for next iteration
                best_transition = min(
                    transitions,
                    key=lambda t: (t[1].size, t[1].level)
                )
                current_state = best_transition[1]
                
            elif sample_strategy == "random":
                # Sample one random action
                action, next_state = random.choice(transitions)
                sample = {
                    "trajectory_id": traj_idx,
                    "step": step,
                    "state": current_state.to_dict(),
                    "state_text": current_state.to_text_representation(),
                    "action": action_to_dict(action, input_bit),
                    "next_state": next_state.to_dict(),
                    "improvement": {
                        "level_change": int(next_state.level - current_state.level),
                        "size_change": int(next_state.size - current_state.size),
                        "reward": float(next_state.reward)
                    }
                }
                dataset.append(sample)
                current_state = next_state
                
            elif sample_strategy == "best":
                # Always pick the best action
                best_transition = min(
                    transitions,
                    key=lambda t: (t[1].size, t[1].level)
                )
                action, next_state = best_transition
                sample = {
                    "trajectory_id": traj_idx,
                    "step": step,
                    "state": current_state.to_dict(),
                    "state_text": current_state.to_text_representation(),
                    "action": action_to_dict(action, input_bit),
                    "next_state": next_state.to_dict(),
                    "improvement": {
                        "level_change": int(next_state.level - current_state.level),
                        "size_change": int(next_state.size - current_state.size),
                        "reward": float(next_state.reward)
                    }
                }
                dataset.append(sample)
                current_state = next_state
    
    return dataset


def convert_to_openr1_format(dataset: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Convert dataset to OpenR1 format for LLM training
    
    OpenR1 format typically uses:
    - "prompt": The input text (state description)
    - "completion": The output text (action to take)
    - "reward": Optional reward signal for GRPO
    """
    openr1_data = []
    
    for sample in dataset:
        # Create prompt from state
        prompt = f"""You are an expert in optimizing arithmetic hardware designs. Given the current state of an adder design, suggest an optimization action to improve it.

Current State:
{sample['state_text']}

Task: Propose an optimization action that will improve the design by reducing size or level while maintaining correctness.

Optimization Action:"""
        
        # Create completion from action
        completion = sample['action']['description']
        
        openr1_sample = {
            "prompt": prompt,
            "completion": completion,
            "reward": sample['improvement']['reward'],
            "metadata": {
                "trajectory_id": sample['trajectory_id'],
                "step": sample['step'],
                "level_change": sample['improvement']['level_change'],
                "size_change": sample['improvement']['size_change']
            }
        }
        openr1_data.append(openr1_sample)
    
    return openr1_data


def main():
    parser = argparse.ArgumentParser(
        description='Generate dataset for LLM finetuning/GRPO training'
    )
    parser.add_argument('--input_bit', type=int, default=8,
                        help='Number of bits for the adder')
    parser.add_argument('--num_trajectories', type=int, default=10,
                        help='Number of optimization trajectories to generate')
    parser.add_argument('--max_steps', type=int, default=50,
                        help='Maximum steps per trajectory')
    parser.add_argument('--output_dir', type=str, default='dataset',
                        help='Output directory for dataset')
    parser.add_argument('--output_format', type=str, default='jsonl',
                        choices=['json', 'jsonl'],
                        help='Output format (json or jsonl)')
    parser.add_argument('--sample_strategy', type=str, default='random',
                        choices=['all_valid', 'random', 'best'],
                        help='Strategy for sampling actions')
    parser.add_argument('--level_bound_delta', type=int, default=1,
                        help='Additional level bound (0=tight, higher=more relaxed)')
    parser.add_argument('--init_type', type=str, default='sklansky',
                        choices=['sklansky', 'brent_kung', 'normal'],
                        help='Initialization type')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed')
    parser.add_argument('--openr1_format', action='store_true',
                        help='Convert to OpenR1 format for LLM training')
    
    args = parser.parse_args()
    
    # Set random seed
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    
    print(f"Generating dataset with parameters:")
    print(f"  Input bits: {args.input_bit}")
    print(f"  Trajectories: {args.num_trajectories}")
    print(f"  Max steps per trajectory: {args.max_steps}")
    print(f"  Sample strategy: {args.sample_strategy}")
    print(f"  Level bound delta: {args.level_bound_delta}")
    print(f"  Init type: {args.init_type}")
    print(f"  Random seed: {args.seed}")
    
    # Generate dataset
    start_time = time.time()
    dataset = generate_dataset(
        input_bit=args.input_bit,
        num_trajectories=args.num_trajectories,
        max_steps_per_trajectory=args.max_steps,
        output_format=args.output_format,
        sample_strategy=args.sample_strategy,
        level_bound_delta=args.level_bound_delta,
        init_type=args.init_type
    )
    elapsed_time = time.time() - start_time
    
    print(f"\nGenerated {len(dataset)} samples in {elapsed_time:.2f} seconds")
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Save raw dataset
    raw_output_file = os.path.join(
        args.output_dir,
        f'dataset_{args.input_bit}b_{args.init_type}_{args.num_trajectories}traj_lbd{args.level_bound_delta}_{args.sample_strategy}.{args.output_format}'
    )
    
    if args.output_format == 'jsonl':
        with open(raw_output_file, 'w') as f:
            for sample in dataset:
                f.write(json.dumps(sample) + '\n')
    else:
        with open(raw_output_file, 'w') as f:
            json.dump(dataset, f, indent=2)
    
    print(f"Saved raw dataset to {raw_output_file}")
    
    # Convert to OpenR1 format if requested
    if args.openr1_format:
        openr1_data = convert_to_openr1_format(dataset)
        openr1_output_file = os.path.join(
            args.output_dir,
            f'openr1_dataset_{args.input_bit}b_{args.init_type}_{args.num_trajectories}traj_lbd{args.level_bound_delta}_{args.sample_strategy}.{args.output_format}'
        )
        
        if args.output_format == 'jsonl':
            with open(openr1_output_file, 'w') as f:
                for sample in openr1_data:
                    f.write(json.dumps(sample) + '\n')
        else:
            with open(openr1_output_file, 'w') as f:
                json.dump(openr1_data, f, indent=2)
        
        print(f"Saved OpenR1 format dataset to {openr1_output_file}")
    
    # Print statistics
    print("\nDataset Statistics:")
    print(f"  Total samples: {len(dataset)}")
    
    if dataset:
        avg_reward = sum(s['improvement']['reward'] for s in dataset) / len(dataset)
        print(f"  Average reward: {avg_reward:.4f}")
        
        size_reductions = [s['improvement']['size_change'] for s in dataset]
        avg_size_reduction = sum(size_reductions) / len(size_reductions)
        print(f"  Average size change: {avg_size_reduction:.2f}")
        
        level_changes = [s['improvement']['level_change'] for s in dataset]
        avg_level_change = sum(level_changes) / len(level_changes)
        print(f"  Average level change: {avg_level_change:.2f}")
    
    print("\nDataset generation complete!")


if __name__ == "__main__":
    main()
