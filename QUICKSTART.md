# Quick Start Guide: Dataset Generation for LLM Training

This guide will get you started with generating datasets for LLM finetuning or GRPO training in under 5 minutes.

## Prerequisites

```bash
pip install torch numpy tqdm
```

## 1. Generate Your First Dataset (30 seconds)

```bash
python generate_dataset.py --input_bit=8 --num_trajectories=5 --openr1_format
```

This creates:
- `dataset/dataset_8b_sklansky_5traj_lbd1_random.jsonl` - Raw format
- `dataset/openr1_dataset_8b_sklansky_5traj_lbd1_random.jsonl` - OpenR1 format

## 2. Inspect the Dataset

```bash
python example_dataset_usage.py dataset/openr1_dataset_8b_sklansky_5traj_lbd1_random.jsonl
```

## 3. Generate a Training-Ready Dataset

For actual training, generate a larger dataset:

```bash
python generate_dataset.py \
  --input_bit=16 \
  --num_trajectories=100 \
  --max_steps=30 \
  --level_bound_delta=2 \
  --openr1_format
```

Expected: ~500-1000 samples in < 10 seconds

## 4. Use the Dataset for Training

### Option A: With OpenR1/GRPO Framework

```python
import json

# Load dataset
with open('dataset/openr1_dataset_16b_sklansky_100traj_lbd2_random.jsonl', 'r') as f:
    dataset = [json.loads(line) for line in f]

# Each sample has:
# - prompt: State description
# - completion: Optimization action
# - reward: Improvement score

# Use with your GRPO trainer
from your_framework import GRPOTrainer
trainer = GRPOTrainer(model=your_model, dataset=dataset)
trainer.train()
```

### Option B: With Standard Supervised Fine-Tuning

```python
from transformers import AutoModelForCausalLM, Trainer

# Load your model
model = AutoModelForCausalLM.from_pretrained("your-base-model")

# Convert dataset to training format
train_data = []
for sample in dataset:
    text = sample['prompt'] + sample['completion']
    train_data.append(tokenizer(text))

# Train
trainer = Trainer(model=model, train_dataset=train_data)
trainer.train()
```

## 5. Advanced: Generate Multiple Datasets

```bash
bash generate_batch_datasets.sh
```

This generates datasets with different configurations for comprehensive training.

## Common Commands

### Small test dataset
```bash
python generate_dataset.py --input_bit=8 --num_trajectories=5 --openr1_format
```

### Medium training dataset
```bash
python generate_dataset.py --input_bit=16 --num_trajectories=50 --openr1_format
```

### Large production dataset
```bash
python generate_dataset.py --input_bit=32 --num_trajectories=200 --openr1_format
```

### Expert demonstrations (best actions only)
```bash
python generate_dataset.py --input_bit=16 --num_trajectories=50 --sample_strategy=best --openr1_format
```

### From suboptimal starting point
```bash
python generate_dataset.py --input_bit=16 --num_trajectories=50 --init_type=normal --level_bound_delta=3 --openr1_format
```

## Dataset Format

### OpenR1 Format (for GRPO/RL training)
```json
{
  "prompt": "You are an expert in optimizing arithmetic hardware...",
  "completion": "Remove cell at position (3,2)",
  "reward": 7.0,
  "metadata": {...}
}
```

### Raw Format (for analysis/custom training)
```json
{
  "trajectory_id": 0,
  "step": 0,
  "state": {...},
  "action": {...},
  "next_state": {...},
  "improvement": {...}
}
```

## Troubleshooting

### "Generated 0 samples"
- Increase `--level_bound_delta` to 2 or 3
- Try different `--init_type` (e.g., `brent_kung` or `normal`)

### Dataset too large
- Reduce `--num_trajectories` or `--max_steps`
- Use `--sample_strategy=random` instead of `all_valid`

### Trajectories too short
- Increase `--level_bound_delta`
- Use `--init_type=normal` for more optimization potential

## Next Steps

1. Read [DATASET_GENERATION.md](DATASET_GENERATION.md) for detailed documentation
2. Check [dataset_configs.txt](dataset_configs.txt) for configuration examples
3. Run [test_dataset_generation.py](test_dataset_generation.py) to verify installation
4. Adapt [advanced_training_example.py](advanced_training_example.py) for your training framework

## Support

For issues or questions, please refer to:
- Full documentation: [DATASET_GENERATION.md](DATASET_GENERATION.md)
- Configuration examples: [dataset_configs.txt](dataset_configs.txt)
- Original paper: https://arxiv.org/abs/2405.06758
