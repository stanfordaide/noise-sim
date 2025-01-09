import os
import argparse
import pydicom
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
import threading
import signal
import sys
from tqdm import tqdm

STOP_PROCESSING = threading.Event()

def signal_handler(signum, frame):
    print("\nInterrupt received. Cleaning up...")
    STOP_PROCESSING.set()

def simulate_beam_hardening(volume, intensity=1.0, threshold=200):
    """
    Simulate beam hardening artifacts in a 3D volume.
    
    Args:
        volume: 3D numpy array of CT values
        intensity: Strength of the beam hardening effect (0-1)
        threshold: HU threshold for high-density objects
    """
    # Create mask for high-density objects
    dense_mask = volume > threshold
    
    # Initialize artifact volume
    artifact_volume = np.zeros_like(volume)
    
    # Process each axial slice
    for z in range(volume.shape[0]):
        slice_2d = volume[z]
        mask_2d = dense_mask[z]
        
        if not np.any(mask_2d):
            continue
            
        # Find dense objects
        from scipy.ndimage import label
        labeled_objects, num_objects = label(mask_2d)
        
        if num_objects < 2:
            continue
            
        # Create streaking artifacts between dense objects
        for obj1 in range(1, num_objects + 1):
            for obj2 in range(obj1 + 1, num_objects + 1):
                # Get centroids of objects
                y1, x1 = np.mean(np.where(labeled_objects == obj1), axis=1)
                y2, x2 = np.mean(np.where(labeled_objects == obj2), axis=1)
                
                # Create line between objects
                length = int(np.hypot(x2-x1, y2-y1))
                x = np.linspace(x1, x2, length)
                y = np.linspace(y1, y2, length)
                
                # Add dark band artifact
                xx, yy = x.astype(np.int32), y.astype(np.int32)
                mask = (xx >= 0) & (xx < slice_2d.shape[1]) & (yy >= 0) & (yy < slice_2d.shape[0])
                xx, yy = xx[mask], yy[mask]
                
                # Create streak pattern
                streak = -intensity * 100 * np.ones_like(xx, dtype=float)
                artifact_volume[z, yy, xx] += streak
    
    # Add cupping artifact
    y, x = np.ogrid[-volume.shape[1]//2:volume.shape[1]//2,
                    -volume.shape[2]//2:volume.shape[2]//2]
    r = np.hypot(x, y)
    cupping = 1 - (r / np.max(r))**2
    cupping = cupping * intensity * 50  # Scale cupping effect
    
    # Apply cupping to each slice
    for z in range(volume.shape[0]):
        artifact_volume[z] += cupping
    
    # Smooth artifacts
    artifact_volume = gaussian_filter(artifact_volume, sigma=2)
    
    # Combine with original volume
    result_volume = volume + artifact_volume
    
    return result_volume

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
        new_dcm = template.copy()
        
        # Convert back to original scale
        pixel_array = (volume[i] - template.RescaleIntercept) / template.RescaleSlope
        pixel_array = np.clip(pixel_array, 
                            np.min(template.pixel_array),
                            np.max(template.pixel_array))
        new_dcm.PixelData = pixel_array.astype(template.pixel_array.dtype).tobytes()
        
        # Save new DICOM
        output_path = os.path.join(output_dir, os.path.basename(template_path))
        new_dcm.save_as(output_path)

def visualize_beam_hardening(original_vol, hardened_vol, output_dir):
    """Create visualizations comparing original and beam-hardened volumes."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Select middle slices for each orientation
    mid_z = original_vol.shape[0] // 2
    mid_y = original_vol.shape[1] // 2
    mid_x = original_vol.shape[2] // 2
    
    # Create comparison plots for each orientation
    orientations = [
        ('Axial', original_vol[mid_z], hardened_vol[mid_z]),
        ('Coronal', original_vol[:, mid_y], hardened_vol[:, mid_y]),
        ('Sagittal', original_vol[:, :, mid_x], hardened_vol[:, :, mid_x])
    ]
    
    for orientation, orig_slice, hardened_slice in orientations:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        # Use same window/level for both images
        vmin = np.percentile(orig_slice, 1)
        vmax = np.percentile(orig_slice, 99)
        
        im1 = ax1.imshow(orig_slice, cmap='gray', vmin=vmin, vmax=vmax)
        ax1.set_title(f'Original {orientation}')
        plt.colorbar(im1, ax=ax1)
        
        im2 = ax2.imshow(hardened_slice, cmap='gray', vmin=vmin, vmax=vmax)
        ax2.set_title(f'Beam Hardening {orientation}')
        plt.colorbar(im2, ax=ax2)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'beam_hardening_{orientation.lower()}.png'))
        plt.close()

def process_dicom_series(input_dir, output_dir, intensity, threshold, visualization_dir=None):
    """Process a series of DICOM files with beam hardening artifacts."""
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
    
    # Apply beam hardening artifact
    print("Applying beam hardening artifact...")
    hardened_volume = simulate_beam_hardening(volume, intensity, threshold)
    
    # Create visualizations if requested
    if visualization_dir:
        print("Generating visualizations...")
        visualize_beam_hardening(volume, hardened_volume, visualization_dir)
    
    # Convert back to DICOM
    print("Converting back to DICOM...")
    volume_to_dicoms(hardened_volume, sorted_dicoms, output_dir)
    
    return True

def main():
    STOP_PROCESSING.clear()
    signal.signal(signal.SIGINT, signal_handler)
    
    parser = argparse.ArgumentParser(description='Add beam hardening artifacts to DICOM images')
    parser.add_argument('input_dir', help='Input directory containing DICOM studies')
    parser.add_argument('output_dir', help='Output directory for artifact-affected DICOM files')
    parser.add_argument('--intensity', type=float, default=0.5,
                       help='Intensity of beam hardening effect (0-1, default: 0.5)')
    parser.add_argument('--threshold', type=float, default=200,
                       help='HU threshold for high-density objects (default: 200)')
    parser.add_argument('--visualize', action='store_true', default=True,
                       help='Generate visualization images (default: True)')
    parser.add_argument('--no-visualize', dest='visualize', action='store_false',
                       help='Disable visualization generation')
    
    args = parser.parse_args()
    
    # Create output directory structure
    transform_name = f"beam_hardening_int{args.intensity}_thresh{args.threshold}"
    output_base = os.path.join(args.output_dir, transform_name)
    processed_dir = os.path.join(output_base, "processed_files")
    visualization_dir = os.path.join(output_base, "visualization") if args.visualize else None
    
    os.makedirs(processed_dir, exist_ok=True)
    if visualization_dir:
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
            
            # Create corresponding output directory
            rel_path = os.path.relpath(root, args.input_dir)
            output_subdir = os.path.join(processed_dir, rel_path)
            
            print(f"\nProcessing directory: {root}")
            success = process_dicom_series(
                root, 
                output_subdir, 
                args.intensity,
                args.threshold,
                visualization_dir=visualization_dir if args.visualize else None
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