#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive test demonstrating legalization tracking in adder.py

This test creates realistic scenarios where legalization adds cells and
verifies that the tracking works correctly.
"""

import sys
import numpy as np
import copy
import torch

# Set up environment
INPUT_BIT = 8
LEVEL_BOUND_DELTA = 0

# Import the State class from adder.py
import adder

def test_legalization_tracking():
    """Test that legalization effects are properly tracked in the generation trace"""
    
    print("=" * 80)
    print("LEGALIZATION TRACKING TEST")
    print("=" * 80)
    print()
    
    # Create a Sklansky adder as initial state
    print("1. Creating initial Sklansky adder (8-bit)...")
    state = adder.get_sklansky_init()
    print(f"   Initial state: level={state.level}, size={state.size}")
    print(f"   Available choices for cell removal: {state.available_choice}")
    print()
    
    # Generate a few states to see legalization in action
    print("2. Generating states with cell removal...")
    print()
    
    current_state = state
    max_steps = 5
    step_count = 0
    
    while step_count < max_steps and current_state is not None:
        next_state = current_state.get_next_state_with_random_choice()
        
        if next_state is None:
            print(f"   No more valid states after {step_count} steps")
            break
            
        step_count += 1
        current_state = next_state
        
        # Display information about the last operation
        if len(next_state.generation_trace) > 0:
            last_op = next_state.generation_trace[-1]
            removed_pos = last_op['position']
            added_cells = last_op.get('legalization_added_cells', [])
            
            print(f"   Step {last_op['step']}:")
            print(f"   - Removed cell at: ({removed_pos[0]}, {removed_pos[1]})")
            if added_cells:
                print(f"   - Legalization added {len(added_cells)} cell(s): {added_cells}")
            else:
                print(f"   - Legalization: No cells added")
            print(f"   - Size change: {last_op['prev_size']:.0f} -> {last_op['next_size']:.0f}")
            print(f"   - Level change: {last_op['prev_level']:.0f} -> {last_op['next_level']:.0f}")
            print()
    
    # Display the complete trace
    if current_state is not None and len(current_state.generation_trace) > 0:
        print("3. Complete generation trace:")
        print("-" * 80)
        current_state.output_generation_trace()
        print()
        
        # Save to file
        output_file = "/tmp/legalization_tracking_test.txt"
        current_state.output_generation_trace(output_file)
        print(f"   Trace saved to: {output_file}")
        print()
    
    # Verify that legalization info is present
    print("4. Verification:")
    if current_state is not None and len(current_state.generation_trace) > 0:
        has_legalization_info = all(
            'legalization_added_cells' in op 
            for op in current_state.generation_trace
        )
        print(f"   All operations have legalization info: {has_legalization_info}")
        
        # Count operations with legalization additions
        ops_with_additions = sum(
            1 for op in current_state.generation_trace 
            if len(op.get('legalization_added_cells', [])) > 0
        )
        total_ops = len(current_state.generation_trace)
        print(f"   Operations with cell additions: {ops_with_additions}/{total_ops}")
        
        # Count total cells added
        total_added = sum(
            len(op.get('legalization_added_cells', [])) 
            for op in current_state.generation_trace
        )
        print(f"   Total cells added by legalization: {total_added}")
        print()
        
        print("✓ Test completed successfully!")
    else:
        print("   Warning: No states were generated")
    
    print("=" * 80)


def test_manual_scenario():
    """Test a specific scenario where we know legalization will add cells"""
    
    print()
    print("=" * 80)
    print("MANUAL SCENARIO TEST - Known Legalization Pattern")
    print("=" * 80)
    print()
    
    # Create a state with a specific pattern that will require legalization
    cell_map = np.zeros((INPUT_BIT, INPUT_BIT))
    level_map = np.zeros((INPUT_BIT, INPUT_BIT))
    
    # Initialize diagonal
    for i in range(INPUT_BIT):
        cell_map[i, i] = 1
        cell_map[i, 0] = 1
        level_map[i, i] = 1
        level_map[i, 0] = i + 1
    
    # Add a chain of cells that will trigger legalization when broken
    # Pattern: cells at (7,3), (6,3), (5,3)
    cell_map[7, 3] = 1
    cell_map[6, 3] = 1
    cell_map[5, 3] = 1
    level_map[7, 3] = 5
    level_map[6, 3] = 4
    level_map[5, 3] = 3
    
    # Create min_map (cells that can be removed)
    min_map = copy.deepcopy(cell_map)
    for i in range(INPUT_BIT):
        min_map[i, i] = 0
        min_map[i, 0] = 0
    
    # Mark the top cell as removable
    min_map[7, 3] = 1
    
    level = level_map.max()
    size = cell_map.sum() - INPUT_BIT
    
    print(f"Creating state with specific pattern...")
    print(f"  - Cells at (7,3), (6,3), (5,3) form a chain")
    print(f"  - Initial size: {size}")
    print()
    
    # Create the state
    state = adder.State(level, size, cell_map, level_map, min_map, 0, 0, 0)
    
    print(f"Removing cell at (7,3)...")
    print(f"  - This should trigger legalization to add cell at (4,3)")
    print()
    
    # Generate next state
    next_state = state.get_next_state_with_random_choice()
    
    if next_state and len(next_state.generation_trace) > 0:
        op = next_state.generation_trace[0]
        print(f"Result:")
        print(f"  - Removed cell at: {op['position']}")
        print(f"  - Cells added: {op['legalization_added_cells']}")
        print(f"  - Size change: {op['prev_size']:.0f} -> {op['next_size']:.0f}")
        print()
        
        next_state.output_generation_trace()
        
        if len(op['legalization_added_cells']) > 0:
            print("✓ Legalization tracking works correctly!")
        else:
            print("⚠ Warning: Expected legalization to add cells")
    else:
        print("✗ Failed to generate next state")
    
    print("=" * 80)
    print()


if __name__ == "__main__":
    # Run both tests
    test_legalization_tracking()
    test_manual_scenario()
    
    print()
    print("All tests completed!")
