import os
import argparse
import pydicom
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import zoom
import threading
import signal
import sys
from tqdm import tqdm

STOP_PROCESSING = threading.Event()

def signal_handler(signum, frame):
    print("\nInterrupt received. Cleaning up...")
    STOP_PROCESSING.set()

def resample_volume(volume, original_spacing, target_spacing):
    """
    Resample a 3D volume to a new slice thickness.
    
    Args:
        volume: 3D numpy array
        original_spacing: Original voxel spacing (z, y, x) in mm
        target_spacing: Desired voxel spacing (z, y, x) in mm
    """
    # Calculate resize factors
    resize_factors = np.array(original_spacing) / np.array(target_spacing)
    
    # Perform interpolation
    # order=3 for cubic interpolation, which provides good quality for medical images
    resampled = zoom(volume, resize_factors, order=3, mode='nearest')
    
    return resampled

def get_slice_positions(dicoms):
    """Extract slice positions and spacing from DICOM files."""
    positions = []
    for dcm in dicoms:
        pos = float(dcm.ImagePositionPatient[2])
        positions.append(pos)
    
    positions = sorted(positions)
    spacings = np.diff(positions)
    avg_spacing = np.mean(spacings)
    
    return positions, avg_spacing

def process_dicom_series(input_dir, output_dir, target_thickness, visualization_dir=None):
    """Process a series of DICOM files to modify slice thickness."""
    # Collect and sort DICOM files
    dicom_files = []
    for filename in os.listdir(input_dir):
        filepath = os.path.join(input_dir, filename)
        try:
            dcm = pydicom.dcmread(filepath)
            dicom_files.append(dcm)
        except:
            continue
    
    if not dicom_files:
        print(f"No DICOM files found in {input_dir}")
        return False
    
    # Sort DICOMs by slice position
    dicom_files.sort(key=lambda x: float(x.ImagePositionPatient[2]))
    
    # Get original spacing
    positions, original_z_spacing = get_slice_positions(dicom_files)
    pixel_spacing = dicom_files[0].PixelSpacing
    original_spacing = (original_z_spacing, float(pixel_spacing[0]), float(pixel_spacing[1]))
    
    # Define target spacing (only changing z-spacing)
    target_spacing = (target_thickness, original_spacing[1], original_spacing[2])
    
    # Create 3D volume
    print("Converting DICOM series to volume...")
    volume_shape = (len(dicom_files), *dicom_files[0].pixel_array.shape)
    volume = np.zeros(volume_shape)
    
    for i, dcm in enumerate(dicom_files):
        volume[i] = dcm.pixel_array * dcm.RescaleSlope + dcm.RescaleIntercept
    
    # Resample volume
    print("Resampling volume...")
    resampled = resample_volume(volume, original_spacing, target_spacing)
    
    # Create visualizations if requested
    if visualization_dir:
        print("Generating visualizations...")
        os.makedirs(visualization_dir, exist_ok=True)
        visualize_thickness_effect(volume, resampled, original_spacing, target_spacing, visualization_dir)
    
    # Save processed DICOM files
    print("Saving DICOM files...")
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate new z positions
    new_positions = np.linspace(positions[0], positions[-1], resampled.shape[0])
    
    template_dcm = dicom_files[0]
    for i in range(resampled.shape[0]):
        # Create new DICOM using template
        new_dcm = template_dcm.copy()
        
        # Update slice position
        new_pos = list(new_dcm.ImagePositionPatient)
        new_pos[2] = float(new_positions[i])
        new_dcm.ImagePositionPatient = new_pos
        
        # Update slice thickness and spacing
        new_dcm.SliceThickness = str(target_thickness)
        new_dcm.SpacingBetweenSlices = str(target_thickness)
        
        # Update image data
        pixel_array = (resampled[i] - new_dcm.RescaleIntercept) / new_dcm.RescaleSlope
        pixel_array = np.clip(pixel_array, np.min(template_dcm.pixel_array), 
                            np.max(template_dcm.pixel_array))
        new_dcm.PixelData = pixel_array.astype(template_dcm.pixel_array.dtype).tobytes()
        
        # Update series description
        new_dcm.SeriesDescription = f"{template_dcm.get('SeriesDescription', 'Unknown')} - {target_thickness}mm"
        
        # Save new DICOM
        output_path = os.path.join(output_dir, f"slice_{i:04d}.dcm")
        new_dcm.save_as(output_path)
    
    return True

def visualize_thickness_effect(original, resampled, original_spacing, target_spacing, output_dir):
    """Create visualizations showing the effect of slice thickness changes."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Create sagittal and coronal views
    fig, axes = plt.subplots(2, 2, figsize=(15, 15))
    
    # Sagittal view
    mid_x = original.shape[2] // 2
    axes[0, 0].imshow(original[:, :, mid_x], cmap='gray', aspect=original_spacing[0]/original_spacing[1])
    axes[0, 0].set_title(f'Original Sagittal (thickness: {original_spacing[0]:.2f}mm)')
    axes[0, 0].axis('off')
    
    axes[0, 1].imshow(resampled[:, :, mid_x], cmap='gray', aspect=target_spacing[0]/target_spacing[1])
    axes[0, 1].set_title(f'Resampled Sagittal (thickness: {target_spacing[0]:.2f}mm)')
    axes[0, 1].axis('off')
    
    # Coronal view
    mid_y = original.shape[1] // 2
    axes[1, 0].imshow(original[:, mid_y, :], cmap='gray', aspect=original_spacing[0]/original_spacing[2])
    axes[1, 0].set_title(f'Original Coronal (thickness: {original_spacing[0]:.2f}mm)')
    axes[1, 0].axis('off')
    
    axes[1, 1].imshow(resampled[:, mid_y, :], cmap='gray', aspect=target_spacing[0]/target_spacing[2])
    axes[1, 1].set_title(f'Resampled Coronal (thickness: {target_spacing[0]:.2f}mm)')
    axes[1, 1].axis('off')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'thickness_comparison.png'))
    plt.close()

def main():
    STOP_PROCESSING.clear()
    signal.signal(signal.SIGINT, signal_handler)
    
    parser = argparse.ArgumentParser(description='Modify slice thickness of DICOM images')
    parser.add_argument('input_dir', help='Input directory containing DICOM studies')
    parser.add_argument('output_dir', help='Output directory for modified DICOM files')
    parser.add_argument('--thickness', type=float, required=True,
                       help='Target slice thickness in mm')
    parser.add_argument('--visualize', action='store_true', default=True,
                       help='Generate visualization images (default: True)')
    parser.add_argument('--no-visualize', dest='visualize', action='store_false',
                       help='Disable visualization generation')
    
    args = parser.parse_args()
    
    # Create output directory structure
    transform_name = f"thickness_{args.thickness}mm"
    output_base = os.path.join(args.output_dir, transform_name)
    processed_dir = os.path.join(output_base, "processed_files")
    
    os.makedirs(processed_dir, exist_ok=True)

    try:
        # Process each subdirectory maintaining the structure
        for root, dirs, files in os.walk(args.input_dir):
            if STOP_PROCESSING.is_set():
                break
            
            # Skip if no DICOM files in directory
            has_dicoms = any(True for f in files if try_dicom_read(os.path.join(root, f)))
            if not has_dicoms:
                continue
            
            # Create corresponding output directory
            rel_path = os.path.relpath(root, args.input_dir)
            output_subdir = os.path.join(processed_dir, rel_path)
            
            # Create visualization directory specific to this subdirectory
            visualization_subdir = None
            if args.visualize:
                visualization_subdir = os.path.join(output_base, "visualization", rel_path)
                os.makedirs(visualization_subdir, exist_ok=True)
            
            print(f"\nProcessing directory: {root}")
            success = process_dicom_series(
                root, 
                output_subdir, 
                args.thickness,
                visualization_dir=visualization_subdir
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