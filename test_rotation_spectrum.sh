#!/bin/bash

# Create output directory if it doesn't exist
mkdir -p ./spectrum-test/output-rotation-artifacts

echo "Starting rotation artifact spectrum-test tests..."

# Level 1 - Minimal patient movement
# Scenario: Slight head tremor or minor patient restlessness
echo "Testing Level 1 - Minimal movement..."
python rotate_cli.py ./data/imbiosmallwidthone ./spectrum-test/output-rotation-artifacts/level1 \
    --rx 0.5 --ry 0.3 --rz 0.2 --visualize

# Level 2 - Mild patient movement
# Scenario: Patient discomfort causing occasional shifting
echo "Testing Level 2 - Mild movement..."
python rotate_cli.py ./data/imbiosmallwidthone ./spectrum-test/output-rotation-artifacts/level2 \
    --rx 1.0 --ry 0.8 --rz 0.5 --visualize

# Level 3 - Moderate patient movement
# Scenario: Patient anxiety or difficulty holding still
echo "Testing Level 3 - Moderate movement..."
python rotate_cli.py ./data/imbiosmallwidthone ./spectrum-test/output-rotation-artifacts/level3 \
    --rx 2.0 --ry 1.5 --rz 1.0 --visualize

# Level 4 - Significant patient movement
# Scenario: Pediatric patient or elderly patient with tremor
echo "Testing Level 4 - Significant movement..."
python rotate_cli.py ./data/imbiosmallwidthone ./spectrum-test/output-rotation-artifacts/level4 \
    --rx 3.5 --ry 2.5 --rz 2.0 --visualize

# Level 5 - Maximum clinical movement
# Scenario: Severe patient discomfort or uncontrolled movement
echo "Testing Level 5 - Maximum movement..."
python rotate_cli.py ./data/imbiosmallwidthone ./spectrum-test/output-rotation-artifacts/level5 \
    --rx 5.0 --ry 4.0 --rz 3.0 --visualize

echo "Rotation artifact spectrum-test tests completed." 