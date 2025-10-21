# Dataset Generation for LLM Finetuning and GRPO Training

This guide explains how to generate training datasets from the adder optimization process for LLM finetuning or Guided Reward Proximal Optimization (GRPO) training, compatible with the OpenR1 framework.

## Overview

The dataset generation captures state transitions during the MCTS-based adder optimization process. Each training sample consists of:

1. **Input**: Current state of the adder design (cell map, level, size, etc.)
2. **Output**: Optimization action to take (cell removal, position, expected changes)
3. **Metadata**: Additional information (rewards, level/size changes, etc.)

This data enables training an LLM to propose optimization actions for arithmetic circuit designs.

## Components

### 1. `generate_dataset.py`
Core module for dataset generation with the `DatasetGenerator` class.

**Key Features:**
- Convert states to text representation
- Convert actions to text representation  
- Create training samples in OpenR1 compatible format
- Support JSON and JSONL output formats
- Compute dataset statistics

### 2. `collect_training_data.py`
Script to collect training data during a new adder optimization run.

**Usage:**
```bash
python collect_training_data.py --input_bit=8 --seed=1 --max_steps=200
```

**Arguments:**
- `--input_bit`: Number of input bits (default: 8)
- `--level_bound_delta`: Level bound delta (default: 0)
- `--seed`: Random seed (default: 1)
- `--max_steps`: Maximum MCTS steps for data collection (default: 200)
- `--output_dir`: Output directory for dataset (default: 'dataset')

### 3. `adder_with_dataset.py`
Script to generate datasets from already saved adder states.

**Usage:**
```bash
python adder_with_dataset.py --mode=from_saved --input_bit=8
```

**Arguments:**
- `--mode`: Dataset generation mode ('from_saved' or 'integrated')
- `--input_bit`: Bit width of adders (default: 8)
- `--cell_map_dir`: Directory containing saved cell maps (default: 'cell_map')
- `--output_dir`: Output directory for dataset (default: 'dataset')

## Quick Start

### Option 1: Collect Data from New Optimization Run

```bash
# Run optimization and collect training data
python collect_training_data.py \
    --input_bit=8 \
    --seed=1 \
    --max_steps=500 \
    --output_dir=dataset
```

This will:
1. Run MCTS-based adder optimization
2. Capture state transitions during the search
3. Save dataset to `dataset/adder_training_8b_seed1_TIMESTAMP.jsonl`

### Option 2: Generate Data from Saved States

First, run standard adder optimization to generate saved states:
```bash
python adder.py --input_bit=8 --level_bound_delta=0
```

Then extract training data from saved states:
```bash
python adder_with_dataset.py \
    --mode=from_saved \
    --input_bit=8 \
    --output_dir=dataset
```

### Option 3: Integrate into Custom Code

```python
from generate_dataset import DatasetGenerator

# Create generator
generator = DatasetGenerator(
    output_dir="dataset",
    dataset_name="my_adder_training"
)

# During your optimization loop:
# When you have prev_state, next_state, and operation_info
generator.add_state_transition(prev_state, next_state, operation_info)

# After optimization:
generator.save_dataset(format='jsonl')

# Get statistics
stats = generator.get_statistics()
print(stats)
```

## Dataset Format

### JSONL Format (Recommended for large datasets)

Each line is a JSON object representing one training sample:

```json
{
  "id": "sample_0",
  "input": "# Adder Design State\nInput Bits: 8\nCurrent Level (Depth): 4\nCurrent Size (Gates): 12\n...",
  "output": "# Optimization Action\nAction Type: remove_cell\nPosition: (5, 2)\n...",
  "metadata": {
    "input_bit": 8,
    "prev_level": 4,
    "next_level": 4,
    "prev_size": 12,
    "next_size": 11,
    "reward": -1.0,
    "action_id": 150,
    "position": [5, 2],
    "step": 1
  }
}
```

### JSON Format (For smaller datasets)

```json
[
  {
    "id": "sample_0",
    "input": "...",
    "output": "...",
    "metadata": {...}
  },
  ...
]
```

## Using with OpenR1 Framework

The generated dataset is compatible with OpenR1 for LLM finetuning and GRPO training.

### Finetuning Example

```python
from openr1 import FineTuner

# Load your generated dataset
dataset_path = "dataset/adder_training_8b_seed1_20250101_120000.jsonl"

# Initialize finetuner
finetuner = FineTuner(
    model_name="your-base-llm",
    dataset_path=dataset_path,
    output_dir="finetuned_models"
)

# Run finetuning
finetuner.train(
    num_epochs=3,
    batch_size=8,
    learning_rate=2e-5
)
```

### GRPO Training Example

```python
from openr1 import GRPOTrainer

# Load dataset
dataset_path = "dataset/adder_training_8b_seed1_20250101_120000.jsonl"

# Initialize GRPO trainer
trainer = GRPOTrainer(
    model_name="your-base-llm",
    dataset_path=dataset_path,
    reward_model_path="reward_model"
)

# Run GRPO training
trainer.train(
    num_iterations=100,
    batch_size=16,
    kl_coef=0.1
)
```

## Dataset Statistics

After generation, you'll see statistics like:

```
Dataset Statistics:
--------------------------------------------------------------------------------
  total_samples: 150
  reward_mean: -1.5
  reward_std: 0.8
  reward_min: -5.0
  reward_max: -0.5
  level_change_mean: 0.1
  size_change_mean: -0.9
  avg_input_bits: 8.0
```

## Best Practices

1. **Sample Size**: Collect at least 1000-5000 samples for effective finetuning
2. **Diversity**: Use multiple seeds and input_bit values to increase diversity
3. **Quality**: Filter samples with very poor rewards if needed
4. **Validation Split**: Reserve 10-20% of data for validation

### Generating Diverse Dataset

```bash
# Generate data with different configurations
for seed in 1 2 3 4 5; do
    for bits in 8 16 32; do
        python collect_training_data.py \
            --input_bit=$bits \
            --seed=$seed \
            --max_steps=500 \
            --output_dir=dataset
    done
done

# Combine all JSONL files
cat dataset/*.jsonl > dataset/combined_training_data.jsonl
```

## Troubleshooting

### Issue: Too few samples collected
**Solution**: Increase `--max_steps` parameter

### Issue: Out of memory during collection
**Solution**: Process in smaller batches or reduce `--input_bit`

### Issue: Dataset file is too large
**Solution**: Use JSONL format and process in streaming mode

## File Structure

After generation, your directory will look like:
```
dataset/
├── adder_training_8b_seed1_20250101_120000.jsonl
├── adder_training_16b_seed1_20250101_120100.jsonl
└── combined_training_data.jsonl
```

## Advanced Usage

### Custom State Representation

You can modify `state_to_text()` in `generate_dataset.py` to customize how states are represented:

```python
def state_to_text(self, state, include_maps=True):
    # Add custom fields
    text = f"# Custom State Representation\n"
    text += f"Optimization Goal: Minimize size while maintaining level <= {state.level_bound}\n"
    # ... rest of representation
    return text
```

### Custom Action Representation

Similarly, customize `action_to_text()` for different action formats:

```python
def action_to_text(self, operation_info):
    # Add analysis or reasoning
    text = f"# Reasoning\n"
    text += f"Removing cell at ({pos[0]}, {pos[1]}) because...\n"
    # ... rest of action
    return text
```

## Citation

If you use this dataset generation in your research, please cite:

```bibtex
@article{lai2024scalable,
  title={Scalable and Effective Arithmetic Tree Generation for Adder and Multiplier Designs},
  author={Lai, Yao and Liu, Jinxin and Pan, David Z and Luo, Ping},
  journal={arXiv preprint arXiv:2405.06758},
  year={2024}
}
```

## Support

For issues or questions:
1. Check this documentation
2. Review example scripts in the repository
3. Open an issue on GitHub
