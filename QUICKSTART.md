# Quick Start Guide - Dataset Generation for LLM Training

This guide will help you quickly get started with generating training datasets from adder optimization for LLM finetuning and GRPO training.

## Prerequisites

```bash
# Install required dependencies
pip install numpy torch
```

## 5-Minute Quick Start

### 1. Generate a Small Dataset

```bash
# Collect 100 optimization steps for 8-bit adder
python collect_training_data.py \
    --input_bit=8 \
    --seed=1 \
    --max_steps=100 \
    --level_bound_delta=1 \
    --output_dir=dataset
```

This will create a file like `dataset/adder_training_8b_seed1_TIMESTAMP.jsonl`

### 2. Verify the Dataset

```bash
# Analyze the generated dataset
python example_training_integration.py \
    --dataset=dataset/adder_training_8b_seed1_*.jsonl \
    --mode=analyze
```

You should see output like:
```
Dataset Analysis:
================================================================================
total_samples: 50
input_bits: {8: 50}
avg_reward: -1.2
avg_size_reduction: 0.85
level_changes: {'same': 48, 'increased': 2}
```

### 3. Test Training Structure

```bash
# Run mock finetuning (shows the training structure)
python example_training_integration.py \
    --dataset=dataset/adder_training_8b_seed1_*.jsonl \
    --mode=finetune \
    --epochs=2
```

## Next Steps

### Generate Production Dataset

For actual training, generate a larger dataset with multiple configurations:

```bash
# Run the complete workflow
chmod +x complete_workflow_example.sh
./complete_workflow_example.sh
```

Or manually:

```bash
# Generate diverse training data
for seed in 1 2 3 4 5; do
    for bits in 8 16 32; do
        python collect_training_data.py \
            --input_bit=$bits \
            --seed=$seed \
            --max_steps=500 \
            --level_bound_delta=1 \
            --output_dir=dataset
    done
done

# Combine all datasets
cat dataset/adder_training_*.jsonl > dataset/combined_training_data.jsonl
```

### Integrate with OpenR1

1. **Install OpenR1** (when available):
```bash
pip install openr1
```

2. **Create configuration** (see `OPENR1_CONFIG.md`):
```yaml
# openr1_config.yaml
model:
  name: "gpt2"
training:
  dataset_path: "dataset/combined_training_data.jsonl"
  num_epochs: 3
  batch_size: 16
```

3. **Run finetuning**:
```bash
openr1 train --config openr1_config.yaml
```

4. **Run GRPO training**:
```bash
openr1 grpo --config openr1_grpo_config.yaml
```

## Example Dataset Sample

Each line in the JSONL file contains:

```json
{
  "id": "sample_0",
  "input": "# Adder Design State\nInput Bits: 8\nCurrent Level: 4\n...",
  "output": "# Optimization Action\nAction Type: remove_cell\n...",
  "metadata": {
    "input_bit": 8,
    "prev_level": 4,
    "next_level": 4,
    "reward": -1.0,
    ...
  }
}
```

## Common Use Cases

### Use Case 1: Fine-tune LLM to suggest optimization actions

```bash
# 1. Generate dataset
python collect_training_data.py --input_bit=16 --max_steps=1000

# 2. Train with OpenR1
openr1 train --config finetune_config.yaml

# 3. Use trained model
python -c "
from openr1 import load_model
model = load_model('finetuned_models/best')
suggestion = model.generate(adder_state_text)
print(suggestion)
"
```

### Use Case 2: Train with GRPO for better optimization

```bash
# 1. Generate dataset
python collect_training_data.py --input_bit=16 --max_steps=1000

# 2. Fine-tune first
openr1 train --config finetune_config.yaml

# 3. GRPO training for optimization
openr1 grpo --config grpo_config.yaml
```

### Use Case 3: Generate from existing runs

```bash
# If you already ran adder.py and have saved states
python adder.py --input_bit=16 --level_bound_delta=0

# Extract dataset from saved states
python adder_with_dataset.py \
    --mode=from_saved \
    --input_bit=16
```

## Troubleshooting

### Problem: No samples collected
**Solution**: Increase `--level_bound_delta` to allow more optimization steps

```bash
python collect_training_data.py --level_bound_delta=1  # or 2
```

### Problem: Dataset too small
**Solution**: Increase `--max_steps` and use multiple seeds

```bash
python collect_training_data.py --max_steps=1000 --seed=1
python collect_training_data.py --max_steps=1000 --seed=2
# ... combine datasets
```

### Problem: Training unstable
**Solution**: Filter low-quality samples or adjust training hyperparameters

```python
# Filter samples with very negative rewards
import json
filtered = []
with open('dataset.jsonl') as f:
    for line in f:
        sample = json.loads(line)
        if sample['metadata']['reward'] > -3.0:
            filtered.append(sample)

with open('filtered_dataset.jsonl', 'w') as f:
    for sample in filtered:
        f.write(json.dumps(sample) + '\n')
```

## Files Overview

- `generate_dataset.py` - Core dataset generation module
- `collect_training_data.py` - Collect data during optimization
- `adder_with_dataset.py` - Generate from saved states
- `test_dataset_generation.py` - Tests for dataset generation
- `example_training_integration.py` - Example training structure
- `complete_workflow_example.sh` - Complete end-to-end workflow

## Documentation

- [DATASET_GENERATION.md](DATASET_GENERATION.md) - Full documentation
- [OPENR1_CONFIG.md](OPENR1_CONFIG.md) - OpenR1 integration guide
- [README.md](README.md) - Main project README

## Support

For issues or questions:
1. Check the documentation files
2. Run the test suite: `python test_dataset_generation.py`
3. Try the example workflow: `./complete_workflow_example.sh`
4. Open an issue on GitHub

---

**Ready to start?** Run:
```bash
python collect_training_data.py --input_bit=16 --max_steps=500 --level_bound_delta=1
```
