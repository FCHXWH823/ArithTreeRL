#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_dataset_generation.py - Test Dataset Generation Functionality

This script tests the dataset generation components to ensure they work correctly.
"""

import os
import sys
import json
import tempfile
import shutil
import numpy as np

from generate_dataset import DatasetGenerator


def create_mock_state(input_bit, level, size, step_num=0):
    """Create a mock state for testing."""
    class MockState:
        def __init__(self, input_bit, level, size, step_num):
            self.input_bit = input_bit
            self.level = level
            self.size = size
            self.step_num = step_num
            self.level_bound = int(np.log2(input_bit)) + 1
            self.available_choice = 5
            self.cell_map = np.eye(input_bit)
            self.level_map = np.eye(input_bit)
            self.min_map = np.zeros((input_bit, input_bit))
            self.generation_trace = []
            self.action = 0
            self.reward = -1.0
    
    return MockState(input_bit, level, size, step_num)


def test_dataset_generator_creation():
    """Test creating a DatasetGenerator instance."""
    print("\n" + "=" * 80)
    print("TEST 1: DatasetGenerator Creation")
    print("=" * 80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = DatasetGenerator(
            output_dir=tmpdir,
            dataset_name="test_dataset"
        )
        
        assert generator.output_dir == tmpdir
        assert generator.dataset_name == "test_dataset"
        assert len(generator.data_samples) == 0
        assert os.path.exists(tmpdir)
        
        print("✓ DatasetGenerator created successfully")
        print(f"  Output dir: {tmpdir}")
        print(f"  Dataset name: test_dataset")
        print(f"  Initial samples: 0")


def test_state_to_text():
    """Test converting state to text representation."""
    print("\n" + "=" * 80)
    print("TEST 2: State to Text Conversion")
    print("=" * 80)
    
    generator = DatasetGenerator()
    mock_state = create_mock_state(input_bit=8, level=4, size=12)
    
    # Test without maps
    text = generator.state_to_text(mock_state, include_maps=False)
    assert "Input Bits: 8" in text
    assert "Current Level (Depth): 4" in text
    assert "Current Size (Gates): 12" in text
    print("✓ State to text (without maps) conversion works")
    print(f"  Output length: {len(text)} characters")
    
    # Test with maps
    text_with_maps = generator.state_to_text(mock_state, include_maps=True)
    assert "Cell Map" in text_with_maps
    assert len(text_with_maps) > len(text)
    print("✓ State to text (with maps) conversion works")
    print(f"  Output length: {len(text_with_maps)} characters")


def test_action_to_text():
    """Test converting action to text representation."""
    print("\n" + "=" * 80)
    print("TEST 3: Action to Text Conversion")
    print("=" * 80)
    
    generator = DatasetGenerator()
    operation_info = {
        'step': 1,
        'action': 150,
        'action_type': 'remove_cell',
        'position': (5, 2),
        'prev_level': 4,
        'next_level': 4,
        'prev_size': 12,
        'next_size': 11,
        'reward': -1.0,
        'legalization_added_cells': [(3, 2)]
    }
    
    text = generator.action_to_text(operation_info)
    assert "Action Type: remove_cell" in text
    assert "Position: (5, 2)" in text
    assert "Action ID: 150" in text
    assert "Legalization Added Cells: 1" in text
    assert "Reward: -1.0000" in text
    
    print("✓ Action to text conversion works")
    print(f"  Output length: {len(text)} characters")
    print(f"  First 200 chars:\n{text[:200]}...")


def test_create_training_sample():
    """Test creating a training sample."""
    print("\n" + "=" * 80)
    print("TEST 4: Training Sample Creation")
    print("=" * 80)
    
    generator = DatasetGenerator()
    prev_state = create_mock_state(input_bit=8, level=4, size=12, step_num=0)
    next_state = create_mock_state(input_bit=8, level=4, size=11, step_num=1)
    
    operation_info = {
        'step': 1,
        'action': 150,
        'action_type': 'remove_cell',
        'position': (5, 2),
        'prev_level': 4,
        'next_level': 4,
        'prev_size': 12,
        'next_size': 11,
        'reward': -1.0,
        'legalization_added_cells': []
    }
    
    sample = generator.create_training_sample(prev_state, next_state, operation_info)
    
    assert sample['id'] == 'sample_0'
    assert 'input' in sample
    assert 'output' in sample
    assert 'metadata' in sample
    assert sample['metadata']['input_bit'] == 8
    assert sample['metadata']['prev_level'] == 4
    assert sample['metadata']['next_level'] == 4
    assert sample['metadata']['prev_size'] == 12
    assert sample['metadata']['next_size'] == 11
    
    print("✓ Training sample created successfully")
    print(f"  Sample ID: {sample['id']}")
    print(f"  Metadata keys: {list(sample['metadata'].keys())}")
    print(f"  Input length: {len(sample['input'])} chars")
    print(f"  Output length: {len(sample['output'])} chars")


def test_add_state_transition():
    """Test adding state transitions."""
    print("\n" + "=" * 80)
    print("TEST 5: Adding State Transitions")
    print("=" * 80)
    
    generator = DatasetGenerator()
    
    # Add multiple transitions
    for i in range(5):
        prev_state = create_mock_state(input_bit=8, level=4, size=12-i, step_num=i)
        next_state = create_mock_state(input_bit=8, level=4, size=11-i, step_num=i+1)
        
        operation_info = {
            'step': i+1,
            'action': 150+i,
            'action_type': 'remove_cell',
            'position': (5, 2+i),
            'prev_level': 4,
            'next_level': 4,
            'prev_size': 12-i,
            'next_size': 11-i,
            'reward': -1.0,
            'legalization_added_cells': []
        }
        
        generator.add_state_transition(prev_state, next_state, operation_info)
    
    assert len(generator.data_samples) == 5
    print(f"✓ Added {len(generator.data_samples)} state transitions")
    
    # Verify IDs are sequential
    for i, sample in enumerate(generator.data_samples):
        assert sample['id'] == f'sample_{i}'
    print("✓ Sample IDs are correctly assigned")


def test_save_dataset():
    """Test saving dataset to file."""
    print("\n" + "=" * 80)
    print("TEST 6: Saving Dataset")
    print("=" * 80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = DatasetGenerator(
            output_dir=tmpdir,
            dataset_name="test_save"
        )
        
        # Add some samples
        for i in range(3):
            prev_state = create_mock_state(input_bit=8, level=4, size=12-i, step_num=i)
            next_state = create_mock_state(input_bit=8, level=4, size=11-i, step_num=i+1)
            
            operation_info = {
                'step': i+1,
                'action': 150+i,
                'action_type': 'remove_cell',
                'position': (5, 2),
                'prev_level': 4,
                'next_level': 4,
                'prev_size': 12-i,
                'next_size': 11-i,
                'reward': -1.0,
                'legalization_added_cells': []
            }
            
            generator.add_state_transition(prev_state, next_state, operation_info)
        
        # Test JSONL format
        jsonl_file = generator.save_dataset(format='jsonl')
        assert os.path.exists(jsonl_file)
        assert jsonl_file.endswith('.jsonl')
        
        # Verify JSONL content
        with open(jsonl_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 3
            for line in lines:
                sample = json.loads(line)
                assert 'id' in sample
                assert 'input' in sample
                assert 'output' in sample
        
        print(f"✓ JSONL dataset saved successfully: {jsonl_file}")
        print(f"  Lines in file: {len(lines)}")
        
        # Test JSON format
        generator2 = DatasetGenerator(
            output_dir=tmpdir,
            dataset_name="test_save_json"
        )
        for i in range(2):
            prev_state = create_mock_state(input_bit=8, level=4, size=12-i, step_num=i)
            next_state = create_mock_state(input_bit=8, level=4, size=11-i, step_num=i+1)
            operation_info = {
                'step': i+1,
                'action': 150+i,
                'action_type': 'remove_cell',
                'position': (5, 2),
                'prev_level': 4,
                'next_level': 4,
                'prev_size': 12-i,
                'next_size': 11-i,
                'reward': -1.0,
                'legalization_added_cells': []
            }
            generator2.add_state_transition(prev_state, next_state, operation_info)
        
        json_file = generator2.save_dataset(format='json')
        assert os.path.exists(json_file)
        assert json_file.endswith('.json')
        
        # Verify JSON content
        with open(json_file, 'r') as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == 2
        
        print(f"✓ JSON dataset saved successfully: {json_file}")
        print(f"  Samples in file: {len(data)}")


def test_get_statistics():
    """Test getting dataset statistics."""
    print("\n" + "=" * 80)
    print("TEST 7: Dataset Statistics")
    print("=" * 80)
    
    generator = DatasetGenerator()
    
    # Test empty dataset
    stats = generator.get_statistics()
    assert stats['total_samples'] == 0
    print("✓ Empty dataset statistics work")
    
    # Add samples with varying rewards
    rewards = [-1.0, -2.0, -1.5, -0.5, -3.0]
    for i, reward in enumerate(rewards):
        prev_state = create_mock_state(input_bit=8, level=4, size=12-i, step_num=i)
        next_state = create_mock_state(input_bit=8, level=4, size=11-i, step_num=i+1)
        
        operation_info = {
            'step': i+1,
            'action': 150+i,
            'action_type': 'remove_cell',
            'position': (5, 2),
            'prev_level': 4,
            'next_level': 4,
            'prev_size': 12-i,
            'next_size': 11-i,
            'reward': reward,
            'legalization_added_cells': []
        }
        
        generator.add_state_transition(prev_state, next_state, operation_info)
    
    stats = generator.get_statistics()
    assert stats['total_samples'] == 5
    assert abs(stats['reward_mean'] - np.mean(rewards)) < 1e-6
    assert abs(stats['reward_std'] - np.std(rewards)) < 1e-6
    assert stats['reward_min'] == min(rewards)
    assert stats['reward_max'] == max(rewards)
    
    print("✓ Dataset statistics computed correctly")
    print(f"  Total samples: {stats['total_samples']}")
    print(f"  Reward mean: {stats['reward_mean']:.4f}")
    print(f"  Reward std: {stats['reward_std']:.4f}")
    print(f"  Reward range: [{stats['reward_min']:.2f}, {stats['reward_max']:.2f}]")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("DATASET GENERATION TEST SUITE")
    print("=" * 80)
    
    tests = [
        test_dataset_generator_creation,
        test_state_to_text,
        test_action_to_text,
        test_create_training_sample,
        test_add_state_transition,
        test_save_dataset,
        test_get_statistics
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n✗ Test failed: {test.__name__}")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n✓ All tests passed!")
    else:
        print(f"\n✗ {failed} test(s) failed")
    
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
