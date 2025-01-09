import os
import argparse
import pydicom
import numpy as np
import astra
import copy
from scipy.ndimage import gaussian_filter
import threading
import signal as sys_signal
import sys
from tqdm import tqdm
import matplotlib.pyplot as plt

STOP_PROCESSING = threading.Event()

def signal_handler(signum, frame):
    print("\nInterrupt received. Cleaning up...")
    STOP_PROCESSING.set()

def make_projector(angle, vol_geom, nr_detectors):
    """Create ASTRA projector for given angle"""
    proj_geom = astra.create_proj_geom('parallel', 1, nr_detectors, [angle])
    projector_id = astra.creators.create_projector('line', proj_geom, vol_geom)
    return projector_id

def simulate_motion_artifact(slice_data, motion_params):
    """
    Simulate motion artifacts using ASTRA toolbox approach.
    
    Args:
        slice_data: 2D numpy array of single CT slice
        motion_params: dict containing:
            - amplitude_x: Motion in x direction (pixels)
            - amplitude_y: Motion in y direction (pixels)
    """
    # Create copy of original data
    temp = copy.copy(slice_data)
    
    # Setup ASTRA geometry
    vol_geom = astra.creators.create_vol_geom(temp.shape[0], temp.shape[1])
    nr_detectors = np.max(temp.shape) + 128
    nr_angles = 360
    angles = np.linspace(0, np.pi, nr_angles)
    
    # Initialize sinogram
    sinogram = np.zeros((nr_angles, nr_detectors))
    
    # Calculate motion indices
    angles_x = np.linspace(0, nr_angles, np.absolute(motion_params['amplitude_x'])+2).astype(np.int32)
    angles_y = np.linspace(0, nr_angles, np.absolute(motion_params['amplitude_y'])+2).astype(np.int32)
    
    # Remove start/end angles
    angles_x = angles_x[1:-1]
    angles_y = angles_y[1:-1]
    
    # Combine motion angles
    motion_angles = np.unique(np.concatenate((angles_x, angles_y)))
    
    # Simulate CT acquisition
    for i, angle in enumerate(angles):
        projector_id = make_projector(angle, vol_geom, nr_detectors)
        
        # Apply motion at specified angles
        if i in motion_angles:
            if i in angles_x:
                temp = np.roll(temp, np.sign(motion_params['amplitude_x']), axis=1)
            if i in angles_y:
                temp = np.roll(temp, np.sign(motion_params['amplitude_y']), axis=0)
        
        # Create projection
        sino_id, sino = astra.creators.create_sino(temp, projector_id, returnData=True)
        sinogram[i,:] = sino
        
        astra.projector.delete(projector_id)
    
    # Cleanup
    astra.projector.clear()
    
    # Reconstruct image
    proj_geom = astra.create_proj_geom('parallel', 1, nr_detectors, angles)
    projector_id = astra.creators.create_projector('line', proj_geom, vol_geom)
    
    sinogram_id = astra.data2d.create('-sino', proj_geom, sinogram)
    reconstruction_id = astra.data2d.create('-vol', vol_geom)
    
    # Use FBP algorithm
    alg_cfg = astra.astra_dict('FBP')
    alg_cfg['ProjectorId'] = projector_id
    alg_cfg['ProjectionDataId'] = sinogram_id
    alg_cfg['ReconstructionDataId'] = reconstruction_id
    algorithm_id = astra.algorithm.create(alg_cfg)
    
    astra.algorithm.run(algorithm_id)
    reconstruction = astra.data2d.get(reconstruction_id)
    
    # Cleanup
    astra.algorithm.delete(algorithm_id)
    astra.data2d.delete(sinogram_id)
    astra.data2d.delete(reconstruction_id)
    
    # Apply slight Gaussian filtering
    reconstruction = gaussian_filter(reconstruction, sigma=0.5)
    
    return np.clip(reconstruction, 0, 1)

def dicoms_to_volume(dicom_files):
    """Convert a list of DICOM files to a 3D volume."""
    # Sort DICOM files by ImagePositionPatient
    sorted_dicoms = []
    for filepath in dicom_files:
        ds = pydicom.dcmread(filepath)
        sorted_dicoms.append((ds.ImagePositionPatient[2], ds, filepath))
    sorted_dicoms.sort()
    
    # Extract pixel arrays and normalize
    volume = []
    final_sorted_dicoms = []
    for _, ds, filepath in sorted_dicoms:
        if STOP_PROCESSING.is_set():
            return None, None
        
        # Normalize pixel values to [0,1]
        pixel_array = ds.pixel_array.astype(float)
        pixel_min = float(np.min(pixel_array))
        pixel_max = float(np.max(pixel_array))
        normalized_array = (pixel_array - pixel_min) / (pixel_max - pixel_min)
        
        volume.append(normalized_array)
        final_sorted_dicoms.append((filepath, ds, (pixel_min, pixel_max)))
    
    return np.array(volume), final_sorted_dicoms

def volume_to_dicoms(volume, sorted_dicoms, output_dir):
    """Convert a volume back to DICOM files."""
    os.makedirs(output_dir, exist_ok=True)
    
    for i, (filepath, ds, norm_params) in enumerate(sorted_dicoms):
        if STOP_PROCESSING.is_set():
            return
        
        # Denormalize pixel values
        pixel_min, pixel_max = norm_params
        denormalized = volume[i] * (pixel_max - pixel_min) + pixel_min
        
        # Update pixel data
        ds.PixelData = denormalized.astype(ds.pixel_array.dtype).tobytes()
        
        # Save to new location
        output_path = os.path.join(output_dir, os.path.basename(filepath))
        ds.save_as(output_path)

def visualize_motion_effect(original, motion_affected, output_dir):
    """Create visualizations comparing original and motion-affected volumes."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Select middle slices for each orientation
    mid_z = original.shape[0] // 2
    mid_y = original.shape[1] // 2
    mid_x = original.shape[2] // 2
    
    # Create comparison plots for each orientation
    orientations = [
        ('Axial', original[mid_z], motion_affected[mid_z]),
        ('Coronal', original[:, mid_y], motion_affected[:, mid_y]),
        ('Sagittal', original[:, :, mid_x], motion_affected[:, :, mid_x])
    ]
    
    for orientation, orig_slice, motion_slice in orientations:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        # Use same window/level for both images
        vmin = np.min(orig_slice)
        vmax = np.max(orig_slice)
        
        im1 = ax1.imshow(orig_slice, cmap='gray', vmin=vmin, vmax=vmax)
        ax1.set_title(f'Original {orientation}')
        plt.colorbar(im1, ax=ax1)
        
        im2 = ax2.imshow(motion_slice, cmap='gray', vmin=vmin, vmax=vmax)
        ax2.set_title(f'Motion Affected {orientation}')
        plt.colorbar(im2, ax=ax2)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'motion_{orientation.lower()}.png'))
        plt.close()

def process_dicom_series(input_dir, output_dir, motion_params, visualization_dir=None):
    """Process a series of DICOM files with motion artifacts."""
    # Add progress feedback for file collection
    print("Collecting DICOM files...")
    dicom_files = []
    for root, _, files in os.walk(input_dir):
        for file in tqdm(files, desc="Scanning files"):
            if STOP_PROCESSING.is_set():
                return False
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
    if volume is None:
        return False
    
    # Apply motion artifact slice by slice
    print("Applying motion artifacts...")
    motion_volume = np.zeros_like(volume)
    for i in tqdm(range(len(volume)), desc="Processing slices"):
        if STOP_PROCESSING.is_set():
            return False
        motion_volume[i] = simulate_motion_artifact(volume[i], motion_params)
    
    # Create visualizations if requested
    if visualization_dir:
        print("Generating visualizations...")
        # Create subdir-specific visualization directory
        rel_path = os.path.basename(input_dir)
        subdir_vis_path = os.path.join(visualization_dir, rel_path)
        os.makedirs(subdir_vis_path, exist_ok=True)
        visualize_motion_effect(volume, motion_volume, subdir_vis_path)
    
    # Convert back to DICOM
    print("Converting back to DICOM...")
    volume_to_dicoms(motion_volume, sorted_dicoms, output_dir)
    
    return True

def try_dicom_read(filepath):
    """Try to read a file as DICOM."""
    try:
        pydicom.dcmread(filepath, stop_before_pixels=True)
        return True
    except:
        return False

def main():
    STOP_PROCESSING.clear()
    sys_signal.signal(sys_signal.SIGINT, signal_handler)
    
    parser = argparse.ArgumentParser(description='Add motion artifacts to DICOM images')
    parser.add_argument('input_dir', help='Input directory containing DICOM studies')
    parser.add_argument('output_dir', help='Output directory for motion-affected DICOM files')
    parser.add_argument('--amplitude_x', type=int, default=9,
                       help='Motion amplitude in x direction (pixels)')
    parser.add_argument('--amplitude_y', type=int, default=0,
                       help='Motion amplitude in y direction (pixels)')
    parser.add_argument('--visualize', action='store_true', default=True,
                       help='Generate visualization images (default: True)')
    parser.add_argument('--no-visualize', dest='visualize', action='store_false',
                       help='Disable visualization generation')
    
    args = parser.parse_args()
    
    # Create output directory structure
    transform_name = f"motion_amp{args.amplitude_x}_amp{args.amplitude_y}"
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
            motion_params = {
                'amplitude_x': args.amplitude_x,
                'amplitude_y': args.amplitude_y
            }
            success = process_dicom_series(
                root, 
                output_subdir, 
                motion_params,
                visualization_dir=visualization_dir if args.visualize else None
            )
            if success:
                print(f"Saved to: {output_subdir}")
                if args.visualize:
                    vis_subdir = os.path.join(visualization_dir, os.path.relpath(root, args.input_dir))
                    print(f"Visualizations saved to: {vis_subdir}")

    except KeyboardInterrupt:
        STOP_PROCESSING.set()
        print("\nInterrupted by user. Cleaning up...")
        sys.exit(0)

if __name__ == "__main__":
    main() 