#!/bin/bash

# Create output directory if it doesn't exist
mkdir -p ./spectrum-2/output-undersample-artifacts

echo "Starting undersampling artifact spectrum-2 tests..."

# Level 1 - Minimal artifacts
echo "Testing Level 1 - Minimal artifacts..."
python undersample_cli.py ./data/imbiosmall ./spectrum-2/output-undersample-artifacts/level1 \
    --dose 0.9 --visualize

# Level 2 - Mild artifacts
echo "Testing Level 2 - Mild artifacts..."
python undersample_cli.py ./data/imbiosmall ./spectrum-2/output-undersample-artifacts/level2 \
    --dose 0.8 --visualize

# Level 3 - Moderate artifacts
echo "Testing Level 3 - Moderate artifacts..."
python undersample_cli.py ./data/imbiosmall ./spectrum-2/output-undersample-artifacts/level3 \
    --dose 0.7 --visualize

# Level 4 - Marked artifacts
echo "Testing Level 4 - Marked artifacts..."
python undersample_cli.py ./data/imbiosmall ./spectrum-2/output-undersample-artifacts/level4 \
    --dose 0.6 --visualize

# Level 5 - Severe artifacts
echo "Testing Level 5 - Severe artifacts..."
python undersample_cli.py ./data/imbiosmall ./spectrum-2/output-undersample-artifacts/level5 \
    --dose 0.5 --visualize

echo "Undersampling artifact spectrum-2 tests completed." 