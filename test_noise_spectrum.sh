#!/bin/bash

# Create output directory if it doesn't exist
mkdir -p ./spectrum-2/output-noise-artifacts

echo "Starting noise artifact spectrum-2 tests..."

# Gaussian Noise Tests
echo "Testing Gaussian Noise Spectrum-2..."

# Level 1 - Minimal noise (High-quality modern scanner)
echo "Testing Level 1 - Minimal Gaussian noise..."
python noise_cli.py ./data/imbiosmall ./spectrum-2/output-noise-artifacts/gaussian_level1 \
    --noise-type gaussian --mean 0 --std 15 --visualize

# Level 2 - Slight noise (Typical clinical scanner)
echo "Testing Level 2 - Slight Gaussian noise..."
python noise_cli.py ./data/imbiosmall ./spectrum-2/output-noise-artifacts/gaussian_level2 \
    --noise-type gaussian --mean 0 --std 30 --visualize

# Level 3 - Moderate noise (Older equipment or lower dose scan)
echo "Testing Level 3 - Moderate Gaussian noise..."
python noise_cli.py ./data/imbiosmall ./spectrum-2/output-noise-artifacts/gaussian_level3 \
    --noise-type gaussian --mean 0 --std 50 --visualize

# Level 4 - Significant noise (Ultra-low dose or equipment issues)
echo "Testing Level 4 - Significant Gaussian noise..."
python noise_cli.py ./data/imbiosmall ./spectrum-2/output-noise-artifacts/gaussian_level4 \
    --noise-type gaussian --mean 0 --std 75 --visualize

# Level 5 - Severe noise (Poor scan conditions)
echo "Testing Level 5 - Severe Gaussian noise..."
python noise_cli.py ./data/imbiosmall ./spectrum-2/output-noise-artifacts/gaussian_level5 \
    --noise-type gaussian --mean 0 --std 100 --visualize

# Salt and Pepper Noise Tests
echo "Testing Salt and Pepper Noise Spectrum-2..."

# Level 1 - Minimal impulse noise (Rare detector defects)
echo "Testing Level 1 - Minimal Salt & Pepper noise..."
python noise_cli.py ./data/imbiosmall ./spectrum-2/output-noise-artifacts/snp_level1 \
    --noise-type salt_and_pepper --prob 0.01 --visualize

# Level 2 - Slight impulse noise (Few detector defects)
echo "Testing Level 2 - Slight Salt & Pepper noise..."
python noise_cli.py ./data/imbiosmall ./spectrum-2/output-noise-artifacts/snp_level2 \
    --noise-type salt_and_pepper --prob 0.03 --visualize

# Level 3 - Moderate impulse noise (Multiple detector defects)
echo "Testing Level 3 - Moderate Salt & Pepper noise..."
python noise_cli.py ./data/imbiosmall ./spectrum-2/output-noise-artifacts/snp_level3 \
    --noise-type salt_and_pepper --prob 0.05 --visualize

# Level 4 - Significant impulse noise (Significant detector issues)
echo "Testing Level 4 - Significant Salt & Pepper noise..."
python noise_cli.py ./data/imbiosmall ./spectrum-2/output-noise-artifacts/snp_level4 \
    --noise-type salt_and_pepper --prob 0.08 --visualize

# Level 5 - Severe impulse noise (Major detector malfunction)
echo "Testing Level 5 - Severe Salt & Pepper noise..."
python noise_cli.py ./data/imbiosmall ./spectrum-2/output-noise-artifacts/snp_level5 \
    --noise-type salt_and_pepper --prob 0.12 --visualize

echo "Noise artifact spectrum-2 tests completed." 