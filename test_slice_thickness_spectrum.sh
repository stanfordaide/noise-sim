#!/bin/bash

# Create output directory if it doesn't exist
mkdir -p ./spectrum-2/output-thickness-artifacts

echo "Starting slice thickness spectrum-2 tests..."

# Level 1 - Minimal change (close to typical thickness)
echo "Testing Level 1 - Minimal thickness change..."
python slice_thickness_cli.py ./data/imbiosmall ./spectrum-2/output-thickness-artifacts/level1 \
    --thickness 2.0 --visualize

# Level 2-3 - Very Mild to Mild changes
echo "Testing Level 2-3 - Mild thickness change..."
python slice_thickness_cli.py ./data/imbiosmall ./spectrum-2/output-thickness-artifacts/level2 \
    --thickness 3.5 --visualize

# Level 4-5 - Moderate changes
echo "Testing Level 4-5 - Moderate thickness change..."
python slice_thickness_cli.py ./data/imbiosmall ./spectrum-2/output-thickness-artifacts/level4 \
    --thickness 5.0 --visualize

# Level 6-7 - Marked changes
echo "Testing Level 6-7 - Marked thickness change..."
python slice_thickness_cli.py ./data/imbiosmall ./spectrum-2/output-thickness-artifacts/level6 \
    --thickness 7.5 --visualize

# Level 8-9 - Severe changes
echo "Testing Level 8-9 - Severe thickness change..."
python slice_thickness_cli.py ./data/imbiosmall ./spectrum-2/output-thickness-artifacts/level8 \
    --thickness 10.0 --visualize

# Level 10 - Extreme changes
echo "Testing Level 10 - Extreme thickness change..."
python slice_thickness_cli.py ./data/imbiosmall ./spectrum-2/output-thickness-artifacts/level10 \
    --thickness 15.0 --visualize

echo "Slice thickness spectrum-2 tests completed." 