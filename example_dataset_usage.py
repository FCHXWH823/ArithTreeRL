#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example script demonstrating how to use the generated dataset
for LLM finetuning or GRPO training.

This is a minimal example showing the data format and structure.
Adapt this to your specific training framework (OpenR1, HuggingFace, etc.)
"""

import json
import argparse
from typing import List, Dict, Any


def load_dataset(filepath: str) -> List[Dict[str, Any]]:
    """Load dataset from JSONL file"""
    dataset = []
    with open(filepath, 'r') as f:
        for line in f:
            dataset.append(json.loads(line))
    return dataset


def print_dataset_info(dataset: List[Dict[str, Any]]):
    """Print information about the dataset"""
    print(f"Dataset size: {len(dataset)} samples")
    
    if not dataset:
        print("Empty dataset!")
        return
    
    # Check if it's OpenR1 format or raw format
    is_openr1 = 'prompt' in dataset[0]
    
    if is_openr1:
        print("Format: OpenR1 (prompt-completion)")
        print(f"\nFirst sample:")
        sample = dataset[0]
        print(f"  Prompt length: {len(sample['prompt'])} chars")
        print(f"  Completion: {sample['completion']}")
        print(f"  Reward: {sample['reward']}")
        if 'metadata' in sample:
            print(f"  Metadata: {sample['metadata']}")
    else:
        print("Format: Raw (state-action-next_state)")
        print(f"\nFirst sample:")
        sample = dataset[0]
        print(f"  Trajectory ID: {sample['trajectory_id']}")
        print(f"  Step: {sample['step']}")
        print(f"  State: {sample['state']['level']}L {sample['state']['size']}S")
        print(f"  Action: {sample['action']['description']}")
        print(f"  Improvement: {sample['improvement']}")
    
    # Compute statistics
    if is_openr1:
        avg_reward = sum(s['reward'] for s in dataset) / len(dataset)
        print(f"\nAverage reward: {avg_reward:.4f}")
    else:
        avg_reward = sum(s['improvement']['reward'] for s in dataset) / len(dataset)
        avg_size_change = sum(s['improvement']['size_change'] for s in dataset) / len(dataset)
        avg_level_change = sum(s['improvement']['level_change'] for s in dataset) / len(dataset)
        print(f"\nStatistics:")
        print(f"  Average reward: {avg_reward:.4f}")
        print(f"  Average size change: {avg_size_change:.2f}")
        print(f"  Average level change: {avg_level_change:.2f}")


def example_training_loop(dataset: List[Dict[str, Any]], is_openr1: bool = True):
    """
    Example pseudo-code for training loop
    (Replace with your actual training framework)
    """
    print("\n" + "="*60)
    print("Example Training Loop (Pseudo-code)")
    print("="*60)
    
    if is_openr1:
        print("""
# OpenR1 / GRPO Training Example
from your_training_framework import GRPOTrainer, LLMModel

# 1. Load your model
model = LLMModel.from_pretrained("your-base-model")

# 2. Create trainer with reward-based optimization
trainer = GRPOTrainer(
    model=model,
    dataset=dataset,
    reward_key="reward",
    learning_rate=1e-5,
    batch_size=8,
    # ... other hyperparameters
)

# 3. Train with reinforcement learning
trainer.train(
    num_epochs=3,
    save_steps=100,
    evaluation_steps=50
)

# 4. Save the fine-tuned model
trainer.save_model("fine-tuned-adder-optimizer")
""")
    else:
        print("""
# Supervised Fine-Tuning Example
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer

# 1. Load your model and tokenizer
model = AutoModelForCausalLM.from_pretrained("your-base-model")
tokenizer = AutoTokenizer.from_pretrained("your-base-model")

# 2. Convert raw dataset to training format
def prepare_sample(sample):
    prompt = sample['state_text']
    completion = sample['action']['description']
    input_text = prompt + "\\n\\nOptimization Action: " + completion
    return tokenizer(input_text, truncation=True, max_length=512)

train_dataset = [prepare_sample(s) for s in dataset]

# 3. Create trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    # ... other parameters
)

# 4. Train
trainer.train()
""")


def show_sample_prompt_completion(dataset: List[Dict[str, Any]], num_samples: int = 3):
    """Show a few sample prompt-completion pairs"""
    print("\n" + "="*60)
    print(f"Sample Prompt-Completion Pairs")
    print("="*60)
    
    is_openr1 = 'prompt' in dataset[0]
    
    for i, sample in enumerate(dataset[:num_samples]):
        print(f"\n--- Sample {i+1} ---")
        
        if is_openr1:
            print(f"PROMPT:\n{sample['prompt'][:300]}...")
            print(f"\nCOMPLETION: {sample['completion']}")
            print(f"REWARD: {sample['reward']}")
        else:
            print(f"STATE TEXT:\n{sample['state_text'][:300]}...")
            print(f"\nACTION: {sample['action']['description']}")
            print(f"IMPROVEMENT: {sample['improvement']}")


def main():
    parser = argparse.ArgumentParser(
        description='Example script for using generated datasets'
    )
    parser.add_argument('dataset_file', type=str,
                        help='Path to dataset file (.jsonl)')
    parser.add_argument('--show_samples', type=int, default=3,
                        help='Number of samples to display')
    parser.add_argument('--show_training_example', action='store_true',
                        help='Show example training code')
    
    args = parser.parse_args()
    
    # Load dataset
    print(f"Loading dataset from: {args.dataset_file}")
    dataset = load_dataset(args.dataset_file)
    
    # Print dataset info
    print_dataset_info(dataset)
    
    # Show sample pairs
    if dataset:
        show_sample_prompt_completion(dataset, args.show_samples)
    
    # Show training example
    if args.show_training_example:
        is_openr1 = 'prompt' in dataset[0] if dataset else True
        example_training_loop(dataset, is_openr1)


if __name__ == "__main__":
    main()
