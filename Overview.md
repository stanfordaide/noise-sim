# CT Artifact Simulation Overview

This document provides a comprehensive overview of the various CT artifacts that have been simulated in this project. Each artifact type is implemented to mimic realistic CT imaging challenges, with parameters chosen to represent both typical clinical scenarios and extreme test cases.

## 1. Parameter Summary Tables

### Slice Thickness Parameters
| Scenario | Value (mm) | Description |
|:---------|:-----------|:------------|
| Ultra-thin | 0.5 | Highest resolution, increased noise characteristics |
| Thin | 1.0 | High detail visualization, moderate noise |
| Standard | 2.5 | Typical clinical protocol, balanced noise/detail |
| Thick | 5.0 | Reduced noise, decreased detail resolution |
| Extra thick | 7.0 | Further detail reduction, minimal noise |
| Very thick | 10.0 | Maximum thickness tested, significant detail loss |

### Noise Parameters
| Type | Parameters | Clinical Impact |
|:-----|:-----------|:---------------|
| Low Electronic | Gaussian σ=30 | Minimal impact on diagnosis |
| Moderate Electronic | Gaussian σ=60 | Typical clinical noise levels |
| Heavy Electronic | Gaussian σ=100 | May impact fine detail visibility |
| Very High | Gaussian σ=150 | Significant diagnostic challenges |
| Typical Detector | S&P 2% | Common detector-related artifacts |
| Strong Detector | S&P 5% | Notable impact on image quality |
| Severe Detector | S&P 20% | Maximum tested artifact case |

### Motion Parameters
| Scenario | Movement (pixels) | Clinical Context |
|:---------|:-----------------|:-----------------|
| Mild breathing | 3px X, 0px Y | Normal respiratory motion |
| Normal movement | 7px X, 2px Y | Typical patient movement |
| Large movement | 20px X, 10px Y | Significant patient motion |
| Extreme movement | 30px X, 15px Y | Worst-case scenario |

### Beam Hardening Parameters
| Severity | Parameters | Effect |
|:---------|:-----------|:--------|
| Mild | 30%, 180 HU | Minimal dark bands |
| Moderate | 50%, 250 HU | Standard clinical appearance |
| Strong | 80%, 300 HU | Pronounced artifacts |
| Very strong | 90%, 150 HU | Severe dark bands |
| Extreme | 100%, 400 HU | Maximum artifact intensity |

### Ring Artifact Parameters
| Severity | Configuration | Impact |
|:---------|:--------------|:--------|
| Subtle | 2 rings, 30% intensity | Minor detector issues |
| Moderate | 4 rings, 50% intensity | Visible ring patterns |
| Multiple defects | 8 rings, 70% intensity | Multiple detector problems |
| Multiple strong | 8 rings, 80% intensity | Severe ring patterns |
| Maximum | 12 rings, 100% intensity | Worst-case scenario |

### Dose Reduction Parameters
| Level | Dose Percentage | Image Quality Impact |
|:------|:----------------|:-------------------|
| Moderate reduction | 70% | Minor quality degradation |
| Significant reduction | 50% | Noticeable quality loss |
| Very low | 20% | Significant degradation |
| Ultra-low | 10% | Maximum dose reduction |

### Patient Positioning Parameters
| Scenario | Rotation | Clinical Context |
|:---------|:---------|:----------------|
| Slight head tilt | 5° X-axis | Minor misalignment |
| Moderate lateral | 10° Y-axis | Common positioning variation |
| Slight rotation | 8° Z-axis | Typical rotation |
| Large head tilt | 15° X-axis | Significant misalignment |
| Severe lateral | 25° Y-axis | Extreme positioning |
| Combined rotation | 10° all axes | Complex misalignment |

## 2. Technical Implementation Details

### Motion Artifact Simulation
Motion artifacts are simulated using the ASTRA toolbox for realistic patient movement effects during CT acquisition.

Implementation characteristics:
- Scanner geometry simulation:
  - Parallel beam geometry (672 detector pixels)
  - 360 projection angles over 2π radians
  - Strip-based projection model
- Motion application during projection acquisition
- Filtered Back Projection (FBP) reconstruction
- Post-processing with Gaussian filtering

Reference: `motion_cli.py`

### Low-Dose Simulation
Implements reduced radiation dose effects through projection undersampling.

Technical approach:
- ASTRA toolbox integration:
  - Parallel beam geometry configuration
  - Strip-based projector model
  - Full 360° angular sampling
- Projection count reduction proportional to dose
- Noise characteristic preservation:
  - Original projection statistics maintained
  - Dose-dependent noise scaling
- FBP reconstruction with adaptive filtering

### Slice Thickness Variation
Implements variable slice thickness common in clinical protocols.

Key features:
- Cubic interpolation for resampling
- In-plane resolution preservation
- DICOM metadata updating
- Physical dimension maintenance

### Noise Variation
Simulates electronic and detector-based noise patterns.

Implementation details:
- Multiple noise model support
- Statistical property preservation
- Image space noise application
- Hounsfield Unit scale maintenance

### Beam Hardening Simulation
Models dense structure artifacts through physics-based simulation.

Components:
- Polychromatic X-ray behavior modeling
- Intensity-dependent attenuation
- Cupping and streaking artifact simulation
- Anatomical structure preservation

### Ring Artifact Generation
Simulates detector-based ring patterns.

Technical features:
- Concentric ring pattern generation
- Variable intensity implementation
- Detector response simulation
- Cross-slice consistency

### Patient Positioning Simulation
Implements various patient positioning scenarios.

Technical aspects:
- 3D rotation matrix transformation
- Dimension and scaling preservation
- Anatomical relationship maintenance
- Smooth rotation interpolation

Reference: `rotate_cli.py`

## 3. Output Structure and Visualization

### Directory Structure