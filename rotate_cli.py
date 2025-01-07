import os
import argparse
import pydicom
import numpy as np
import nibabel as nib
from scipy.interpolate import interpn
import signal
import sys
import threading
import matplotlib.pyplot as plt
from tqdm import tqdm
from matplotlib.animation import FuncAnimation, PillowWriter

STOP_PROCESSING = threading.Event()

def signal_handler(signum, frame):
    print("\nInterrupt received. Cleaning up...")
    STOP_PROCESSING.set()

def apply_affine(tx, ty, tz, rx, ry, rz, image3d, resolution=(1, 1, 1),
                method='linear', fill_value=0):
    # Create the rotation matrices
    rotx = np.array([[1, 0, 0],
                     [0, np.cos(rx), -np.sin(rx)],
                     [0, np.sin(rx), np.cos(rx)]])

    roty = np.array([[np.cos(ry), 0, np.sin(ry)],
                     [0, 1, 0],
                     [-np.sin(ry), 0, np.cos(ry)]])

    rotz = np.array([[np.cos(rz), -np.sin(rz), 0],
                     [np.sin(rz), np.cos(rz), 0],
                     [0, 0, 1]])

    rotation_matrix = np.dot(np.dot(rotx, roty), rotz)

    # Create the affine transformation matrix
    affine = np.array([
        [rotation_matrix[0, 0], rotation_matrix[0, 1], rotation_matrix[0, 2], tx],
        [rotation_matrix[1, 0], rotation_matrix[1, 1], rotation_matrix[1, 2], ty],
        [rotation_matrix[2, 0], rotation_matrix[2, 1], rotation_matrix[2, 2], tz],
        [0, 0, 0, 1]
    ])

    # Create grids of the original image
    center = np.array(image3d.shape) / 2.0
    grids = [np.arange(image3d.shape[dim]) - center[dim] for dim in range(3)]
    for dim in range(3):
        grids[dim] *= resolution[dim]

    # Create meshgrid and coordinates
    x, y, z = np.meshgrid(grids[0], grids[1], grids[2], indexing='ij')
    coords = np.array([x.flatten(), y.flatten(), z.flatten(), 
                      np.ones_like(x.flatten())]).T

    # Apply transformation and interpolate
    transformed_coords = np.dot(affine, coords.T).T
    image3d2 = interpn(grids, image3d, transformed_coords[:, :3],
                      method=method, bounds_error=False, fill_value=fill_value)
    
    return image3d2.reshape(image3d.shape)

def dicoms_to_volume(dicom_files):
    """Convert a list of DICOM files to a 3D volume."""
    # Sort DICOM files by ImagePositionPatient
    sorted_dicoms = []
    for dcm_path in dicom_files:
        dcm = pydicom.dcmread(dcm_path)
        pos = tuple(map(float, dcm.ImagePositionPatient))
        sorted_dicoms.append((pos[2], dcm_path))  # Sort by z-position
    sorted_dicoms.sort()
    
    # Read first DICOM to get dimensions
    first_dcm = pydicom.dcmread(sorted_dicoms[0][1])
    volume_shape = (len(sorted_dicoms), *first_dcm.pixel_array.shape)
    volume = np.zeros(volume_shape)
    
    # Fill volume
    for i, (_, dcm_path) in enumerate(sorted_dicoms):
        dcm = pydicom.dcmread(dcm_path)
        volume[i] = dcm.pixel_array * dcm.RescaleSlope + dcm.RescaleIntercept
    
    return volume, sorted_dicoms

def volume_to_dicoms(volume, template_dicoms, output_dir):
    """Convert a 3D volume back to DICOM files using template DICOM metadata."""
    os.makedirs(output_dir, exist_ok=True)
    
    for i, (_, template_path) in enumerate(template_dicoms):
        # Read template DICOM
        template = pydicom.dcmread(template_path)
        
        # Create new DICOM dataset
        new_dcm = pydicom.Dataset()
        new_dcm = template
        
        # Convert back to original scale
        pixel_array = (volume[i] - template.RescaleIntercept) / template.RescaleSlope
        new_dcm.PixelData = pixel_array.astype(np.int16).tobytes()
        
        # Save new DICOM
        output_path = os.path.join(output_dir, os.path.basename(template_path))
        new_dcm.save_as(output_path)

def visualize_volume(volume, rotated_volume, output_dir, n_slices=24):
    """Create static visualization of volume slices, showing original and rotated side by side."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a figure with multiple slice pairs
    fig, axes = plt.subplots(8, 6, figsize=(30, 40))
    slice_indices = np.linspace(0, volume.shape[0]-1, n_slices, dtype=int)

    for i in range(n_slices):
        row = i // 3
        col = (i % 3) * 2  # Multiply by 2 to leave space for rotated image
        
        # Original slice
        axes[row, col].imshow(volume[slice_indices[i]], cmap='gray')
        axes[row, col].set_title(f'Original Slice {slice_indices[i]}')
        axes[row, col].axis('off')
        
        # Rotated slice
        axes[row, col+1].imshow(rotated_volume[slice_indices[i]], cmap='gray')
        axes[row, col+1].set_title(f'Rotated Slice {slice_indices[i]}')
        axes[row, col+1].axis('off')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'slices_comparison.png'))
    plt.close()

    # Save individual comparison slices
    for idx in slice_indices:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
        ax1.imshow(volume[idx], cmap='gray')
        ax1.set_title(f'Original Slice {idx}')
        ax1.axis('off')
        
        ax2.imshow(rotated_volume[idx], cmap='gray')
        ax2.set_title(f'Rotated Slice {idx}')
        ax2.axis('off')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'slice_{idx:03d}_comparison.png'))
        plt.close()

def process_dicom_series(input_dir, output_dir, angles, visualization_dir=None, rel_path=''):
    """Process a series of DICOM files with rotation."""
    # Collect DICOM files
    dicom_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            try:
                filepath = os.path.join(root, file)
                pydicom.dcmread(filepath, stop_before_pixels=True)
                dicom_files.append(filepath)
            except:
                continue
    
    if not dicom_files:
        print(f"No DICOM files found in {input_dir}")
        return False
    
    # Convert to volume
    print("Converting DICOM series to volume...")
    volume, sorted_dicoms = dicoms_to_volume(dicom_files)
    
    # Apply rotation
    print("Applying rotation...")
    rx, ry, rz = [np.radians(angle) for angle in angles]
    rotated_volume = apply_affine(0, 0, 0, rx, ry, rz, volume)
    
    # Create visualizations if requested
    if visualization_dir:
        print("Generating visualizations...")
        vis_subdir = os.path.join(visualization_dir, rel_path) if rel_path else visualization_dir
        os.makedirs(vis_subdir, exist_ok=True)
        visualize_volume(volume, rotated_volume, vis_subdir)
    
    # Convert back to DICOM
    print("Converting back to DICOM...")
    volume_to_dicoms(rotated_volume, sorted_dicoms, output_dir)
    
    return True

def main():
    STOP_PROCESSING.clear()
    signal.signal(signal.SIGINT, signal_handler)
    
    parser = argparse.ArgumentParser(description='Rotate 3D DICOM images')
    parser.add_argument('input_dir', help='Input directory containing DICOM studies')
    parser.add_argument('output_dir', help='Output directory for rotated DICOM files')
    parser.add_argument('--rx', type=float, default=0, help='Rotation angle around X axis (degrees)')
    parser.add_argument('--ry', type=float, default=0, help='Rotation angle around Y axis (degrees)')
    parser.add_argument('--rz', type=float, default=0, help='Rotation angle around Z axis (degrees)')
    parser.add_argument('--visualize', action='store_true', default=True,
                       help='Generate visualization images (default: True)')
    parser.add_argument('--no-visualize', dest='visualize', action='store_false',
                       help='Disable visualization generation')
    parser.add_argument('--num-samples', type=int, default=5,
                       help='Number of random samples to visualize (default: 5)')
    
    args = parser.parse_args()
    angles = (args.rx, args.ry, args.rz)
    
    # Create output directory structure
    transform_name = f"rotation_rx{args.rx}_ry{args.ry}_rz{args.rz}"
    output_base = os.path.join(args.output_dir, transform_name)
    processed_dir = os.path.join(output_base, "processed_files")
    visualization_dir = os.path.join(output_base, "visualization")
    os.makedirs(processed_dir, exist_ok=True)
    if args.visualize:
        os.makedirs(visualization_dir, exist_ok=True)

    try:
        # Process each subdirectory maintaining the structure
        for root, dirs, files in os.walk(args.input_dir):
            if STOP_PROCESSING.is_set():
                break
            
            # Skip if no DICOM files in directory
            has_dicoms = any(True for f in files if try_dicom_read(os.path.join(root, f)))
            if not has_dicoms:
                continue
            
            # Create corresponding output directory within processed_files
            rel_path = os.path.relpath(root, args.input_dir)
            output_subdir = os.path.join(processed_dir, rel_path)
            
            print(f"\nProcessing directory: {root}")
            success = process_dicom_series(
                root, 
                output_subdir, 
                angles, 
                visualization_dir=visualization_dir if args.visualize else None,
                rel_path=rel_path
            )
            if success:
                print(f"Saved to: {output_subdir}")
                
    except KeyboardInterrupt:
        STOP_PROCESSING.set()
        print("\nInterrupted by user. Cleaning up...")
        sys.exit(0)

def try_dicom_read(filepath):
    """Try to read a file as DICOM."""
    try:
        pydicom.dcmread(filepath, stop_before_pixels=True)
        return True
    except:
        return False

if __name__ == "__main__":
    main()
