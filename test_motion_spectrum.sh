#!/bin/bash

# Create output directory if it doesn't exist
mkdir -p ./spectrum-2/output-motion

echo "Starting motion artifact spectrum-2 tests..."

# Level 1 - Minimal artifacts
echo "Testing Level 1 - Minimal artifacts..."
python motion_cli.py ./data/imbiosmall ./spectrum-2/output-motion/level1 \
    --amplitude_x 2 --amplitude_y 0 --visualize

# Level 2 - Mild artifacts
echo "Testing Level 2 - Mild artifacts..."
python motion_cli.py ./data/imbiosmall ./spectrum-2/output-motion/level2 \
    --amplitude_x 4 --amplitude_y 1 --visualize

# Level 3 - Moderate artifacts
echo "Testing Level 3 - Moderate artifacts..."
python motion_cli.py ./data/imbiosmall ./spectrum-2/output-motion/level3 \
    --amplitude_x 6 --amplitude_y 2 --visualize

# Level 4 - Marked artifacts
echo "Testing Level 4 - Marked artifacts..."
python motion_cli.py ./data/imbiosmall ./spectrum-2/output-motion/level4 \
    --amplitude_x 8 --amplitude_y 3 --visualize

# Level 5 - Severe artifacts
echo "Testing Level 5 - Severe artifacts..."
python motion_cli.py ./data/imbiosmall ./spectrum-2/output-motion/level5 \
    --amplitude_x 10 --amplitude_y 4 --visualize

echo "Motion artifact spectrum-2 tests completed." 