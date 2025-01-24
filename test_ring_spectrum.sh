#!/bin/bash

# Create output directory if it doesn't exist
mkdir -p ./spectrum-2/output-ring-artifacts

echo "Starting ring artifact spectrum-2 tests..."

# Level 5 - Severe artifacts
# Clinical relevance: Significant image quality degradation that may affect diagnosis.
# Typically seen in older scanners with multiple defective detector elements or
# severe calibration issues. May require immediate scanner maintenance.
echo "Testing Level 5 - Severe artifacts..."
python ring_cli.py ./data/imbiosmall ./spectrum-2/output-ring-artifacts/level5 \
    --num-defects 8 --intensity 1.25 --width 2 --radius-min 0.4 --radius-max 0.5 \
    --angle-range 90 --visualize

# Level 4 - Marked artifacts
# Clinical relevance: Noticeable ring artifacts that could interfere with detection
# of subtle pathology. May affect quantitative measurements in the affected region.
# Scanner calibration recommended.
echo "Testing Level 4 - Marked artifacts..."
python ring_cli.py ./data/imbiosmall ./spectrum-2/output-ring-artifacts/level4 \
    --num-defects 7 --intensity 1.2 --width 2 --radius-min 0.42 --radius-max 0.5 \
    --angle-range 80 --visualize

# Level 3 - Moderate artifacts
# Clinical relevance: Visible rings that typically don't impact diagnostic confidence
# but should be documented. Common in routine clinical practice, may indicate need
# for upcoming detector calibration.
echo "Testing Level 3 - Moderate artifacts..."
python ring_cli.py ./data/imbiosmall ./spectrum-2/output-ring-artifacts/level3 \
    --num-defects 5 --intensity 1.15 --width 1 --radius-min 0.43 --radius-max 0.5 \
    --angle-range 70 --visualize

# Level 2 - Mild artifacts
# Clinical relevance: Subtle rings visible to trained observers but unlikely to
# affect diagnosis. Typical of well-maintained scanners during normal operation.
echo "Testing Level 2 - Mild artifacts..."
python ring_cli.py ./data/imbiosmall ./spectrum-2/output-ring-artifacts/level2 \
    --num-defects 4 --intensity 1.12 --width 1 --radius-min 0.44 --radius-max 0.5 \
    --angle-range 65 --visualize

# Level 1 - Minimal artifacts
# Clinical relevance: Barely perceptible rings that meet highest image quality
# standards. Representative of optimal scanner performance after calibration.
echo "Testing Level 1 - Minimal artifacts..."
python ring_cli.py ./data/imbiosmall ./spectrum-2/output-ring-artifacts/level1 \
    --num-defects 3 --intensity 1.1 --width 1 --radius-min 0.45 --radius-max 0.5 \
    --angle-range 60 --visualize

echo "Ring artifact spectrum-2 tests completed." 
