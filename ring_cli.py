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

def create_ring_artifact(shape, center=None, num_rings=3, intensity=1.0, thickness=2, radius_range=(0.2, 0.8)):
    """
    Create ring artifacts in a 2D image.
    
    Args:
        shape: Shape of the image (height, width)
        center: Center of rings (defaults to image center)
        num_rings: Number of rings to generate
        intensity: Strength of ring artifacts (-1.0 to 1.0)
        thickness: Thickness of rings in pixels
        radius_range: (min_radius, max_radius) as fraction of image size
    """
    if center is None:
        center = np.array(shape) / 2
    
    # Create coordinate grid
    y, x = np.ogrid[:shape[0], :shape[1]]
    
    # Calculate distances from center
    distances = np.sqrt((x - center[1])**2 + (y - center[0])**2)
    
    # Initialize ring mask
    ring_mask = np.zeros(shape)
    
    # Calculate min and max radii in pixels
    min_radius = radius_range[0] * min(shape)
    max_radius = radius_range[1] * min(shape)
    
    # Generate random radii for rings
    radii = np.linspace(min_radius, max_radius, num_rings)
    
    # Create rings
    for radius in radii:
        # Create ring with specified thickness
        ring = np.abs(distances - radius) < thickness/2
        
        # Add random intensity variation along the ring
        angle = np.arctan2(y - center[0], x - center[1])
        variation = np.sin(angle * np.random.randint(2, 6)) * 0.3
        
        # Add ring to mask with intensity variation
        ring_mask += ring * (intensity * (1 + variation))
    
    return ring_mask

def apply_ring_artifacts(volume, num_rings=3, intensity=1.0, thickness=2, radius_range=(0.2, 0.8)):
    """
    Apply ring artifacts to a 3D volume.
    
    Args:
        volume: 3D numpy array
        num_rings: Number of rings per slice
        intensity: Strength of ring artifacts
        thickness: Thickness of rings in pixels
        radius_range: (min_radius, max_radius) as fraction of image size
    """
    result = volume.copy()
    
    # Create different ring patterns for each slice
    for z in range(volume.shape[0]):
        # Create ring artifact pattern
        rings = create_ring_artifact(
            volume.shape[1:],
            num_rings=num_rings,
            intensity=intensity,
            thickness=thickness,
            radius_range=radius_range
        )
        
        # Apply rings to slice
        # Scale ring intensity by local image intensity to make artifacts more realistic
        local_scale = np.clip(np.abs(volume[z]) / 1000, 0.1, 1.0)
        result[z] += rings * local_scale * 100  # Scale factor for HU units
    
    return result

def visualize_ring_effect(original, ring_affected, output_dir):
    """Create visualizations of ring artifacts in different planes."""
    # Create directory for visualizations
    os.makedirs(output_dir, exist_ok=True)
    
    # Get middle slices for each plane
    z_mid = original.shape[0] // 2
    y_mid = original.shape[1] // 2
    x_mid = original.shape[2] // 2
    
    # Define planes and slices
    planes = {
        'Axial': (original[z_mid], ring_affected[z_mid]),
        'Coronal': (original[:, y_mid], ring_affected[:, y_mid]),
        'Sagittal': (original[:, :, x_mid], ring_affected[:, :, x_mid])
    }
    
    # Create visualizations for each plane
    for orientation, (orig_slice, ring_slice) in planes.items():
        plt.figure(figsize=(12, 6))
        
        # Set consistent window for visualization
        vmin = np.percentile(orig_slice, 1)
        vmax = np.percentile(orig_slice, 99)
        
        # Create subplot for original image
        plt.subplot(121)
        plt.imshow(orig_slice, cmap='gray', vmin=vmin, vmax=vmax)
        plt.title(f'Original {orientation}')
        plt.axis('off')
        
        # Create subplot for ring-affected image
        plt.subplot(122)
        plt.imshow(ring_slice, cmap='gray', vmin=vmin, vmax=vmax)
        plt.title(f'Ring Artifacts {orientation}')
        plt.axis('off')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'ring_artifacts_{orientation.lower()}.png'))
        plt.close()

def process_dicom_series(input_dir, output_dir, num_rings, intensity, thickness, 
                        radius_range, visualization_dir=None):
    """Process a series of DICOM files with ring artifacts."""
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
    
    # Sort DICOM files by slice position
    sorted_dicoms = []
    for dcm_path in dicom_files:
        dcm = pydicom.dcmread(dcm_path)
        pos = tuple(map(float, dcm.ImagePositionPatient))
        sorted_dicoms.append((pos[2], dcm_path))
    sorted_dicoms.sort()
    
    # Create 3D volume
    print("Converting DICOM series to volume...")
    first_dcm = pydicom.dcmread(sorted_dicoms[0][1])
    volume_shape = (len(sorted_dicoms), *first_dcm.pixel_array.shape)
    volume = np.zeros(volume_shape)
    
    for i, (_, dcm_path) in enumerate(sorted_dicoms):
        dcm = pydicom.dcmread(dcm_path)
        volume[i] = dcm.pixel_array * dcm.RescaleSlope + dcm.RescaleIntercept
    
    # Apply ring artifacts
    print("Applying ring artifacts...")
    ring_volume = apply_ring_artifacts(
        volume,
        num_rings=num_rings,
        intensity=intensity,
        thickness=thickness,
        radius_range=radius_range
    )
    
    # Create visualizations if requested
    if visualization_dir:
        print("Generating visualizations...")
        visualize_ring_effect(volume, ring_volume, visualization_dir)
    
    # Save processed DICOM files
    print("Saving DICOM files...")
    os.makedirs(output_dir, exist_ok=True)
    
    for i, (_, template_path) in enumerate(sorted_dicoms):
        template = pydicom.dcmread(template_path)
        
        # Convert back to original scale
        pixel_array = (ring_volume[i] - template.RescaleIntercept) / template.RescaleSlope
        pixel_array = np.clip(pixel_array, np.min(template.pixel_array), np.max(template.pixel_array))
        
        # Create new DICOM with ring artifacts
        new_dcm = template.copy()
        new_dcm.PixelData = pixel_array.astype(template.pixel_array.dtype).tobytes()
        new_dcm.SeriesDescription = f"{template.get('SeriesDescription', 'Unknown')} - Ring artifacts"
        
        # Save new DICOM
        output_path = os.path.join(output_dir, os.path.basename(template_path))
        new_dcm.save_as(output_path)
    
    return True

def main():
    STOP_PROCESSING.clear()
    signal.signal(signal.SIGINT, signal_handler)
    
    parser = argparse.ArgumentParser(description='Add ring artifacts to DICOM images')
    parser.add_argument('input_dir', help='Input directory containing DICOM studies')
    parser.add_argument('output_dir', help='Output directory for artifact-affected DICOM files')
    parser.add_argument('--num-rings', type=int, default=3,
                       help='Number of rings to generate (default: 3)')
    parser.add_argument('--intensity', type=float, default=0.5,
                       help='Intensity of ring artifacts (0-1, default: 0.5)')
    parser.add_argument('--thickness', type=int, default=2,
                       help='Thickness of rings in pixels (default: 2)')
    parser.add_argument('--min-radius', type=float, default=0.2,
                       help='Minimum ring radius as fraction of image size (default: 0.2)')
    parser.add_argument('--max-radius', type=float, default=0.8,
                       help='Maximum ring radius as fraction of image size (default: 0.8)')
    parser.add_argument('--visualize', action='store_true', default=True,
                       help='Generate visualization images (default: True)')
    parser.add_argument('--no-visualize', dest='visualize', action='store_false',
                       help='Disable visualization generation')
    
    args = parser.parse_args()
    
    # Create output directory structure
    transform_name = f"ring_n{args.num_rings}_i{args.intensity}_t{args.thickness}"
    output_base = os.path.join(args.output_dir, transform_name)
    processed_dir = os.path.join(output_base, "processed_files")
    
    # Remove the single visualization_dir and handle it per subdirectory
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
                args.num_rings,
                args.intensity,
                args.thickness,
                (args.min_radius, args.max_radius),
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