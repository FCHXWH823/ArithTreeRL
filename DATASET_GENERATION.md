# Dataset Generation for LLM Finetuning and GRPO Training

This document describes how to generate training datasets from the ArithTreeRL repository for finetuning Large Language Models (LLMs) or training with Guided Reward Proximal Optimization (GRPO).

## Overview

The `generate_dataset.py` script creates datasets where each sample consists of:
- **Input**: Current state of an adder design (cell map, level, size, available actions)
- **Output**: An optimization action that improves the design
- **Reward**: The improvement achieved by the action

This dataset format is suitable for:
1. **Supervised Fine-Tuning (SFT)**: Teaching LLMs to propose optimization actions
2. **GRPO Training**: Reinforcement learning with reward signals using frameworks like OpenR1

## Usage

### Basic Usage

Generate a dataset for an 8-bit adder with default parameters:

```bash
python generate_dataset.py --input_bit=8 --num_trajectories=10 --openr1_format
```

### Advanced Usage

Generate a dataset with custom parameters:

```bash
python generate_dataset.py \
  --input_bit=16 \
  --num_trajectories=20 \
  --max_steps=30 \
  --sample_strategy=random \
  --level_bound_delta=2 \
  --init_type=sklansky \
  --output_dir=my_dataset \
  --openr1_format
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--input_bit` | int | 8 | Number of bits for the adder (e.g., 8, 16, 32, 64, 128) |
| `--num_trajectories` | int | 10 | Number of optimization trajectories to generate |
| `--max_steps` | int | 50 | Maximum optimization steps per trajectory |
| `--sample_strategy` | str | random | Action sampling strategy: `random`, `best`, or `all_valid` |
| `--level_bound_delta` | int | 1 | Additional level bound flexibility (higher = more relaxed constraints) |
| `--init_type` | str | sklansky | Initial adder type: `sklansky`, `brent_kung`, or `normal` |
| `--output_dir` | str | dataset | Output directory for generated datasets |
| `--output_format` | str | jsonl | Output format: `json` or `jsonl` |
| `--seed` | int | 42 | Random seed for reproducibility |
| `--openr1_format` | flag | False | Also generate dataset in OpenR1 format for LLM training |

## Output Formats

### Raw Format

The raw dataset format includes complete state information:

```json
{
  "trajectory_id": 0,
  "step": 0,
  "state": {
    "input_bit": 8,
    "level": 4,
    "size": 12,
    "level_bound": 5,
    "available_choice": 4,
    "cell_map": [[1, 0, ...], ...],
    "level_map": [[1, 0, ...], ...],
    "min_map": [[0, 0, ...], ...],
    "available_actions": [90, 230, 246, 254],
    "step_num": 0,
    "reward": 0.0
  },
  "state_text": "Input Bits: 8\nCurrent Level: 4.0\n...",
  "action": {
    "action": 90,
    "action_type": 1,
    "position": {"x": 3, "y": 2},
    "description": "Remove cell at position (3,2)"
  },
  "next_state": {...},
  "improvement": {
    "level_change": 1,
    "size_change": -1,
    "reward": 7.0
  }
}
```

### OpenR1 Format

The OpenR1 format is optimized for LLM training:

```json
{
  "prompt": "You are an expert in optimizing arithmetic hardware designs...",
  "completion": "Remove cell at position (3,2)",
  "reward": 7.0,
  "metadata": {
    "trajectory_id": 0,
    "step": 0,
    "level_change": 1,
    "size_change": -1
  }
}
```

## Sample Strategies

### Random Strategy (`--sample_strategy=random`)
- Samples one random valid action at each step
- Creates diverse trajectories
- Good for exploration and general-purpose training

### Best Strategy (`--sample_strategy=best`)
- Always selects the action that provides maximum improvement
- Creates optimal trajectories
- Good for learning best practices

### All Valid Strategy (`--sample_strategy=all_valid`)
- Generates samples for all valid actions from each state
- Creates comprehensive datasets
- Good for covering the full action space (but produces large datasets)

## Initialization Types

### Sklansky (`--init_type=sklansky`)
- Fast parallel prefix adder
- Already near-optimal structure
- Good for fine-tuning optimizations

### Brent-Kung (`--init_type=brent_kung`)
- Area-efficient adder design
- More room for optimization
- Good for learning significant improvements

### Normal/Ripple-Carry (`--init_type=normal`)
- Simple ripple-carry adder
- Maximum room for optimization
- Good for learning from basic structures

## Level Bound Delta

The `level_bound_delta` parameter controls how much flexibility is allowed in the optimization process:

- **0**: Tight bound (log₂(N) + 1), most restrictive
- **1-2**: Moderate flexibility, good balance for most cases
- **3+**: High flexibility, allows more exploration but may sacrifice optimality

For reference, level bounds by bit width:
- 8-bit: base bound = 4
- 16-bit: base bound = 5
- 32-bit: base bound = 6
- 64-bit: base bound = 7
- 128-bit: base bound = 8

## Examples

### Example 1: Small Dataset for Quick Testing

```bash
python generate_dataset.py \
  --input_bit=8 \
  --num_trajectories=5 \
  --max_steps=10 \
  --level_bound_delta=1 \
  --openr1_format
```

Expected output: ~20-50 samples in < 1 second

### Example 2: Medium Dataset for Training

```bash
python generate_dataset.py \
  --input_bit=16 \
  --num_trajectories=50 \
  --max_steps=30 \
  --level_bound_delta=2 \
  --sample_strategy=random \
  --openr1_format
```

Expected output: ~500-1000 samples in < 10 seconds

### Example 3: Large Dataset for Comprehensive Training

```bash
python generate_dataset.py \
  --input_bit=32 \
  --num_trajectories=100 \
  --max_steps=50 \
  --level_bound_delta=2 \
  --sample_strategy=random \
  --openr1_format
```

Expected output: ~2000-5000 samples in < 1 minute

### Example 4: Multi-size Dataset

Generate datasets for multiple bit widths:

```bash
for bits in 8 16 32; do
  python generate_dataset.py \
    --input_bit=$bits \
    --num_trajectories=50 \
    --max_steps=30 \
    --level_bound_delta=2 \
    --output_dir=dataset_multsize \
    --openr1_format
done
```

## Using with OpenR1 Framework

The OpenR1 format is designed for use with reinforcement learning frameworks like OpenR1. Here's how to use it:

1. **Generate the dataset**:
```bash
python generate_dataset.py --openr1_format
```

2. **Load in your training script**:
```python
import json

# Load OpenR1 format dataset
with open('dataset/openr1_dataset_8b_sklansky_10traj_lbd1_random.jsonl', 'r') as f:
    dataset = [json.loads(line) for line in f]

# Each sample has:
# - prompt: Input text describing the current state
# - completion: Target action to predict
# - reward: Reward signal for GRPO training
```

3. **Fine-tune your LLM**:
```python
from openr1 import GRPOTrainer  # Example - adjust for your framework

trainer = GRPOTrainer(
    model=your_model,
    dataset=dataset,
    reward_key="reward",
    # ... other training parameters
)

trainer.train()
```

## Dataset Statistics

After generation, the script prints statistics about the dataset:

```
Dataset Statistics:
  Total samples: 18
  Average reward: 1.67
  Average size change: -1.00
  Average level change: 0.17
```

- **Average reward**: Higher is generally better (indicates more improvement)
- **Average size change**: Negative values indicate reduction in circuit size
- **Average level change**: Small positive values indicate slight level increases for size reduction

## Tips and Best Practices

1. **Start small**: Test with `--input_bit=8` and `--num_trajectories=5` first
2. **Adjust level_bound_delta**: If you get very few samples, increase `level_bound_delta`
3. **Use random strategy**: For most training scenarios, `random` strategy provides good diversity
4. **Generate diverse datasets**: Create datasets with different bit widths and initialization types
5. **Monitor statistics**: Check that average rewards and size changes are reasonable

## Integration with Original Code

This dataset generation script is compatible with the original `adder.py` MCTS code. The state representations and transition logic are identical, ensuring that actions learned from this dataset can be applied to the original optimization process.

## Requirements

- Python >= 3.9
- PyTorch >= 1.10
- NumPy >= 1.20
- tqdm (optional, for progress bars)

Install with:
```bash
pip install torch numpy tqdm
```

## Troubleshooting

### Problem: Getting 0 samples

**Solution**: Increase `--level_bound_delta` or change `--init_type`:
```bash
python generate_dataset.py --level_bound_delta=2 --init_type=brent_kung
```

### Problem: Dataset is too large

**Solution**: Reduce `--num_trajectories` or `--max_steps`, or change from `all_valid` to `random`:
```bash
python generate_dataset.py --sample_strategy=random --max_steps=20
```

### Problem: Trajectories are too short

**Solution**: Increase `--level_bound_delta` to allow more optimization steps:
```bash
python generate_dataset.py --level_bound_delta=3
```

## Citation

If you use this dataset generation tool in your research, please cite the original ArithTreeRL paper:

```bibtex
@article{lai2024scalable,
  title={Scalable and Effective Arithmetic Tree Generation for Adder and Multiplier Designs},
  author={Lai, Yao and Liu, Jinxin and Pan, David Z and Luo, Ping},
  journal={arXiv preprint arXiv:2405.06758},
  year={2024}
}
```
