#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generate_dataset.py - Dataset Generation for LLM Finetuning/GRPO Training

This module generates training datasets for LLM finetuning or GRPO (Guided Reward 
Proximal Optimization) training based on state transitions from the adder design process.

The dataset captures:
1. Current state representation (cell_map, level, size)
2. Optimization action taken
3. Resulting new state

This data can be used to train an LLM to propose optimization actions for arithmetic
circuit designs, compatible with the OpenR1 framework.
"""

import json
import numpy as np
import argparse
import os
from datetime import datetime


class DatasetGenerator:
    """
    Generator for creating training datasets from adder optimization traces.
    """
    
    def __init__(self, output_dir="dataset", dataset_name="adder_optimization"):
        """
        Initialize the dataset generator.
        
        Args:
            output_dir (str): Directory to save generated datasets
            dataset_name (str): Base name for the dataset file
        """
        self.output_dir = output_dir
        self.dataset_name = dataset_name
        self.data_samples = []
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def state_to_text(self, state, include_maps=True):
        """
        Convert a state object to text representation for LLM input.
        
        Args:
            state: State object from adder.py
            include_maps (bool): Whether to include full cell/level/min maps
            
        Returns:
            str: Text representation of the state
        """
        text = f"# Adder Design State\n"
        text += f"Input Bits: {state.input_bit}\n"
        text += f"Current Level (Depth): {int(state.level)}\n"
        text += f"Current Size (Gates): {int(state.size)}\n"
        text += f"Level Bound: {state.level_bound}\n"
        text += f"Available Actions: {state.available_choice}\n"
        
        if include_maps:
            # Add cell map representation
            text += f"\n## Cell Map ({state.input_bit}x{state.input_bit}):\n"
            for i in range(state.input_bit):
                row = " ".join([str(int(state.cell_map[i, j])) for j in range(state.input_bit)])
                text += f"{row}\n"
        
        return text
    
    def action_to_text(self, operation_info):
        """
        Convert an operation/action to text representation.
        
        Args:
            operation_info (dict): Operation information dictionary
            
        Returns:
            str: Text representation of the action
        """
        text = f"# Optimization Action\n"
        text += f"Action Type: {operation_info['action_type']}\n"
        text += f"Position: ({operation_info['position'][0]}, {operation_info['position'][1]})\n"
        text += f"Action ID: {operation_info['action']}\n"
        
        # Include legalization effects
        if 'legalization_added_cells' in operation_info and len(operation_info['legalization_added_cells']) > 0:
            text += f"Legalization Added Cells: {len(operation_info['legalization_added_cells'])}\n"
            for cell in operation_info['legalization_added_cells']:
                text += f"  - ({cell[0]}, {cell[1]})\n"
        else:
            text += f"Legalization Added Cells: 0\n"
        
        text += f"\nLevel Change: {int(operation_info['prev_level'])} -> {int(operation_info['next_level'])}\n"
        text += f"Size Change: {int(operation_info['prev_size'])} -> {int(operation_info['next_size'])}\n"
        text += f"Reward: {operation_info['reward']:.4f}\n"
        
        return text
    
    def create_training_sample(self, prev_state, next_state, operation_info):
        """
        Create a single training sample from a state transition.
        
        Args:
            prev_state: State before the action
            next_state: State after the action
            operation_info (dict): Information about the action taken
            
        Returns:
            dict: Training sample in OpenR1 compatible format
        """
        # Convert state to text representation
        input_text = self.state_to_text(prev_state, include_maps=True)
        
        # Generate the target output (the action/optimization to take)
        output_text = self.action_to_text(operation_info)
        
        # Add the resulting state summary
        output_text += f"\n# Resulting State Summary\n"
        output_text += f"New Level: {int(next_state.level)}\n"
        output_text += f"New Size: {int(next_state.size)}\n"
        
        # Create sample in a format suitable for OpenR1/LLM training
        sample = {
            "id": f"sample_{len(self.data_samples)}",
            "input": input_text,
            "output": output_text,
            "metadata": {
                "input_bit": int(prev_state.input_bit),
                "prev_level": int(operation_info['prev_level']),
                "next_level": int(operation_info['next_level']),
                "prev_size": int(operation_info['prev_size']),
                "next_size": int(operation_info['next_size']),
                "reward": float(operation_info['reward']),
                "action_id": int(operation_info['action']),
                "position": [int(operation_info['position'][0]), int(operation_info['position'][1])],
                "step": int(operation_info['step'])
            }
        }
        
        return sample
    
    def add_state_transition(self, prev_state, next_state, operation_info):
        """
        Add a state transition to the dataset.
        
        Args:
            prev_state: State before the action
            next_state: State after the action  
            operation_info (dict): Information about the action taken
        """
        sample = self.create_training_sample(prev_state, next_state, operation_info)
        self.data_samples.append(sample)
    
    def add_generation_trace(self, final_state):
        """
        Add all state transitions from a generation trace.
        
        Args:
            final_state: Final state containing the full generation_trace
        """
        if not hasattr(final_state, 'generation_trace'):
            return
        
        # We need to reconstruct states at each step
        # For now, we'll use the trace information directly
        for i, operation_info in enumerate(final_state.generation_trace):
            # Create a simplified representation
            # In a real implementation, we'd reconstruct the actual state objects
            sample = {
                "id": f"trace_{id(final_state)}_{i}",
                "input": self.action_to_text(operation_info),
                "output": f"# Result\nLevel: {operation_info['next_level']}\nSize: {operation_info['next_size']}\nReward: {operation_info['reward']:.4f}",
                "metadata": {
                    "input_bit": int(final_state.input_bit),
                    "prev_level": int(operation_info['prev_level']),
                    "next_level": int(operation_info['next_level']),
                    "prev_size": int(operation_info['prev_size']),
                    "next_size": int(operation_info['next_size']),
                    "reward": float(operation_info['reward']),
                    "action_id": int(operation_info['action']),
                    "position": [int(operation_info['position'][0]), int(operation_info['position'][1])],
                    "step": int(operation_info['step'])
                }
            }
            self.data_samples.append(sample)
    
    def save_dataset(self, format="jsonl"):
        """
        Save the dataset to file.
        
        Args:
            format (str): Output format - 'jsonl' or 'json'
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "jsonl":
            filename = os.path.join(self.output_dir, f"{self.dataset_name}_{timestamp}.jsonl")
            with open(filename, 'w') as f:
                for sample in self.data_samples:
                    f.write(json.dumps(sample) + '\n')
        else:  # json
            filename = os.path.join(self.output_dir, f"{self.dataset_name}_{timestamp}.json")
            with open(filename, 'w') as f:
                json.dump(self.data_samples, f, indent=2)
        
        print(f"Dataset saved to: {filename}")
        print(f"Total samples: {len(self.data_samples)}")
        
        return filename
    
    def get_statistics(self):
        """
        Get statistics about the dataset.
        
        Returns:
            dict: Dataset statistics
        """
        if not self.data_samples:
            return {"total_samples": 0}
        
        rewards = [s['metadata']['reward'] for s in self.data_samples]
        level_changes = [s['metadata']['next_level'] - s['metadata']['prev_level'] 
                         for s in self.data_samples]
        size_changes = [s['metadata']['next_size'] - s['metadata']['prev_size'] 
                        for s in self.data_samples]
        
        stats = {
            "total_samples": len(self.data_samples),
            "reward_mean": float(np.mean(rewards)),
            "reward_std": float(np.std(rewards)),
            "reward_min": float(np.min(rewards)),
            "reward_max": float(np.max(rewards)),
            "level_change_mean": float(np.mean(level_changes)),
            "size_change_mean": float(np.mean(size_changes)),
            "avg_input_bits": float(np.mean([s['metadata']['input_bit'] for s in self.data_samples]))
        }
        
        return stats


def main():
    """
    Main function for standalone dataset generation from existing traces.
    """
    parser = argparse.ArgumentParser(description='Generate training dataset from adder optimization')
    parser.add_argument('--output_dir', type=str, default='dataset',
                        help='Output directory for dataset')
    parser.add_argument('--dataset_name', type=str, default='adder_optimization',
                        help='Base name for dataset file')
    parser.add_argument('--format', type=str, default='jsonl', choices=['json', 'jsonl'],
                        help='Output format')
    
    args = parser.parse_args()
    
    generator = DatasetGenerator(
        output_dir=args.output_dir,
        dataset_name=args.dataset_name
    )
    
    print("Dataset Generator initialized.")
    print(f"To use this generator, integrate it with your adder.py training loop.")
    print(f"Example usage:")
    print(f"  from generate_dataset import DatasetGenerator")
    print(f"  generator = DatasetGenerator()")
    print(f"  generator.add_state_transition(prev_state, next_state, operation_info)")
    print(f"  generator.save_dataset()")
    
    # Save empty dataset as template
    generator.save_dataset(format=args.format)
    

if __name__ == "__main__":
    main()
