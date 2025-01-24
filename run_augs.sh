#!/bin/bash

# Create output directory if it doesn't exist
mkdir -p ./output-augmentations

echo "Starting CT artifact simulation tests..."

echo "Part 1: Testing realistic clinical scenarios..."

# Slice thickness variations - clinical ranges
# echo "Testing typical clinical slice thickness modifications..."
# python slice_thickness_cli.py ./data/imbio ./output-augmentations --thickness 1.0 --visualize  # Thin slices
# python slice_thickness_cli.py ./data/imbio ./output-augmentations --thickness 2.5 --visualize  # Standard slices
# python slice_thickness_cli.py ./data/imbio ./output-augmentations --thickness 5.0 --visualize  # Thick slices
# python slice_thickness_cli.py ./data/imbio ./output-augmentations --thickness 7.0 --visualize  # Extra thick slices

# # Noise variations - typical and clinical noise levels
# echo "Testing typical clinical noise levels..."
# python noise_cli.py ./data/imbio ./output-augmentations --noise-type gaussian --std 30 --visualize  # Low noise
# python noise_cli.py ./data/imbio ./output-augmentations --noise-type gaussian --std 60 --visualize  # Moderate noise
# python noise_cli.py ./data/imbio ./output-augmentations --noise-type gaussian --std 100 --visualize  # Heavy noise
# python noise_cli.py ./data/imbio ./output-augmentations --noise-type salt_and_pepper --prob 0.02 --visualize  # Typical artifact
python noise_cli.py ./data/imbio ./output-augmentations --noise-type salt_and_pepper --prob 0.05 --visualize  # Strong artifact

# Motion artifacts - typical patient movement
echo "Testing typical motion artifacts..."
python motion_cli.py ./data/imbio ./output-augmentations --amplitude_x 3 --amplitude_y 0 --visualize  # Mild breathing
python motion_cli.py ./data/imbio ./output-augmentations --amplitude_x 7 --amplitude_y 2 --visualize  # Normal movement

# Beam hardening - common clinical scenarios
echo "Testing typical beam hardening..."
python beam_hardening_cli.py ./data/imbio ./output-augmentations --intensity 0.3 --threshold 180 --visualize  # Mild
python beam_hardening_cli.py ./data/imbio ./output-augmentations --intensity 0.5 --threshold 250 --visualize  # Moderate
python beam_hardening_cli.py ./data/imbio ./output-augmentations --intensity 0.8 --threshold 300 --visualize  # Strong

# Ring artifacts - typical scanner issues
echo "Testing typical ring artifacts..."
python ring_cli.py ./data/imbio ./output-augmentations --num-rings 2 --intensity 0.3 --thickness 2 --visualize  # Subtle
python ring_cli.py ./data/imbio ./output-augmentations --num-rings 4 --intensity 0.5 --thickness 2 --visualize  # Moderate
python ring_cli.py ./data/imbio ./output-augmentations --num-rings 8 --intensity 0.7 --thickness 3 --visualize  # Multiple defects

# Undersampling variations
echo "Testing realistic dose reductions..."
python undersample_cli.py ./data/imbio ./output-augmentations --dose 0.7 --visualize  # 30% reduction
python undersample_cli.py ./data/imbio ./output-augmentations --dose 0.5 --visualize  # 50% reduction

# Add rotation variations section
echo "Testing typical patient positioning variations..."
python rotate_cli.py ./data/imbio ./output-augmentations --rx 5 --ry 0 --rz 0 --visualize  # Slight head tilt
python rotate_cli.py ./data/imbio ./output-augmentations --rx 0 --ry 10 --rz 0 --visualize  # Moderate lateral tilt
python rotate_cli.py ./data/imbio ./output-augmentations --rx 0 --ry 0 --rz 8 --visualize  # Slight rotation

echo "Part 2: Testing extreme scenarios for stress testing..."

# Extreme cases
echo "Testing extreme scenarios..."
python slice_thickness_cli.py ./data/imbio ./output-augmentations --thickness 0.5 --visualize  # Ultra-thin
python slice_thickness_cli.py ./data/imbio ./output-augmentations --thickness 10.0 --visualize  # Very thick

python noise_cli.py ./data/imbio ./output-augmentations --noise-type gaussian --std 150 --visualize  # Very high noise
python noise_cli.py ./data/imbio ./output-augmentations --noise-type salt_and_pepper --prob 0.2 --visualize  # Severe artifacts

python motion_cli.py ./data/imbio ./output-augmentations --amplitude_x 20 --amplitude_y 10 --visualize  # Large movement
python motion_cli.py ./data/imbio ./output-augmentations --amplitude_x 30 --amplitude_y 15 --visualize  # Extreme movement

python beam_hardening_cli.py ./data/imbio ./output-augmentations --intensity 0.9 --threshold 150 --visualize  # Strong
python beam_hardening_cli.py ./data/imbio ./output-augmentations --intensity 1.0 --threshold 400 --visualize  # Extreme

python ring_cli.py ./data/imbio ./output-augmentations --num-rings 8 --intensity 0.8 --thickness 4 --visualize  # Multiple strong
python ring_cli.py ./data/imbio ./output-augmentations --num-rings 12 --intensity 1.0 --thickness 5 --visualize  # Maximum artifacts

python undersample_cli.py ./data/imbio ./output-augmentations --dose 0.2 --visualize  # Very low dose
python undersample_cli.py ./data/imbio ./output-augmentations --dose 0.1 --visualize  # Ultra-low dose

# Add extreme rotation tests
echo "Testing extreme patient positioning..."
python rotate_cli.py ./data/imbio ./output-augmentations --rx 15 --ry 0 --rz 0 --visualize  # Large head tilt
python rotate_cli.py ./data/imbio ./output-augmentations --rx 0 --ry 25 --rz 0 --visualize  # Severe lateral tilt
python rotate_cli.py ./data/imbio ./output-augmentations --rx 10 --ry 10 --rz 10 --visualize  # Combined rotation

echo "CT artifact simulation tests completed."
