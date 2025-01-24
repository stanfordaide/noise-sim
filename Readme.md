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
   - [Slice Thickness](#36-slice-thickness)
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
Simulates reduced radiation dose effects through physics-based noise modeling and reconstruction.

**Parameters:**
- `--dose` (0.0-1.0): Simulates reduced radiation dose
  - 1.0 = Full dose (original quality)
  - 0.7 = 30% dose reduction (mild noise)
  - 0.5 = 50% dose reduction (moderate noise)
  - 0.2 = 80% dose reduction (significant noise)
  - 0.1 = 90% dose reduction (severe noise)

**Technical Implementation:**
- Noise modeling:
  - Poisson noise distribution simulation
  - Dose-dependent variance scaling
  - Mean-preserving noise addition
- Artifact reduction pipeline:
  - Bilateral filtering for edge preservation
  - Directional median filtering for streak reduction
  - Adaptive filter strength based on dose level
- Reconstruction considerations:
  - Modified filtered back projection (FBP)
  - Dose-dependent parameter optimization
  - Edge-preserving post-processing

**Clinical Impact:**
- Lower dose values increase quantum noise
- Affects contrast-to-noise ratio
- May impact fine detail visibility
- Realistic simulation of dose reduction effects

### 3.2 Motion Artifacts
Simulates realistic patient movement artifacts during CT acquisition using ASTRA toolbox physics-based simulation.

**Parameters:**
- `--amplitude_x` (pixels): Magnitude of horizontal motion
  - Controls severity of motion artifacts in x direction
  - Typical clinical range: 2-8 pixels
  - Stress testing range: 10-30 pixels
- `--amplitude_y` (pixels): Magnitude of vertical motion
  - Controls severity of motion artifacts in y direction
  - Typical clinical range: 0-3 pixels
  - Stress testing range: 4-15 pixels

**Technical Implementation:**
- Physics-based simulation using ASTRA toolbox:
  - Parallel beam geometry with 672 detector pixels
  - 360 projection angles over 2π radians
  - Line-based projection model
- Motion simulation characteristics:
  - Random displacement vector generation
  - Elastic deformation for realistic movement
  - Gaussian filtering (σ=0.5) for smoothing
- Maintains 3D consistency across slices
- Intensity of artifacts proportional to:
  - Motion amplitude
  - Local tissue contrast
  - Movement direction

**Clinical Impact Levels:**
1. Minimal (2px X, 0px Y): Slight breathing artifacts
2. Mild (4px X, 1px Y): Normal patient movement
3. Moderate (6px X, 2px Y): Noticeable motion
4. Marked (8px X, 3px Y): Significant movement
5. Severe (10px+ X, 4px+ Y): Major motion artifacts

### 3.3 Noise Variations
Simulates various types of noise artifacts commonly encountered in CT imaging.

**Parameters:**
- `--noise-type`: Type of noise to apply
  - `gaussian`: Random Gaussian noise
  - `salt_and_pepper`: Impulse noise simulating detector defects
- For Gaussian noise:
  - `--mean` (HU): Center of noise distribution (default: 0)
  - `--std` (HU): Standard deviation of noise (default: 50)
- For Salt & Pepper noise:
  - `--prob`: Probability of noise occurrence (0.0-1.0)
    - 0.05: Moderate detector defects
    - 0.08: Significant detector issues
    - 0.12: Major detector malfunction

**Technical Implementation:**
- Gaussian noise:
  - Normal distribution sampling
  - Independent noise per pixel
  - Preserves image statistics
- Salt & Pepper noise:
  - Random binary mask generation
  - Separate salt (max) and pepper (min) probabilities
  - Simulates dead/hot detector elements

### 3.4 Ring Artifacts
Simulates detector-based ring artifacts with realistic characteristics.

**Parameters:**
- `--num-defects`: Number of detector defects to simulate
- `--intensity`: Relative intensity of defects (typically 1.12-1.15)
- `--width`: Width of defect response in pixels
- `--radius-min`, `--radius-max`: Ring radius range as fraction of image
- `--angle-range`: Angular range of artifact visibility (degrees)

**Technical Implementation:**
- Detector response modeling:
  - Clustered defect patterns (1-2 elements)
  - Limited to 20% of detector width
  - Dead (0.4×) and hot (1.3×) detector simulation
- Spatial characteristics:
  - Narrow defect width (1-3 pixels)
  - Center-weighted positioning
  - Angular consistency preservation

### 3.5 Beam Hardening
Simulates polychromatic X-ray beam artifacts.

**Parameters:**
- `--intensity` (0.0-1.0): Strength of beam hardening effect
  - 0.15: Minimal artifacts
  - 0.3: Mild artifacts
  - 0.45: Moderate artifacts
  - 0.6: Marked artifacts
- `--threshold` (HU): Density threshold for artifact generation
  - 300: Minimal effect
  - 262: Mild effect
  - 225: Moderate effect
  - 187: Marked effect

**Technical Implementation:**
- Signal handling for safe interruption
- Progress tracking with tqdm
- Visualization options for quality control
- DICOM metadata preservation

### 3.6 Slice Thickness
Simulates variations in slice thickness reconstruction.

**Parameters:**
- `--thickness` (mm): Target slice thickness
  - 2.0: Minimal change
  - 3.5: Mild change
  - 5.0: Moderate change
  - 7.5: Marked change
  - 10.0: Extreme change

**Technical Implementation:**
- Maintains DICOM metadata
- Visualization comparison generation
- Progress tracking
- Interrupt-safe processing

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


