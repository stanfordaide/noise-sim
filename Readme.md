# CT Noise Simulation Tools

A collection of tools for simulating various types of noise and artifacts in CT scans. Designed for testing the robustness of medical image analysis algorithms.

## Table of Contents
1. [Installation](#1-installation)
2. [Usage](#2-usage)
3. [Supported Augmentations](#3-supported-augmentations)
4. [Tool Reference](#4-tool-reference)

## 1. Installation

### 1.1 Conda Environment
Create and activate conda environment:

```bash
conda create -n noise-simulation python=3.10
conda activate noise-simulation
conda install pip
pip install -e .
```

## 2. Usage

Each tool can be run from the command line with various parameters. All tools support both single DICOM files and directories containing DICOM series.

### 2.1 Basic Usage Pattern
```bash
python <tool_name>.py /path/to/input /path/to/output [parameters]
```

### 2.2 Common Arguments
All tools support these base arguments:
- `input_dir`: Directory containing DICOM files
- `output_dir`: Directory where processed files will be saved
- `--visualize`: Generate visualization images (default: True)
- `--no-visualize`: Disable visualization generation

## 3. Supported Augmentations

### 3.1 Undersampling (Low-Dose Simulation)
Simulates low-dose CT by reducing the number of projections in sinogram space.

**Parameters:**
- `--dose` (0.0-1.0): Simulates reduced radiation dose
  - 1.0 = Original quality (no noise)
  - 0.5 = Half dose (moderate noise)
  - 0.1 = 10% dose (significant noise)

**Impact:**
- Lower dose values increase quantum noise
- Affects image contrast and detail visibility
- Realistic simulation of low-dose acquisition

### 3.2 Motion Artifacts
Simulates realistic patient movement artifacts during CT acquisition, including blurring and streaking patterns based on actual CT physics.

**Parameters:**
- `--amplitude_x` (pixels): Magnitude of horizontal motion
  - Controls severity of motion artifacts in x direction
  - Larger values create more pronounced blurring and streaking
  - Typical range: 5-20 pixels
- `--amplitude_y` (pixels): Magnitude of vertical motion
  - Controls severity of motion artifacts in y direction
  - Larger values create more pronounced blurring and streaking
  - Typical range: 5-20 pixels
- `--visualize`: Generate visualization images (default: True)
- `--no-visualize`: Disable visualization generation

**Impact:**
- Creates two main types of artifacts:
  1. Blurring: General loss of sharpness
  2. Streaking: Long-range streaks from high-contrast edges
- Artifacts vary with:
  - Local image contrast
  - Motion amplitude and direction
- More pronounced near:
  - Bone-tissue interfaces
  - Air-tissue boundaries
  - Other high-contrast edges

**Technical Details:**
- Physics-based simulation using ASTRA toolbox considering:
  - CT scanner geometry
  - Projection-reconstruction process
  - Filtered back projection (FBP) reconstruction
- 3D consistent across slices
- Intensity of streaks proportional to edge contrast
- Gaussian filtering applied for realistic smoothing

### Usage Examples:
```bash
# Simulate subtle motion (e.g., slight patient movement)
python motion_cli.py /path/to/input ./output \
    --amplitude_x 5 \
    --amplitude_y 0

# Simulate strong horizontal motion
python motion_cli.py /path/to/input ./output \
    --amplitude_x 15 \
    --amplitude_y 0

# Simulate vertical motion
python motion_cli.py /path/to/input ./output \
    --amplitude_x 0 \
    --amplitude_y 10
```

### 3.3 Beam Hardening
Simulates beam hardening artifacts common in CT imaging.

**Parameters:**
- `--intensity` (0.0-1.0): Strength of beam hardening effect (default: 0.5)
  - Controls the prominence of dark bands and cupping artifacts
- `--threshold` (HU): Threshold for high-density objects (default: 200)
  - Determines which structures cause streaking
  - Typical range: 150-300 HU

**Impact:**
- Creates dark bands between dense objects
- Produces cupping artifacts
- More pronounced near metal/bone interfaces

### 3.4 Gaussian Noise
Adds random Gaussian noise to simulate various acquisition artifacts.

**Parameters:**
- `--mean` (HU): Center of noise distribution (default: 0)
- `--std` (HU): Standard deviation of noise (default: 50)
  - Controls noise intensity
  - Typical range: 20-100 HU

**Impact:**
- Adds random variation to pixel values
- Simulates electronic noise
- Affects image contrast and detail visibility

### 3.5 Ring Artifacts
Simulates ring artifacts commonly caused by miscalibrated or defective detector elements in CT scanners.

**Parameters:**
- `--num-rings` (integer): Number of rings to generate (default: 3)
  - Controls density of artifacts
  - Typical range: 2-10 rings
- `--intensity` (0.0-1.0): Strength of ring artifacts (default: 0.5)
  - Controls visibility of rings
  - Higher values create more pronounced artifacts
- `--thickness` (pixels): Width of rings (default: 2)
  - Controls ring sharpness
  - Larger values create broader rings
- `--min-radius` (0.0-1.0): Minimum ring radius as fraction of image size (default: 0.2)
- `--max-radius` (0.0-1.0): Maximum ring radius as fraction of image size (default: 0.8)
  - Together control the distribution of ring sizes

**Impact:**
- Creates concentric circular artifacts
- Varies in intensity along the ring circumference
- More pronounced in areas of uniform density
- Consistent across slices in 3D

### 3.6 Slice Thickness Modification
Simulates different slice thickness acquisitions through 3D resampling.

**Parameters:**
- `--thickness` (mm): Target slice thickness
  - Must be specified
  - Typical CT ranges:
    - Thin slices: 0.5-1.5mm
    - Standard slices: 2-3mm
    - Thick slices: 5-10mm

**Impact:**
- Affects z-axis resolution
- Changes noise characteristics:
  - Thicker slices reduce noise but decrease detail
  - Thinner slices increase noise but improve detail
- Modifies partial volume effects
- Updates DICOM metadata to reflect new spacing

**Technical Details:**
- Uses cubic interpolation for high quality resampling
- Preserves in-plane (x-y) resolution
- Maintains proper physical dimensions
- Updates relevant DICOM tags:
  - SliceThickness
  - SpacingBetweenSlices
  - ImagePositionPatient

## 4. Tool Reference

### 4.1 Undersampling Tool
```bash
# Basic usage (90% dose)
python undersample_cli.py /path/to/input ./output

# High noise (50% dose)
python undersample_cli.py /path/to/input ./output --dose 0.5

# Disable visualization
python undersample_cli.py /path/to/input ./output --dose 0.7 --no-visualize
```

### 4.2 Motion Artifact Tool
```bash
# Mild motion
python motion_cli.py /path/to/input ./output --amplitude_x 5 --amplitude_y 0

# Strong motion with high frequency
python motion_cli.py /path/to/input ./output --amplitude_x 15 --amplitude_y 0 --frequency 2.0
```

### 4.3 Beam Hardening Tool
```bash
# Moderate beam hardening
python beam_hardening_cli.py /path/to/input ./output --intensity 0.5

# Strong artifacts with lower threshold
python beam_hardening_cli.py /path/to/input ./output --intensity 0.8 --threshold 150
```

### 4.4 Noise Tool
```bash
# Add Gaussian noise
python noise_cli.py /path/to/input ./output --noise-type gaussian --std 75

# Add salt and pepper noise
python noise_cli.py /path/to/input ./output --noise-type salt_and_pepper --prob 0.05
```

### 4.5 Ring Artifact Tool
```bash
# Basic ring artifacts
python ring_cli.py /path/to/input ./output

# Multiple pronounced rings
python ring_cli.py /path/to/input ./output --num-rings 5 --intensity 0.8 --thickness 3

# Control ring distribution
python ring_cli.py /path/to/input ./output --min-radius 0.3 --max-radius 0.7
```

### 4.6 Slice Thickness Tool
```bash
# Increase slice thickness to 5mm
python slice_thickness_cli.py /path/to/input ./output --thickness 5.0

# Create thin slices (1mm)
python slice_thickness_cli.py /path/to/input ./output --thickness 1.0

# Thick slices without visualization
python slice_thickness_cli.py /path/to/input ./output --thickness 7.5 --no-visualize
```

## 5. Output Structure
```
output_dir/
├── transform_name/              # Based on tool and parameters
│   ├── visualization/          # If enabled
│   │   └── comparison_*.png
│   └── processed_files/
│       └── [preserved input structure]
```

## 6. Notes
- All tools preserve DICOM metadata
- Visualizations include side-by-side comparisons
- Processing is done in 3D when appropriate
- Tools can be interrupted safely with Ctrl+C