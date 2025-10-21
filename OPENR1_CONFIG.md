# OpenR1 Configuration for Adder Optimization Training

This document provides example configurations for using the generated datasets
with the OpenR1 framework for LLM finetuning and GRPO training.

## Dataset Format

The generated datasets are in JSONL format, where each line contains:
- `id`: Unique identifier for the sample
- `input`: Text description of the current adder state
- `output`: Text description of the optimization action to take
- `metadata`: Additional information (rewards, level/size changes, etc.)

## Finetuning Configuration

### Example OpenR1 Finetuning Config (`openr1_finetune_config.yaml`)

```yaml
# Model configuration
model:
  name: "gpt2"  # or any compatible LLM
  checkpoint: null  # Path to pretrained checkpoint if available
  
# Training configuration
training:
  dataset_path: "dataset/adder_training_16b_seed1_*.jsonl"
  output_dir: "finetuned_models/adder_optimizer"
  num_epochs: 3
  batch_size: 8
  learning_rate: 2e-5
  warmup_steps: 100
  gradient_accumulation_steps: 4
  max_length: 1024
  
  # Evaluation
  eval_steps: 100
  save_steps: 500
  logging_steps: 10
  
  # Optimization
  optimizer: "adamw"
  weight_decay: 0.01
  max_grad_norm: 1.0

# Data processing
data:
  train_split: 0.9
  validation_split: 0.1
  shuffle: true
  seed: 42
```

### Usage

```python
from openr1 import FineTuner

# Load configuration
finetuner = FineTuner.from_config("openr1_finetune_config.yaml")

# Train
finetuner.train()

# Evaluate
results = finetuner.evaluate()
print(results)
```

## GRPO Training Configuration

### Example OpenR1 GRPO Config (`openr1_grpo_config.yaml`)

```yaml
# Model configuration
model:
  name: "gpt2"
  checkpoint: "finetuned_models/adder_optimizer/best"  # Use finetuned model
  
# GRPO training configuration
grpo:
  dataset_path: "dataset/adder_training_16b_seed1_*.jsonl"
  output_dir: "grpo_models/adder_optimizer"
  
  # GRPO specific parameters
  num_iterations: 100
  batch_size: 16
  learning_rate: 1e-5
  kl_coef: 0.1  # KL divergence coefficient
  clip_range: 0.2
  value_loss_coef: 0.5
  entropy_coef: 0.01
  
  # Reward model
  reward_model:
    type: "metadata_based"  # Use reward from metadata
    reward_key: "reward"
    normalize: true
    
  # Generation parameters
  generation:
    max_length: 512
    temperature: 0.8
    top_p: 0.9
    num_return_sequences: 4
    
  # Evaluation
  eval_steps: 50
  save_steps: 100
  logging_steps: 5

# Data processing
data:
  train_split: 0.9
  validation_split: 0.1
  shuffle: true
  seed: 42
```

### Usage

```python
from openr1 import GRPOTrainer

# Load configuration
trainer = GRPOTrainer.from_config("openr1_grpo_config.yaml")

# Train with GRPO
trainer.train()

# Evaluate
results = trainer.evaluate()
print(results)
```

## Custom Reward Function

For more advanced GRPO training, you can define a custom reward function:

```python
from openr1 import GRPOTrainer

def custom_reward_fn(sample, generated_output):
    """
    Custom reward function that evaluates optimization quality.
    
    Args:
        sample: Input sample with metadata
        generated_output: Generated optimization action
        
    Returns:
        float: Reward score
    """
    # Parse the generated output to extract predicted changes
    # Compare with actual optimal action from metadata
    
    prev_size = sample['metadata']['prev_size']
    next_size = sample['metadata']['next_size']
    
    # Reward for size reduction
    size_reduction_reward = (prev_size - next_size) * 1.0
    
    # Penalty for level increase
    level_change = sample['metadata']['next_level'] - sample['metadata']['prev_level']
    level_penalty = level_change * 10.0
    
    # Combined reward
    reward = size_reduction_reward - level_penalty
    
    return reward

# Initialize trainer with custom reward
trainer = GRPOTrainer.from_config("openr1_grpo_config.yaml")
trainer.set_reward_function(custom_reward_fn)
trainer.train()
```

## Multi-Configuration Training

To train on datasets with different bit widths:

```python
from openr1 import FineTuner
import glob

# Collect all dataset files
dataset_files = glob.glob("dataset/adder_training_*b_*.jsonl")

# Train on combined data
config = {
    "model": {"name": "gpt2"},
    "training": {
        "dataset_path": dataset_files,
        "output_dir": "finetuned_models/adder_optimizer_multi",
        "num_epochs": 5,
        "batch_size": 16,
    }
}

finetuner = FineTuner.from_dict(config)
finetuner.train()
```

## Inference Example

After training, use the model for inference:

```python
from openr1 import load_model

# Load trained model
model = load_model("grpo_models/adder_optimizer/best")

# Prepare input state
input_state = """
# Adder Design State
Input Bits: 16
Current Level (Depth): 6
Current Size (Gates): 30
Level Bound: 6
Available Actions: 10

## Cell Map (16x16):
1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0
...
"""

# Generate optimization action
output = model.generate(
    input_state,
    max_length=256,
    temperature=0.7,
    top_p=0.9
)

print("Suggested optimization:")
print(output)
```

## Evaluation Metrics

Track these metrics during training:

1. **Loss**: Standard language modeling loss
2. **Reward**: Average reward from GRPO training
3. **Accuracy**: Percentage of correct action predictions
4. **Size Reduction**: Average size reduction achieved
5. **Level Preservation**: Percentage of actions that don't increase level

```python
# Custom evaluation
from openr1 import evaluate_model

metrics = evaluate_model(
    model_path="grpo_models/adder_optimizer/best",
    dataset_path="dataset/validation_set.jsonl",
    metrics=["loss", "reward", "accuracy", "size_reduction", "level_preservation"]
)

print("Evaluation Results:")
for metric, value in metrics.items():
    print(f"  {metric}: {value:.4f}")
```

## Tips for Training

1. **Start with finetuning**: First finetune on the dataset before GRPO
2. **Use multiple seeds**: Generate datasets with different random seeds
3. **Vary bit widths**: Include 8b, 16b, 32b datasets for generalization
4. **Monitor overfitting**: Use validation set to track generalization
5. **Adjust KL coefficient**: Start with 0.1 and adjust based on performance
6. **Curriculum learning**: Start with smaller problems (8b) then larger (32b)

## Troubleshooting

### Issue: Model generates invalid actions
**Solution**: Increase finetuning epochs or adjust temperature during generation

### Issue: GRPO training is unstable
**Solution**: Reduce learning rate or increase KL coefficient

### Issue: Poor generalization to different bit widths
**Solution**: Include more diverse training data with various bit widths

## Additional Resources

- [OpenR1 Documentation](https://github.com/openr1/openr1)
- [GRPO Paper](https://arxiv.org/abs/2402.xxxxx)
- [Dataset Generation Guide](DATASET_GENERATION.md)
