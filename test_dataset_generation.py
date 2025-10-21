#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Integration tests for dataset generation

Run these tests to verify that dataset generation is working correctly.
"""

import os
import sys
import json
import tempfile
import shutil
import subprocess


def test_basic_generation():
    """Test basic dataset generation"""
    print("Test 1: Basic dataset generation...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run([
            'python', 'generate_dataset.py',
            '--input_bit=8',
            '--num_trajectories=2',
            '--max_steps=5',
            '--sample_strategy=random',
            '--level_bound_delta=1',
            '--output_dir=' + tmpdir,
            '--seed=42'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"  FAILED: {result.stderr}")
            return False
        
        # Check that output file exists
        files = os.listdir(tmpdir)
        if not any(f.endswith('.jsonl') for f in files):
            print("  FAILED: No output file generated")
            return False
        
        print("  PASSED")
        return True


def test_openr1_format():
    """Test OpenR1 format generation"""
    print("Test 2: OpenR1 format generation...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run([
            'python', 'generate_dataset.py',
            '--input_bit=8',
            '--num_trajectories=2',
            '--max_steps=5',
            '--sample_strategy=random',
            '--level_bound_delta=1',
            '--output_dir=' + tmpdir,
            '--openr1_format',
            '--seed=42'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"  FAILED: {result.stderr}")
            return False
        
        # Check that OpenR1 file exists
        files = os.listdir(tmpdir)
        openr1_files = [f for f in files if 'openr1' in f and f.endswith('.jsonl')]
        if not openr1_files:
            print("  FAILED: No OpenR1 file generated")
            return False
        
        # Verify OpenR1 format
        with open(os.path.join(tmpdir, openr1_files[0]), 'r') as f:
            first_line = f.readline()
            data = json.loads(first_line)
            if 'prompt' not in data or 'completion' not in data or 'reward' not in data:
                print("  FAILED: Invalid OpenR1 format")
                return False
        
        print("  PASSED")
        return True


def test_different_init_types():
    """Test different initialization types"""
    print("Test 3: Different initialization types...")
    
    init_types = ['sklansky', 'brent_kung', 'normal']
    
    for init_type in init_types:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run([
                'python', 'generate_dataset.py',
                '--input_bit=8',
                '--num_trajectories=1',
                '--max_steps=5',
                '--sample_strategy=random',
                '--level_bound_delta=2',
                '--init_type=' + init_type,
                '--output_dir=' + tmpdir,
                '--seed=42'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"  FAILED ({init_type}): {result.stderr}")
                return False
    
    print("  PASSED")
    return True


def test_different_sample_strategies():
    """Test different sampling strategies"""
    print("Test 4: Different sampling strategies...")
    
    strategies = ['random', 'best']
    
    for strategy in strategies:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run([
                'python', 'generate_dataset.py',
                '--input_bit=8',
                '--num_trajectories=1',
                '--max_steps=5',
                '--sample_strategy=' + strategy,
                '--level_bound_delta=1',
                '--output_dir=' + tmpdir,
                '--seed=42'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"  FAILED ({strategy}): {result.stderr}")
                return False
    
    print("  PASSED")
    return True


def test_dataset_format():
    """Test that generated dataset has correct format"""
    print("Test 5: Dataset format validation...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run([
            'python', 'generate_dataset.py',
            '--input_bit=8',
            '--num_trajectories=2',
            '--max_steps=5',
            '--sample_strategy=random',
            '--level_bound_delta=1',
            '--output_dir=' + tmpdir,
            '--seed=42'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"  FAILED: {result.stderr}")
            return False
        
        # Find the output file
        files = [f for f in os.listdir(tmpdir) if f.endswith('.jsonl') and 'openr1' not in f]
        if not files:
            print("  FAILED: No output file found")
            return False
        
        # Validate format
        with open(os.path.join(tmpdir, files[0]), 'r') as f:
            for line in f:
                data = json.loads(line)
                required_keys = ['trajectory_id', 'step', 'state', 'action', 'next_state', 'improvement']
                if not all(key in data for key in required_keys):
                    print(f"  FAILED: Missing required keys in data")
                    return False
                
                # Check state format
                state_keys = ['input_bit', 'level', 'size', 'level_bound', 'available_choice']
                if not all(key in data['state'] for key in state_keys):
                    print(f"  FAILED: Missing required keys in state")
                    return False
        
        print("  PASSED")
        return True


def test_example_usage_script():
    """Test that example usage script works"""
    print("Test 6: Example usage script...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate a small dataset
        subprocess.run([
            'python', 'generate_dataset.py',
            '--input_bit=8',
            '--num_trajectories=1',
            '--max_steps=3',
            '--sample_strategy=random',
            '--level_bound_delta=1',
            '--output_dir=' + tmpdir,
            '--openr1_format',
            '--seed=42'
        ], capture_output=True, text=True)
        
        # Find the OpenR1 file
        files = [f for f in os.listdir(tmpdir) if 'openr1' in f and f.endswith('.jsonl')]
        if not files:
            print("  FAILED: No dataset file generated")
            return False
        
        # Run example script
        result = subprocess.run([
            'python', 'example_dataset_usage.py',
            os.path.join(tmpdir, files[0])
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"  FAILED: {result.stderr}")
            return False
        
        print("  PASSED")
        return True


def main():
    print("="*60)
    print("Running Dataset Generation Integration Tests")
    print("="*60)
    print()
    
    # Change to repository directory
    os.chdir('/home/runner/work/ArithTreeRL/ArithTreeRL')
    
    tests = [
        test_basic_generation,
        test_openr1_format,
        test_different_init_types,
        test_different_sample_strategies,
        test_dataset_format,
        test_example_usage_script,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  FAILED with exception: {e}")
            failed += 1
        print()
    
    print("="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
