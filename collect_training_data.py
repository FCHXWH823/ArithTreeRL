#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
collect_training_data.py - Collect Training Data from Adder Optimization

This script extends adder.py to collect training data during the MCTS search.
It captures state transitions that can be used for LLM finetuning/GRPO training
compatible with OpenR1 framework.

Usage:
    python collect_training_data.py --input_bit=8 --seed=1 --max_steps=100
"""

import sys
import os
import argparse
import numpy as np
import copy
import math
import random
import torch
import time

# Parse arguments first before importing adder
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Collect training data from adder optimization'
    )
    parser.add_argument('--input_bit', type=int, default=8,
                        help='Number of input bits')
    parser.add_argument('--level_bound_delta', type=int, default=0,
                        help='Level bound delta')
    parser.add_argument('--seed', type=int, default=1,
                        help='Random seed')
    parser.add_argument('--max_steps', type=int, default=200,
                        help='Maximum MCTS steps')
    parser.add_argument('--output_dir', type=str, default='dataset',
                        help='Output directory for dataset')
    
    cli_args = parser.parse_args()
    
    # Set up args for adder module before importing it
    sys.argv = ['adder.py', 
                '--input_bit', str(cli_args.input_bit),
                '--level_bound_delta', str(cli_args.level_bound_delta),
                '--seed', str(cli_args.seed)]

# Import components from adder and dataset generator
from generate_dataset import DatasetGenerator
import adder


class DatasetCollector:
    """
    Collector class that integrates with adder.py to capture training data.
    """
    
    def __init__(self, output_dir="dataset", dataset_name="adder_training"):
        self.generator = DatasetGenerator(output_dir, dataset_name)
        self.state_history = []  # Track states for transition construction
        
    def collect_transition(self, current_state, next_state):
        """
        Collect a state transition for the dataset.
        
        Args:
            current_state: State before action
            next_state: State after action
        """
        if next_state is None or not hasattr(next_state, 'generation_trace'):
            return
        
        if len(next_state.generation_trace) > 0:
            operation_info = next_state.generation_trace[-1]
            try:
                self.generator.add_state_transition(current_state, next_state, operation_info)
            except Exception as e:
                print(f"Warning: Failed to collect transition: {e}")
    
    def save(self, format='jsonl'):
        """Save the collected dataset."""
        return self.generator.save_dataset(format=format)
    
    def get_stats(self):
        """Get dataset statistics."""
        return self.generator.get_statistics()


def monte_carlo_tree_search_with_collection(node, computation_budget, collector=None):
    """
    Modified MCTS that collects training data.
    This is based on the monte_carlo_tree_search function from adder.py
    """
    for i in range(computation_budget):
        if i % 100 == 0:
            print(f"MCTS iteration {i}/{computation_budget}")
        
        # Tree policy - select node to explore
        current_node = node
        while current_node.get_state().is_terminal() == False:
            if current_node.is_all_expand() or (np.random.random() > 0.8 and len(current_node.get_children()) >= 1):
                current_node = adder.best_child(current_node, True)
            else:
                # Expand - this creates new states
                current_node = adder.expand(current_node)
                break
        
        # Default policy - rollout
        current_state = current_node.get_state()
        
        # Collect the current state
        if collector is not None:
            collector.state_history.append(copy.deepcopy(current_state))
        
        # Rollout
        rollout_state = current_state
        while rollout_state.is_terminal() == False:
            next_rollout_state = rollout_state.get_next_state_with_random_choice()
            if next_rollout_state is None:
                break
            
            # Collect transition during rollout
            if collector is not None:
                collector.collect_transition(rollout_state, next_rollout_state)
            
            rollout_state = next_rollout_state
        
        reward = current_state.compute_reward()
        
        # Backup
        current_node = adder.backup(current_node, reward)
    
    return node


def run_with_data_collection(input_bit, level_bound_delta, seed, max_steps, output_dir):
    """
    Run adder optimization with data collection.
    
    Args:
        input_bit (int): Number of input bits
        level_bound_delta (int): Level bound delta
        seed (int): Random seed
        max_steps (int): Maximum MCTS steps
        output_dir (str): Output directory for dataset
    """
    # Setup
    adder.INPUT_BIT = input_bit
    adder.LEVEL_BOUND_DELTA = level_bound_delta
    adder.random_seed = seed
    np.random.seed(seed)
    random.seed(seed)
    
    # Create dataset collector
    collector = DatasetCollector(
        output_dir=output_dir,
        dataset_name=f"adder_training_{input_bit}b_seed{seed}"
    )
    
    print("=" * 80)
    print(f"Running Adder Optimization with Data Collection")
    print(f"Input Bits: {input_bit}")
    print(f"Level Bound Delta: {level_bound_delta}")
    print(f"Seed: {seed}")
    print(f"Max Steps: {max_steps}")
    print("=" * 80)
    
    # Get initial state
    init_state = adder.get_sklansky_init()
    init_node = adder.Node()
    init_node.set_state(init_state)
    
    # Run MCTS with collection
    print("\nStarting MCTS search with data collection...")
    try:
        final_node = monte_carlo_tree_search_with_collection(
            init_node, 
            max_steps, 
            collector=collector
        )
        print(f"\nSearch completed!")
    except Exception as e:
        print(f"Error during search: {e}")
        import traceback
        traceback.print_exc()
    
    # Save dataset
    print("\n" + "=" * 80)
    print("Saving collected dataset...")
    filename = collector.save(format='jsonl')
    
    # Print statistics
    stats = collector.get_stats()
    print("\nDataset Statistics:")
    print("-" * 80)
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print("=" * 80)
    
    return filename


def main():
    """Main function - called when running as script."""
    # cli_args was already parsed above
    run_with_data_collection(
        input_bit=cli_args.input_bit,
        level_bound_delta=cli_args.level_bound_delta,
        seed=cli_args.seed,
        max_steps=cli_args.max_steps,
        output_dir=cli_args.output_dir
    )


if __name__ == "__main__":
    main()
