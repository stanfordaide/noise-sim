#!/bin/bash

echo "Starting all artifact spectrum tests..."

echo -e "\nRunning noise spectrum tests..."
./test_noise_spectrum.sh

echo -e "\nRunning ring artifact spectrum tests..."
./test_ring_spectrum.sh

echo -e "\nRunning rotation spectrum tests..."
./test_rotation_spectrum.sh

echo -e "\nRunning undersampling spectrum tests..."
./test_undersample_spectrum.sh


echo -e "\nRunning motion spectrum tests..."
./test_motion_spectrum.sh

# Run each spectrum test script
echo "Running beam hardening spectrum tests..."
./test_beam_hardening_spectrum.sh

echo -e "\nRunning slice thickness spectrum tests..."
./test_slice_thickness_spectrum.sh

echo -e "\nAll artifact spectrum tests completed successfully!" 