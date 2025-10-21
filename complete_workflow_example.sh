#!/bin/bash
# complete_workflow_example.sh - Complete workflow for dataset generation and training
# 
# This script demonstrates the complete workflow from adder optimization to
# dataset generation to LLM training preparation.

set -e  # Exit on error

echo "================================================================================"
echo "Complete Dataset Generation and Training Workflow Example"
echo "================================================================================"

# Configuration
INPUT_BITS=(8 16)
SEEDS=(1 2 3)
MAX_STEPS=200
LEVEL_BOUND_DELTA=1
OUTPUT_DIR="dataset_example"

echo ""
echo "Configuration:"
echo "  Input bits: ${INPUT_BITS[*]}"
echo "  Seeds: ${SEEDS[*]}"
echo "  Max steps per run: $MAX_STEPS"
echo "  Level bound delta: $LEVEL_BOUND_DELTA"
echo "  Output directory: $OUTPUT_DIR"
echo ""

# Step 1: Collect training data
echo "================================================================================"
echo "Step 1: Collecting Training Data"
echo "================================================================================"
echo ""

for bits in "${INPUT_BITS[@]}"; do
    for seed in "${SEEDS[@]}"; do
        echo "Collecting data for ${bits}b with seed ${seed}..."
        python collect_training_data.py \
            --input_bit=$bits \
            --seed=$seed \
            --max_steps=$MAX_STEPS \
            --level_bound_delta=$LEVEL_BOUND_DELTA \
            --output_dir=$OUTPUT_DIR \
            2>&1 | tail -20
        echo ""
    done
done

# Step 2: Analyze collected datasets
echo "================================================================================"
echo "Step 2: Analyzing Collected Datasets"
echo "================================================================================"
echo ""

for dataset in $OUTPUT_DIR/*.jsonl; do
    if [ -f "$dataset" ]; then
        echo "Analyzing: $dataset"
        python example_training_integration.py \
            --dataset="$dataset" \
            --mode=analyze
        echo ""
    fi
done

# Step 3: Combine datasets (optional)
echo "================================================================================"
echo "Step 3: Combining Datasets"
echo "================================================================================"
echo ""

COMBINED_DATASET="$OUTPUT_DIR/combined_training_data.jsonl"
cat $OUTPUT_DIR/adder_training_*.jsonl > $COMBINED_DATASET
echo "Combined dataset created: $COMBINED_DATASET"
echo "Total lines: $(wc -l < $COMBINED_DATASET)"
echo ""

# Step 4: Analyze combined dataset
echo "Analyzing combined dataset..."
python example_training_integration.py \
    --dataset="$COMBINED_DATASET" \
    --mode=analyze
echo ""

# Step 5: Run mock training
echo "================================================================================"
echo "Step 4: Running Mock Finetuning"
echo "================================================================================"
echo ""

python example_training_integration.py \
    --dataset="$COMBINED_DATASET" \
    --mode=finetune \
    --epochs=2 \
    --batch_size=16

echo ""

# Step 6: Run mock GRPO
echo "================================================================================"
echo "Step 5: Running Mock GRPO Training"
echo "================================================================================"
echo ""

python example_training_integration.py \
    --dataset="$COMBINED_DATASET" \
    --mode=grpo \
    --iterations=20 \
    --batch_size=16

echo ""

# Summary
echo "================================================================================"
echo "Workflow Complete!"
echo "================================================================================"
echo ""
echo "Generated datasets are in: $OUTPUT_DIR"
echo "Combined dataset: $COMBINED_DATASET"
echo ""
echo "Next steps for real training:"
echo "1. Install OpenR1 framework"
echo "2. Create OpenR1 configuration file (see OPENR1_CONFIG.md)"
echo "3. Run actual finetuning: openr1 train --config openr1_finetune_config.yaml"
echo "4. Run GRPO training: openr1 grpo --config openr1_grpo_config.yaml"
echo ""
echo "For more information:"
echo "  - See DATASET_GENERATION.md for detailed documentation"
echo "  - See OPENR1_CONFIG.md for OpenR1 integration examples"
echo "  - See example_training_integration.py for training structure"
echo ""
echo "================================================================================"
