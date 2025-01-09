# CT Artifact Simulation Overview

This document provides a comprehensive overview of the various CT artifacts that have been simulated in this project. Each artifact type is implemented to mimic realistic CT imaging challenges.

## 0. Overview

| Artifact Type | Description | Clinical Significance | Parameter Range |
|--------------|-------------|----------------------|-----------------|
| Motion | Patient movement during scan | Causes blurring and streaking | 3px - 30px movement |
| Low-Dose | Reduced radiation exposure | Increased noise, reduced detail | 10% - 70% of normal dose |
| Slice Thickness | Z-axis resolution variation | Affects detail visibility | 0.5mm - 10.0mm |
| Noise | Electronic and quantum noise | Reduces image quality | σ=30 - 150 (Gaussian), 2-20% (Salt & Pepper) |
| Beam Hardening | X-ray energy dependent artifacts | Dark bands near dense objects | 30% - 100% intensity |
| Ring Artifacts | Detector calibration issues | Concentric rings in image | 2-12 rings, 30-100% intensity |
| Patient Positioning | Patient orientation variations | Affects anatomical relationships | 5° - 25° rotations |

### Detailed Augmentation Parameters

| Category | Scenario | Parameters | Description |
|----------|----------|------------|-------------|
| **Slice Thickness** | Ultra-thin | 0.5mm | Highest resolution, increased noise |
| | Thin | 1.0mm | High detail visualization |
| | Standard | 2.5mm | Typical clinical protocol |
| | Thick | 5.0mm | Reduced noise, less detail |
| | Extra thick | 7.0mm | Further detail reduction |
| | Very thick | 10.0mm | Maximum thickness tested |
| **Noise** | Low | Gaussian σ=30 | Minimal electronic noise |
| | Moderate | Gaussian σ=60 | Typical clinical noise |
| | Heavy | Gaussian σ=100 | Challenging noise level |
| | Very high | Gaussian σ=150 | Extreme noise case |
| | Typical artifacts | S&P 2% | Common detector artifacts |
| | Strong artifacts | S&P 5% | Significant artifacts |
| | Severe artifacts | S&P 20% | Maximum artifact case |
| **Motion** | Mild breathing | 3px X, 0px Y | Normal respiratory motion |
| | Normal movement | 7px X, 2px Y | Typical patient movement |
| | Large movement | 20px X, 10px Y | Significant motion |
| | Extreme movement | 30px X, 15px Y | Worst-case scenario |
| **Beam Hardening** | Mild | 30%, 180 HU | Minimal dark bands |
| | Moderate | 50%, 250 HU | Typical clinical appearance |
| | Strong | 80%, 300 HU | Pronounced artifacts |
| | Very strong | 90%, 150 HU | Severe dark bands |
| | Extreme | 100%, 400 HU | Maximum artifact case |
| **Ring Artifacts** | Subtle | 2 rings, 30% | Minor detector issues |
| | Moderate | 4 rings, 50% | Visible ring patterns |
| | Multiple defects | 8 rings, 70% | Multiple detector problems |
| | Multiple strong | 8 rings, 80% | Severe ring patterns |
| | Maximum | 12 rings, 100% | Worst-case scenario |
| **Low-Dose** | Moderate reduction | 70% dose | Minor quality impact |
| | Significant reduction | 50% dose | Noticeable quality loss |
| | Very low | 20% dose | Significant degradation |
| | Ultra-low | 10% dose | Maximum dose reduction |
| **Patient Positioning** | Slight head tilt | 5° X-axis | Minor misalignment |
| | Moderate lateral | 10° Y-axis | Common positioning variation |
| | Slight rotation | 8° Z-axis | Typical rotation |
| | Large head tilt | 15° X-axis | Significant misalignment |
| | Severe lateral | 25° Y-axis | Extreme positioning |
| | Combined rotation | 10° all axes | Complex misalignment |

## 1. Motion Artifacts

Motion artifacts are simulated using the ASTRA toolbox to recreate realistic patient movement effects during CT acquisition.

### Parameters Tested:
- Mild breathing: 3px horizontal motion
- Normal movement: 7px horizontal, 2px vertical motion
- Large movement: 20px horizontal, 10px vertical motion
- Extreme movement: 30px horizontal, 15px vertical motion

### Technical Implementation:
The motion simulation uses a physics-based approach that:
- Simulates CT scanner geometry and projection-reconstruction process using ASTRA toolbox:
  - Parallel beam geometry with 672 detector pixels
  - 360 projection angles over 2π radians
  - Strip-based projection model for accurate ray tracing
- Applies motion during specific projection angles
- Uses Filtered Back Projection (FBP) for reconstruction
- Applies subtle Gaussian filtering for realism

Reference implementation: `motion_cli.py`

## 2. Low-Dose (Undersampling) Artifacts

Simulates the effects of reduced radiation dose through projection undersampling.

### Parameters Tested:
- Moderate dose reduction: 70% of normal dose (30% reduction)
- Significant dose reduction: 50% of normal dose
- Very low dose: 20% of normal dose
- Ultra-low dose: 10% of normal dose

### Technical Implementation:
- Uses ASTRA toolbox for realistic sinogram generation:
  - Parallel beam geometry configuration
  - Strip-based projector model for accurate physics simulation
  - Full 360° angular sampling with configurable projection count
- Reduces number of projections proportional to dose reduction
- Maintains proper noise characteristics through:
  - Preservation of original projection statistics
  - Appropriate scaling of noise based on dose reduction
- Implements FBP reconstruction with dose-specific filtering

## 3. Slice Thickness Variations

Simulates different slice thickness settings commonly used in clinical practice.

### Parameters Tested:
- Ultra-thin: 0.5mm
- Thin slices: 1.0mm
- Standard slices: 2.5mm
- Thick slices: 5.0mm
- Extra thick slices: 7.0mm
- Very thick slices: 10.0mm

### Technical Implementation:
- Uses cubic interpolation for high-quality resampling
- Preserves in-plane resolution
- Updates DICOM metadata appropriately
- Maintains proper physical dimensions

## 4. Noise Variations

Simulates different types of noise commonly encountered in CT imaging.

### Parameters Tested:
- Low electronic noise: Gaussian (σ=30)
- Moderate electronic noise: Gaussian (σ=60)
- Heavy electronic noise: Gaussian (σ=100)
- Very high noise: Gaussian (σ=150)
- Typical artifacts: Salt & pepper (2% probability)
- Strong artifacts: Salt & pepper (5% probability)
- Severe artifacts: Salt & pepper (20% probability)

### Technical Implementation:
- Implements multiple noise models
- Preserves underlying image statistics
- Applies noise in appropriate image space
- Maintains proper HU scale

## 5. Beam Hardening

Simulates beam hardening artifacts commonly seen around dense structures.

### Parameters Tested:
- Mild artifacts: 30% intensity, 180 HU threshold
- Moderate artifacts: 50% intensity, 250 HU threshold
- Strong artifacts: 80% intensity, 300 HU threshold
- Very strong artifacts: 90% intensity, 150 HU threshold
- Extreme artifacts: 100% intensity, 400 HU threshold

### Technical Implementation:
- Models polychromatic X-ray behavior
- Applies intensity-dependent attenuation
- Simulates cupping and streaking artifacts
- Preserves anatomical structures

## 6. Ring Artifacts

Simulates detector-related ring artifacts.

### Parameters Tested:
- Subtle detector issues: 2 rings, 30% intensity, 2px thickness
- Moderate artifacts: 4 rings, 50% intensity, 2px thickness
- Multiple defects: 8 rings, 70% intensity, 3px thickness
- Multiple strong: 8 rings, 80% intensity, 4px thickness
- Maximum artifacts: 12 rings, 100% intensity, 5px thickness

### Technical Implementation:
- Generates concentric ring patterns
- Applies intensity variations
- Simulates detector response characteristics
- Maintains artifact consistency across slices

## 7. Patient Positioning Variations (New Section)

Simulates various patient positioning scenarios during scanning.

### Parameters Tested:
- Slight head tilt: 5° around x-axis
- Moderate lateral tilt: 10° around y-axis
- Slight rotation: 8° around z-axis
- Large head tilt: 15° around x-axis
- Severe lateral tilt: 25° around y-axis
- Combined rotation: 10° around all axes

### Technical Implementation:
- Uses 3D rotation matrices for accurate transformation
- Preserves image dimensions and scaling
- Maintains proper anatomical relationships
- Implements interpolation for smooth rotations

Reference implementation: `rotate_cli.py`

## Output Structure

All simulated artifacts are saved with the following structure:

## Visualization Examples

### Motion Artifacts
![Motion Artifact Example](./output/motion/example_motion_5px.png)

### Low-Dose Artifacts
![Low Dose Example](./output/lowdose/example_30percent.png)

### Slice Thickness Comparison
![Slice Thickness Comparison](./output-augmentations/thickness_5.0mm/visualization/images_22620384/thickness_comparison.png)

### Noise Variations
![Noise Example](./output/noise/heavy_noise_example.png)

### Beam Hardening
![Beam Hardening Example](./output/beamhardening/strong_artifact.png)

### Ring Artifacts
![Ring Artifact Example](./output/rings/multiple_rings.png)

## References

Implementation details can be found in the following files:
- Motion artifacts: `motion_cli.py`
- Undersampling: `undersample_cli.py`
- Slice thickness: `slice_thickness_cli.py`
- Noise: `noise_cli.py`
- Beam hardening: `beam_hardening_cli.py`
- Ring artifacts: `ring_cli.py`