# CT Artifact Simulation Overview

This document provides a comprehensive overview of the various CT artifacts that have been simulated in this project. Each artifact type is implemented to mimic realistic CT imaging challenges.

## 1. Motion Artifacts

Motion artifacts are simulated using the ASTRA toolbox to recreate realistic patient movement effects during CT acquisition.

### Parameters Tested:
- Subtle movement: 5px horizontal motion
- Strong sudden movement: 15px motion at 45° angle
- Breathing-like motion: 10px motion at 90° angle

### Technical Implementation:
The motion simulation uses a physics-based approach that:
- Simulates CT scanner geometry and projection-reconstruction process
- Applies motion during specific projection angles
- Uses Filtered Back Projection (FBP) for reconstruction
- Applies subtle Gaussian filtering for realism

Reference implementation: `motion_cli.py`

## 2. Low-Dose (Undersampling) Artifacts

Simulates the effects of reduced radiation dose through projection undersampling.

### Parameters Tested:
- Mild dose reduction: 70% of normal dose
- Significant dose reduction: 30% of normal dose

### Technical Implementation:
- Uses ASTRA toolbox for realistic sinogram generation
- Reduces number of projections proportional to dose reduction
- Maintains proper noise characteristics
- Implements FBP reconstruction

## 3. Slice Thickness Variations

Simulates different slice thickness settings commonly used in clinical practice.

### Parameters Tested:
- Thin diagnostic: 1.0mm
- Standard clinical: 3.0mm
- Thick screening: 7.0mm

### Technical Implementation:
- Uses cubic interpolation for high-quality resampling
- Preserves in-plane resolution
- Updates DICOM metadata appropriately
- Maintains proper physical dimensions

## 4. Noise Variations

Simulates different types of noise commonly encountered in CT imaging.

### Parameters Tested:
- Moderate electronic noise: Gaussian (σ=50)
- Heavy electronic noise: Gaussian (σ=100)
- Sparse impulse noise: Salt & pepper (5% probability)

### Technical Implementation:
- Implements multiple noise models
- Preserves underlying image statistics
- Applies noise in appropriate image space
- Maintains proper HU scale

## 5. Beam Hardening

Simulates beam hardening artifacts commonly seen around dense structures.

### Parameters Tested:
- Moderate artifacts: 40% intensity, 200 HU threshold
- Strong artifacts: 80% intensity, 300 HU threshold

### Technical Implementation:
- Models polychromatic X-ray behavior
- Applies intensity-dependent attenuation
- Simulates cupping and streaking artifacts
- Preserves anatomical structures

## 6. Ring Artifacts

Simulates detector-related ring artifacts.

### Parameters Tested:
- Subtle detector issues: 3 rings, 40% intensity, 2px thickness
- Multiple detector defects: 8 rings, 70% intensity, 3px thickness

### Technical Implementation:
- Generates concentric ring patterns
- Applies intensity variations
- Simulates detector response characteristics
- Maintains artifact consistency across slices

## Output Structure

All simulated artifacts are saved with the following structure:

## Visualization Examples

### Motion Artifacts
![Motion Artifact Example](./output/motion/example_motion_5px.png)

### Low-Dose Artifacts
![Low Dose Example](./output/lowdose/example_30percent.png)

### Slice Thickness Comparison
![Slice Thickness Comparison](./output/thickness/thickness_comparison.png)

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