#!/bin/bash
# Batch dataset generation script
# This script generates multiple datasets with different configurations

set -e  # Exit on error

echo "==================================================================="
echo "ArithTreeRL Dataset Batch Generation"
echo "==================================================================="

# Create output directory
DATASET_DIR="dataset_batch_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DATASET_DIR"

echo "Output directory: $DATASET_DIR"
echo ""

# =============================================================================
# Generate datasets for different bit widths
# =============================================================================
echo "Generating datasets for multiple bit widths..."

for BITS in 8 16 32; do
  echo ""
  echo "--- Generating ${BITS}-bit dataset ---"
  python generate_dataset.py \
    --input_bit=$BITS \
    --num_trajectories=50 \
    --max_steps=30 \
    --sample_strategy=random \
    --level_bound_delta=2 \
    --init_type=sklansky \
    --output_dir="$DATASET_DIR" \
    --openr1_format \
    --seed=42
done

# =============================================================================
# Generate datasets for different initialization types
# =============================================================================
echo ""
echo "==================================================================="
echo "Generating datasets for different initialization types..."

for INIT_TYPE in sklansky brent_kung normal; do
  echo ""
  echo "--- Generating dataset with ${INIT_TYPE} initialization ---"
  python generate_dataset.py \
    --input_bit=16 \
    --num_trajectories=30 \
    --max_steps=30 \
    --sample_strategy=random \
    --level_bound_delta=2 \
    --init_type=$INIT_TYPE \
    --output_dir="$DATASET_DIR" \
    --openr1_format \
    --seed=42
done

# =============================================================================
# Generate datasets with different sampling strategies
# =============================================================================
echo ""
echo "==================================================================="
echo "Generating datasets with different sampling strategies..."

for STRATEGY in random best; do
  echo ""
  echo "--- Generating dataset with ${STRATEGY} strategy ---"
  python generate_dataset.py \
    --input_bit=16 \
    --num_trajectories=30 \
    --max_steps=25 \
    --sample_strategy=$STRATEGY \
    --level_bound_delta=2 \
    --init_type=sklansky \
    --output_dir="$DATASET_DIR" \
    --openr1_format \
    --seed=42
done

# =============================================================================
# Summary
# =============================================================================
echo ""
echo "==================================================================="
echo "Dataset generation complete!"
echo "==================================================================="
echo "Output directory: $DATASET_DIR"
echo ""
echo "Generated files:"
ls -lh "$DATASET_DIR"/*.jsonl
echo ""
echo "Total dataset size:"
du -sh "$DATASET_DIR"
echo ""
echo "Number of samples per file:"
for FILE in "$DATASET_DIR"/*.jsonl; do
  COUNT=$(wc -l < "$FILE")
  echo "  $(basename $FILE): $COUNT samples"
done

echo ""
echo "You can now use these datasets for training!"
echo "See DATASET_GENERATION.md for usage instructions."
