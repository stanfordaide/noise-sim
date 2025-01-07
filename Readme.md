### 2.1 Conda Environment
Create and activate conda environment

```bash
conda create -n noise-simulation python=3.10
conda activate noise-simulation
conda install pip
pip install -e .
```

### 2.2 Usage Examples

#### Undersampling Tool
Simulates low-dose CT scans by reducing the number of projections.

```bash
# Basic usage with 90% dose (minimal noise)
python undersample_cli.py /path/to/dicom/folder ./output

# Higher noise simulation (50% dose)
python undersample_cli.py /path/to/dicom/folder ./output --dose 0.5

# Disable visualization generation
python undersample_cli.py /path/to/dicom/folder ./output --dose 0.7 --no-visualize

# Change number of sample visualizations
python undersample_cli.py /path/to/dicom/folder ./output --num-samples 10
```

#### Rotation Tool
Applies 3D rotation to DICOM image series.

```bash
# Basic usage (no rotation - useful for testing)
python rotate_cli.py /path/to/dicom/folder ./output

# Rotate 45 degrees around X axis
python rotate_cli.py /path/to/dicom/folder ./output --rx 45

# Complex rotation around multiple axes
python rotate_cli.py /path/to/dicom/folder ./output --rx 30 --ry 45 --rz 15

# Disable visualization generation
python rotate_cli.py /path/to/dicom/folder ./output --rx 45 --no-visualize
```

### 2.3 Common Arguments
Both tools support these arguments:
- `input_dir`: Directory containing DICOM files
- `output_dir`: Directory where processed files will be saved
- `--visualize`: Generate visualization images (default: True)
- `--no-visualize`: Disable visualization generation
- `--num-samples`: Number of random samples to visualize (default: 5)

### 2.4 Tool-Specific Arguments

#### Undersampling
- `--dose`: Dose level between 0 and 1 (default: 0.9)
  - 1.0 = Original quality
  - 0.5 = Half dose
  - 0.1 = Very noisy

#### Rotation
- `--rx`: Rotation angle around X axis in degrees (default: 0)
- `--ry`: Rotation angle around Y axis in degrees (default: 0)
- `--rz`: Rotation angle around Z axis in degrees (default: 0)

### 2.5 Output Directory Structure
```
output_dir/
├── dose_90/                     # For undersampling
│   ├── visualization/
│   │   └── comparison_*.png
│   └── processed_files/
└── rotation_rx45_ry0_rz0/      # For rotation
    ├── visualization/
    │   └── comparison_*.png
    └── processed_files/
```