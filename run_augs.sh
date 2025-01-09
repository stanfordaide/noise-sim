#!/bin/bash

# Create output directory if it doesn't exist
mkdir -p ./output

echo "Starting CT artifact simulation tests..."

# Motion artifacts - testing different scenarios
python motion_cli.py ./data/imbio ./output --amplitude_x 5 --amplitude_y 0 --visualize  # Subtle movement
python motion_cli.py ./data/imbio ./output --amplitude_x 15 --amplitude_y 0 --direction 45 --visualize  # Strong sudden movement
python motion_cli.py ./data/imbio ./output --amplitude_x 10 --amplitude_y 0 --direction 90 --visualize  # Breathing-like motion

# Undersampling (Low-dose) variations
python undersample_cli.py ./data/imbio ./output --dose 0.7 --visualize  # Mild dose reduction
python undersample_cli.py ./data/imbio ./output --dose 0.3 --visualize  # Significant dose reduction

# Slice thickness variations - covering common clinical ranges
python slice_thickness_cli.py ./data/imbio/ ./output --thickness 1.0 --visualize  # Thin diagnostic
python slice_thickness_cli.py ./data/imbio/ ./output --thickness 3.0 --visualize  # Standard clinical
python slice_thickness_cli.py ./data/imbio/ ./output --thickness 7.0 --visualize  # Thick screening

# Noise variations - different types and intensities
python noise_cli.py ./data/imbio/ ./output --noise-type gaussian --std 50 --visualize  # Moderate electronic noise
python noise_cli.py ./data/imbio/ ./output --noise-type gaussian --std 100 --visualize  # Heavy electronic noise
python noise_cli.py ./data/imbio/ ./output --noise-type salt_and_pepper --prob 0.05 --visualize  # Sparse impulse noise

# Beam hardening - realistic clinical scenarios
python beam_hardening_cli.py ./data/imbio/ ./output --intensity 0.4 --threshold 200 --visualize  # Moderate, typical bone
python beam_hardening_cli.py ./data/imbio/ ./output --intensity 0.8 --threshold 300 --visualize  # Strong, dense structures

# Ring artifacts - varying patterns
python ring_cli.py ./data/imbio ./output --num-rings 3 --intensity 0.4 --thickness 2 --visualize  # Subtle detector issues
python ring_cli.py ./data/imbio ./output --num-rings 8 --intensity 0.7 --thickness 3 --visualize  # Multiple detector defects

echo "CT artifact simulation tests completed."
