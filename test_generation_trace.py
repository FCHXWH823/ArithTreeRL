#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to demonstrate the generation trace functionality in adder.py
"""

import sys
import math
import numpy as np
import copy

# Mock the necessary components for testing without running full MCTS
INPUT_BIT = 8
LEVEL_BOUND_DELTA = 0

class SimpleState:
    """Simplified State class for testing generation trace functionality"""
    
    def __init__(self, level, size, cell_map, level_map, min_map, step_num, action, reward):
        self.input_bit = INPUT_BIT
        self.generation_trace = []
        self.level = level
        self.size = size
        self.cell_map = cell_map
        self.level_map = level_map
        self.min_map = min_map
        self.step_num = step_num
        self.action = action
        self.reward = reward
        
    def output_generation_trace(self, file_name=None):
        """
        Output the generation trace showing the operation at each step.
        
        Args:
            file_name (str, optional): Path to save the trace. If None, prints to console.
        
        Returns:
            str: Formatted trace string
        """
        if len(self.generation_trace) == 0:
            trace_str = "No operations performed - this is the initial state.\n"
            trace_str += "Initial State: level={}, size={}\n".format(self.level, self.size)
        else:
            trace_str = "Generation Trace for Adder Design:\n"
            trace_str += "=" * 80 + "\n"
            trace_str += "Input Bit Width: {}\n".format(self.input_bit)
            trace_str += "Final Level (Depth): {}\n".format(self.level)
            trace_str += "Final Size (Gate Count): {}\n".format(self.size)
            trace_str += "Total Steps: {}\n".format(len(self.generation_trace))
            trace_str += "=" * 80 + "\n\n"
            
            for op in self.generation_trace:
                trace_str += "Step {}: {} at position ({}, {})\n".format(
                    op['step'], op['action_type'], op['position'][0], op['position'][1])
                trace_str += "  Action ID: {}\n".format(op['action'])
                
                # Display legalization effects if any cells were added
                if 'legalization_added_cells' in op and len(op['legalization_added_cells']) > 0:
                    trace_str += "  Legalization: {} cell(s) added: {}\n".format(
                        len(op['legalization_added_cells']),
                        ', '.join(['({}, {})'.format(c[0], c[1]) for c in op['legalization_added_cells']])
                    )
                else:
                    trace_str += "  Legalization: No cells added\n"
                
                trace_str += "  Level: {} -> {} (change: {:+d})\n".format(
                    op['prev_level'], op['next_level'], 
                    int(op['next_level'] - op['prev_level']))
                trace_str += "  Size:  {} -> {} (change: {:+d})\n".format(
                    op['prev_size'], op['next_size'],
                    int(op['next_size'] - op['prev_size']))
                trace_str += "  Reward: {:.2f}\n".format(op['reward'])
                trace_str += "-" * 80 + "\n"
        
        if file_name is not None:
            with open(file_name, 'w') as f:
                f.write(trace_str)
            print("Generation trace saved to: {}".format(file_name))
        else:
            print(trace_str)
        
        return trace_str


def test_generation_trace():
    """Test the generation trace functionality"""
    print("Testing Generation Trace Functionality")
    print("=" * 80)
    
    # Create initial state
    cell_map = np.zeros((INPUT_BIT, INPUT_BIT))
    level_map = np.zeros((INPUT_BIT, INPUT_BIT))
    min_map = np.zeros((INPUT_BIT, INPUT_BIT))
    
    # Initialize with diagonal (simple initial configuration)
    for i in range(INPUT_BIT):
        cell_map[i, i] = 1
        level_map[i, i] = 1
    
    initial_state = SimpleState(
        level=1,
        size=0,
        cell_map=cell_map,
        level_map=level_map,
        min_map=min_map,
        step_num=0,
        action=0,
        reward=0
    )
    
    print("\n1. Testing initial state (no operations):")
    print("-" * 80)
    initial_state.output_generation_trace()
    
    # Simulate a few operations
    print("\n2. Testing state after simulated operations:")
    print("-" * 80)
    
    state_with_trace = SimpleState(
        level=4,
        size=10,
        cell_map=cell_map,
        level_map=level_map,
        min_map=min_map,
        step_num=3,
        action=150,
        reward=-2.5
    )
    
    # Manually add some trace entries to simulate operations
    state_with_trace.generation_trace = [
        {
            'step': 1,
            'action': 100,
            'action_type': 'remove_cell',
            'position': (3, 1),
            'prev_level': 4,
            'next_level': 4,
            'prev_size': 12,
            'next_size': 11,
            'reward': -1.0,
            'legalization_added_cells': []  # No cells added
        },
        {
            'step': 2,
            'action': 125,
            'action_type': 'remove_cell',
            'position': (5, 2),
            'prev_level': 4,
            'next_level': 4,
            'prev_size': 11,
            'next_size': 10,
            'reward': -1.0,
            'legalization_added_cells': [(3, 2)]  # One cell added during legalization
        },
        {
            'step': 3,
            'action': 150,
            'action_type': 'remove_cell',
            'position': (7, 3),
            'prev_level': 4,
            'next_level': 4,
            'prev_size': 10,
            'next_size': 10,
            'reward': -2.5,
            'legalization_added_cells': [(4, 3), (5, 3)]  # Two cells added during legalization
        }
    ]
    
    state_with_trace.output_generation_trace()
    
    # Test saving to file
    print("\n3. Testing save to file:")
    print("-" * 80)
    output_file = "/tmp/test_generation_trace.txt"
    state_with_trace.output_generation_trace(file_name=output_file)
    
    print("\nTest completed successfully!")


if __name__ == "__main__":
    test_generation_trace()
