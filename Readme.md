# CT Artifact Simulation Tools

A collection of tools for simulating various types of noise and artifacts in CT scans. Designed for testing the robustness of medical image analysis algorithms.

## Table of Contents

1. [Installation](#1-installation)
   - [Prerequisites](#prerequisites)
   - [Conda Environment Setup](#conda-environment-setup)
2. [Usage](#2-usage)
   - [Basic Usage Pattern](#basic-usage-pattern)
   - [Common Arguments](#common-arguments)
3. [Supported Artifacts](#3-supported-artifacts)
   - [Low-Dose Simulation](#31-low-dose-simulation)
   - [Motion Artifacts](#32-motion-artifacts)
   - [Noise Variations](#33-noise-variations)
   - [Ring Artifacts](#34-ring-artifacts)
   - [Beam Hardening](#35-beam-hardening)
4. [Tool Reference](#4-tool-reference)
   - [Basic Usage Examples](#basic-usage-examples)
   - [Batch Processing](#batch-processing)
5. [Output Structure](#5-output-structure)
6. [Notes](#6-notes)
   - [Implementation Details](#implementation-details)
   - [Performance Considerations](#performance-considerations)
   - [Quality Control](#quality-control)
7. [Contributing](#contributing)
8. [Acknowledgments](#acknowledgments)

## 1. Installation

### Prerequisites
- Python 3.10+
- ASTRA Toolbox
- CUDA-capable GPU (recommended)

### Conda Environment Setup

```
conda create -n noise-sim python=3.10
conda activate noise-sim
conda install pip
pip install -e .
```


## 2. Usage

Each tool can be run independently from the command line. All tools support processing both individual DICOM files and directories containing DICOM series.

### Basic Usage Pattern

```bash
python <tool_name>.py /path/to/input /path/to/output [parameters]
```

### Common Arguments
All tools support these base arguments:
- `input_dir`: Directory containing DICOM files
- `output_dir`: Directory for processed files
- `--visualize`: Generate comparison visualizations (default: True)
- `--no-visualize`: Disable visualization generation

## 3. Supported Artifacts

### 3.1 Low-Dose Simulation
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

### 3.3 Noise Variations
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

### 3.4 Ring Artifacts
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

### 3.5 Beam Hardening
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

## 4. Tool Reference

### Basic Usage Examples
```bash
# Motion artifacts
python motion_cli.py /path/to/input ./output --amplitude_x 5 --amplitude_y 0

# Noise addition
python noise_cli.py /path/to/input ./output --noise-type gaussian --std 50

# Ring artifacts
python ring_cli.py /path/to/input ./output --num-rings 3 --intensity 0.4 --thickness 2

# Beam hardening
python beam_hardening_cli.py /path/to/input ./output --intensity 0.4 --threshold 200
```

### Batch Processing
```bash
# Example batch script
./run_augs.sh
```

## 5. Output Structure
```
output/
├── transform_name/           # Based on artifact type and parameters
│   ├── processed_files/     # Maintains input directory structure
│   │   └── [DICOM files]
│   └── visualization/       # If enabled
│       └── [comparison images]
```

## 6. Notes

### Implementation Details
- All tools preserve DICOM metadata
- Interrupt processing safely with Ctrl+C
- Visualization includes before/after comparisons
- 3D consistency maintained where applicable

### Performance Considerations
- GPU acceleration available for supported operations
- Batch processing recommended for large datasets
- Progress bars indicate processing status

### Quality Control
- Visualization options for artifact verification
- Maintains original DICOM tags for tracking
- Directory structure preserved for easy comparison

## Contributing
Contributions are welcome! Please see our contributing guidelines for more details.

## Acknowledgments
- ASTRA Toolbox for CT simulation capabilities
- PyDicom for DICOM file handling


