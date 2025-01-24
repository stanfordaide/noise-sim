#!/bin/bash

# Create output directory if it doesn't exist
mkdir -p ./spectrum-2/output-beam-hardening

echo "Starting beam hardening spectrum-2 tests..."

# Level 1 - Minimal artifacts
echo "Testing Level 1 - Minimal artifacts..."
python beam_hardening_cli.py ./data/imbiosmall ./spectrum-2/output-beam-hardening/level1 \
    --intensity 0.15 --threshold 300 --visualize

# Level 2 - Mild artifacts
echo "Testing Level 2 - Mild artifacts..."
python beam_hardening_cli.py ./data/imbiosmall ./spectrum-2/output-beam-hardening/level2 \
    --intensity 0.3 --threshold 262 --visualize

# Level 3 - Moderate artifacts
echo "Testing Level 3 - Moderate artifacts..."
python beam_hardening_cli.py ./data/imbiosmall ./spectrum-2/output-beam-hardening/level3 \
    --intensity 0.45 --threshold 225 --visualize

# Level 4 - Marked artifacts
echo "Testing Level 4 - Marked artifacts..."
python beam_hardening_cli.py ./data/imbiosmall ./spectrum-2/output-beam-hardening/level4 \
    --intensity 0.6 --threshold 187 --visualize

# Level 5 - Severe artifacts
echo "Testing Level 5 - Severe artifacts..."
python beam_hardening_cli.py ./data/imbiosmall ./spectrum-2/output-beam-hardening/level5 \
    --intensity 0.75 --threshold 150 --visualize

echo "Beam hardening spectrum-2 tests completed." 