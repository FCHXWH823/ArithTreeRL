#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
adder_with_dataset.py - Adder Design with Dataset Generation

This script provides dataset generation functionality for LLM finetuning/GRPO training.
It can be run in two modes:
1. Collect data during a new adder optimization run
2. Extract data from existing saved states and traces
"""

import sys
import os
import argparse
import numpy as np
import json

# Import the dataset generator
from generate_dataset import DatasetGenerator


def collect_from_saved_states(input_bit, cell_map_dir="cell_map", output_dir="dataset"):
    """
    Collect training data from already saved adder states.
    
    Args:
        input_bit (int): Bit width of adders to collect
        cell_map_dir (str): Directory containing saved cell maps
        output_dir (str): Output directory for dataset
    """
    generator = DatasetGenerator(
        output_dir=output_dir,
        dataset_name=f"adder_optimization_{input_bit}b_from_saved"
    )
    
    # Look for saved cell maps
    saved_dir = os.path.join(cell_map_dir, f"adder_{input_bit}b")
    if not os.path.exists(saved_dir):
        print(f"No saved states found at {saved_dir}")
        return None
    
    files = os.listdir(saved_dir)
    print(f"Found {len(files)} saved cell maps in {saved_dir}")
    
    # Parse each file to extract level and size information
    for filename in sorted(files):
        if not filename.endswith('.log'):
            continue
        
        # Parse filename: adder_8b_4l_12s_0.log
        parts = filename.replace('.log', '').split('_')
        try:
            level = int(parts[2].replace('l', ''))
            size = int(parts[3].replace('s', ''))
            
            # Create a simplified sample showing the design
            sample = {
                "id": f"saved_state_{filename}",
                "input": f"# Adder Design State\nInput Bits: {input_bit}\nCurrent Level: {level}\nCurrent Size: {size}\n",
                "output": f"# Optimized Design\nFile: {filename}\nLevel: {level}\nSize: {size}\n",
                "metadata": {
                    "input_bit": input_bit,
                    "level": level,
                    "size": size,
                    "source": "saved_state",
                    "filename": filename
                }
            }
            generator.data_samples.append(sample)
        except (ValueError, IndexError) as e:
            print(f"Warning: Could not parse filename {filename}: {e}")
            continue
    
    if len(generator.data_samples) > 0:
        filename = generator.save_dataset(format='jsonl')
        stats = generator.get_statistics()
        print("\nDataset Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        return filename
    
    return None


def main():
    """
    Main function for dataset generation.
    """
    parser = argparse.ArgumentParser(
        description='Generate training dataset for LLM finetuning/GRPO from adder optimization'
    )
    parser.add_argument('--mode', type=str, default='from_saved', 
                        choices=['from_saved', 'integrated'],
                        help='Dataset generation mode')
    parser.add_argument('--input_bit', type=int, default=8,
                        help='Bit width of adders')
    parser.add_argument('--cell_map_dir', type=str, default='cell_map',
                        help='Directory containing saved cell maps')
    parser.add_argument('--output_dir', type=str, default='dataset',
                        help='Output directory for dataset')
    parser.add_argument('--dataset_format', type=str, default='jsonl',
                        choices=['json', 'jsonl'],
                        help='Output format')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("Adder Optimization Dataset Generator")
    print("=" * 80)
    print(f"Mode: {args.mode}")
    print(f"Input Bits: {args.input_bit}")
    print(f"Output Directory: {args.output_dir}")
    print("=" * 80)
    
    if args.mode == 'from_saved':
        print("\nCollecting data from saved states...")
        result = collect_from_saved_states(
            input_bit=args.input_bit,
            cell_map_dir=args.cell_map_dir,
            output_dir=args.output_dir
        )
        if result:
            print(f"\n✓ Dataset generated successfully: {result}")
        else:
            print("\n✗ No data collected")
    
    elif args.mode == 'integrated':
        print("\nIntegrated mode: Use the DatasetCollector class from generate_dataset.py")
        print("during your adder.py run to collect real-time training data.")
        print("\nExample:")
        print("  from generate_dataset import DatasetGenerator")
        print("  generator = DatasetGenerator()")
        print("  # During MCTS search:")
        print("  generator.add_state_transition(prev_state, next_state, operation_info)")
        print("  # After search:")
        print("  generator.save_dataset()")


if __name__ == "__main__":
    main()
