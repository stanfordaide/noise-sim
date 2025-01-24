import os
import argparse
import pydicom
import numpy as np
from scipy.ndimage import gaussian_filter
import threading
import signal
import sys
from tqdm import tqdm
import astra
import matplotlib.pyplot as plt

STOP_PROCESSING = threading.Event()

def signal_handler(signum, frame):
    print("\nInterrupt received. Cleaning up...")
    STOP_PROCESSING.set()

def ct_scan(image):
    """Convert image to sinogram using ASTRA with higher detector count."""
    dx, dy = image.shape
    vol_geom = astra.create_vol_geom(dx, dy)
    # Increased number of detector pixels for better quality
    proj_geom = astra.create_proj_geom('parallel', 1.0, 1024,
                                      np.linspace(0, 2 * np.pi, 720, False))
    
    proj_id = astra.create_projector('strip', proj_geom, vol_geom)
    sinogram_id, sinogram = astra.create_sino(image, proj_id)
    
    astra.data2d.delete(sinogram_id)
    astra.projector.delete(proj_id)
    
    return sinogram

def inv_ct_scan(sinogram, image_size):
    """Reconstruct image from sinogram using ASTRA with FBP."""
    vol_geom = astra.create_vol_geom(image_size[0], image_size[1])
    proj_geom = astra.create_proj_geom('parallel', 1.0, 1024,
                                      np.linspace(0, 2 * np.pi, sinogram.shape[0], False))
    
    sinogram_id = astra.data2d.create('-sino', proj_geom, sinogram)
    proj_id = astra.create_projector('strip', proj_geom, vol_geom)
    rec_id = astra.data2d.create('-vol', vol_geom)
    
    # Use FBP for faster reconstruction
    cfg = astra.astra_dict('FBP')
    cfg['ReconstructionDataId'] = rec_id
    cfg['ProjectionDataId'] = sinogram_id
    cfg['ProjectorId'] = proj_id
    
    alg_id = astra.algorithm.create(cfg)
    astra.algorithm.run(alg_id)  # FBP only needs one iteration
    
    image = astra.data2d.get(rec_id)
    
    astra.algorithm.delete(alg_id)
    astra.data2d.delete(rec_id)
    astra.data2d.delete(sinogram_id)
    astra.projector.delete(proj_id)
    
    return image

def create_detector_defects(sinogram_shape, num_defects, intensity, width, angle_range=360):
    """Create realistic detector defects in sinogram space with smaller, more localized defects."""
    detector_response = np.ones(sinogram_shape[1])
    
    # Calculate angular range indices
    angle_start = (360 - angle_range) // 2
    angle_end = angle_start + angle_range
    angle_indices = np.arange(sinogram_shape[0])
    angle_mask = (angle_indices >= (angle_start * sinogram_shape[0] / 360)) & \
                (angle_indices <= (angle_end * sinogram_shape[0] / 360))
    
    # Limit defect region to 20% of detector width
    detector_width = sinogram_shape[1]
    max_defect_region = int(detector_width * 0.2)
    center_pos = detector_width // 2
    defect_region_start = center_pos - max_defect_region // 2
    defect_region_end = center_pos + max_defect_region // 2
    
    # Create clustered defects in limited region
    defect_positions = np.random.choice(
        range(defect_region_start, defect_region_end),
        size=num_defects//2,
        replace=False
    )
    
    for pos in defect_positions:
        # Create smaller clusters (1-2 elements)
        cluster_size = np.random.randint(1, 3)
        for i in range(cluster_size):
            defect_pos = pos + np.random.randint(-1, 2)
            if defect_pos < defect_region_start or defect_pos >= defect_region_end:
                continue
                
            # Create very narrow defect response
            defect_width = np.random.randint(1, min(width + 1, 3))
            start = max(defect_region_start, defect_pos - defect_width//2)
            end = min(defect_region_end, defect_pos + defect_width//2 + 1)
            
            # More subtle intensity variations
            defect_type = np.random.choice(['dead', 'hot'], p=[0.8, 0.2])
            if defect_type == 'dead':
                detector_response[start:end] *= 0.4  # Less extreme dead detector
            else:
                detector_response[start:end] *= 1.3  # More subtle hot detector
    
    return detector_response, angle_mask

def apply_ring_artifacts(volume, num_defects=10, intensity=1.0, width=2, 
                        radius_min=0.1, radius_max=0.9, angle_range=360):
    """Apply ring artifacts using sinogram-based detector defects."""
    result = volume.copy()
    
    for z in range(volume.shape[0]):
        # Convert to sinogram
        sinogram = ct_scan(volume[z])
        
        # Create detector defects with angular limitation
        detector_response, angle_mask = create_detector_defects(
            sinogram.shape, num_defects, intensity, width, angle_range
        )
        
        # Apply detector response only to specified angular range
        sinogram_defective = sinogram.copy()
        sinogram_defective[angle_mask] = sinogram[angle_mask] * detector_response[None, :]
        
        # Add subtle variations over projection angles
        angle_variations = np.random.normal(1.0, 0.005, (sinogram.shape[0], 1))
        sinogram_defective[angle_mask] *= angle_variations[angle_mask]
        
        # Reconstruct image
        result[z] = inv_ct_scan(sinogram_defective, volume[z].shape)
    
    return result

def apply_window(image, center, width):
    """Apply window/level to image for visualization."""
    image = image.copy()
    min_value = center - width // 2
    max_value = center + width // 2
    image[image < min_value] = min_value
    image[image > max_value] = max_value
    return (image - min_value) / (max_value - min_value)

def create_comparison_plot(original_image, artifact_image, title):
    """Create side-by-side comparison plot."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    
    # Calculate window/level automatically
    window = 2000
    center = 0
    
    # Apply same windowing to both images
    orig_windowed = apply_window(original_image, center, window)
    art_windowed = apply_window(artifact_image, center, window)
    
    ax1.imshow(orig_windowed, cmap='gray')
    ax1.set_title('Original')
    ax1.axis('off')
    
    ax2.imshow(art_windowed, cmap='gray')
    ax2.set_title(f'Ring Artifacts ({title})')
    ax2.axis('off')
    
    plt.tight_layout()
    return fig

def process_dicom(input_path, output_path, num_defects, intensity, width, visualize=False):
    """Process a single DICOM file."""
    if STOP_PROCESSING.is_set():
        return False
    
    try:
        # Read DICOM
        dcm = pydicom.dcmread(input_path)
        image = dcm.pixel_array * dcm.RescaleSlope + dcm.RescaleIntercept
        
        # Apply ring artifacts
        processed = apply_ring_artifacts(
            image[None, ...],
            num_defects=num_defects,
            intensity=intensity,
            width=width
        )[0]
        
        # Create visualization if requested
        if visualize:
            vis_path = output_path.replace('.dcm', '_comparison.png')
            fig = create_comparison_plot(
                image, 
                processed,
                f"Defects: {num_defects}, Intensity: {intensity:.1f}"
            )
            fig.savefig(vis_path)
            plt.close(fig)
        
        # Convert back to original scale
        processed = ((processed - dcm.RescaleIntercept) / dcm.RescaleSlope).astype(dcm.pixel_array.dtype)
        
        # Create new DICOM
        new_dcm = dcm.copy()
        new_dcm.PixelData = processed.tobytes()
        new_dcm.SeriesDescription = f"{dcm.get('SeriesDescription', 'Unknown')} - Ring Artifacts"
        
        # Save new DICOM
        new_dcm.save_as(output_path)
        return True
        
    except Exception as e:
        print(f"Error processing {input_path}: {str(e)}")
        return False
    finally:
        astra.clear()

def process_dicom_series(input_dir, output_dir, num_defects, intensity, width, visualization_dir=None):
    """Process all DICOM files in a directory."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Get list of files
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        
        success_count = 0
        for file in tqdm(files, desc="Processing files"):
            if STOP_PROCESSING.is_set():
                break
                
            input_path = os.path.join(input_dir, file)
            output_path = os.path.join(output_dir, file)
            
            # Skip if output file already exists
            if os.path.exists(output_path):
                print(f"Skipping {input_path} - output already exists")
                continue
            
            try:
                # Quick check if file is DICOM
                pydicom.dcmread(input_path, stop_before_pixels=True)
                
                # Process the DICOM file
                visualize = visualization_dir is not None
                if visualize:
                    output_path_vis = os.path.join(visualization_dir, file)
                else:
                    output_path_vis = output_path
                    
                success = process_dicom(input_path, output_path_vis, 
                                      num_defects, intensity, width, 
                                      visualize=visualize)
                if success:
                    success_count += 1
                    
            except:
                continue
                
        return success_count > 0
        
    except Exception as e:
        print(f"Error processing directory {input_dir}: {str(e)}")
        return False

def main():
    STOP_PROCESSING.clear()
    signal.signal(signal.SIGINT, signal_handler)
    
    parser = argparse.ArgumentParser(description='Add ring artifacts to DICOM images')
    parser.add_argument('input_dir', help='Input directory containing DICOM studies')
    parser.add_argument('output_dir', help='Output directory for artifact-affected DICOM files')
    parser.add_argument('--num-defects', type=int, default=10,
                       help='Number of detector defects to generate (default: 10)')
    parser.add_argument('--intensity', type=float, default=1.0,
                       help='Intensity of ring artifacts (0-2, default: 1.0)')
    parser.add_argument('--width', type=int, default=2,
                       help='Width of detector defects in pixels (default: 2)')
    parser.add_argument('--radius-min', type=float, default=0.1,
                       help='Minimum radius for ring artifacts (0-1, default: 0.1)')
    parser.add_argument('--radius-max', type=float, default=0.9,
                       help='Maximum radius for ring artifacts (0-1, default: 0.9)')
    parser.add_argument('--angle-range', type=int, default=360,
                       help='Angular range for artifacts in degrees (default: 360)')
    parser.add_argument('--visualize', action='store_true', default=True,
                       help='Generate visualization images (default: True)')
    parser.add_argument('--no-visualize', dest='visualize', action='store_false',
                       help='Disable visualization generation')
    
    args = parser.parse_args()
    
    # Create output directory structure
    transform_name = f"defects_{args.num_defects}_i{args.intensity}_w{args.width}_r{args.radius_min}-{args.radius_max}_a{args.angle_range}"
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
                args.num_defects,
                args.intensity,
                args.width,
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