import os
import argparse
import pydicom
import numpy as np
from skimage.transform import resize
import astra
import signal
import sys
import threading
import matplotlib.pyplot as plt
import random

STOP_PROCESSING = threading.Event()

def ct_scan(image):
    dx, dy = image.shape

    vol_geom = astra.create_vol_geom(dx, dy)
    proj_geom = astra.create_proj_geom('parallel', 1.0, 672,
                                       np.linspace(0, 2 * np.pi, 360, False))

    # For CPU-based algorithms, a "projector" object specifies the projection
    # model used. In this case, we use the "strip" model.
    proj_id = astra.create_projector('strip', proj_geom, vol_geom)

    # Create a sinogram from a phantom
    sinogram_id, sinogram = astra.create_sino(image, proj_id)

    astra.data2d.delete(sinogram_id)
    astra.projector.delete(proj_id)

    return sinogram


def inv_ct_scan(sinogram, image_size):

    vol_geom = astra.create_vol_geom(image_size[0], image_size[1])
    proj_geom = astra.create_proj_geom(
        'parallel', 1.0, 672, np.linspace(0, 2 * np.pi, sinogram.shape[0],
                                          False))
    sinogram_id = astra.data2d.create('-sino', proj_geom, sinogram)
    proj_id = astra.create_projector('strip', proj_geom, vol_geom)
    rec_id = astra.data2d.create('-vol', vol_geom)

    cfg = astra.astra_dict('FBP')
    cfg['ReconstructionDataId'] = rec_id
    cfg['ProjectionDataId'] = sinogram_id
    cfg['ProjectorId'] = proj_id
    # Available algorithms:
    # ART, SART, SIRT, CGLS, FBP

    # Create the algorithm object from the configuration structure
    alg_id = astra.algorithm.create(cfg)

    # Run 20 iterations of the algorithm
    # This will have a runtime in the order of 10 seconds.
    astra.algorithm.run(alg_id, 20)

    # Get the result
    image = astra.data2d.get(rec_id)

    astra.algorithm.delete(alg_id)
    astra.data2d.delete(rec_id)
    astra.data2d.delete(sinogram_id)
    astra.projector.delete(proj_id)

    return image


def add_possion_noise(hsino, alpha):

    # the output distribution ~ (mean=hsino, var=hsino/alpha)
    lsino = np.random.poisson(hsino * alpha) / alpha

    return lsino


def rescale_image(image, slope, intercept):
    return image * slope + intercept


def apply_window(image, center, width):
    image = image.copy()
    min_value = center - width // 2
    max_value = center + width // 2
    image[image < min_value] = min_value
    image[image > max_value] = max_value
    image = image / max_value
    return image


def sim_low_dose(image, dose=0.9, image_min=None, image_max=None):

    if image_min is None:
        image_min = np.min(image)

    if image_max is None:
        image_max = np.max(image)

    image = (image - image_min) / (image_max - image_min)

    sinogram = ct_scan(image)

    if dose < 1:
        nsamples = int(round(sinogram.shape[0] * dose))
        sinogram = resize(sinogram, (nsamples, sinogram.shape[1]))

    recon = inv_ct_scan(sinogram, image.shape)

    recon = recon * (image_max - image_min) + image_min

    return recon, sinogram


def process_dicom(input_path, output_path, dose=0.9):
    """Process a single DICOM file and save the low-dose version."""
    if STOP_PROCESSING.is_set():
        return False
        
    try:
        # Read DICOM
        dcm = pydicom.dcmread(input_path)
        
        # Get original image
        image = dcm.pixel_array
        image = rescale_image(image, dcm.RescaleSlope, dcm.RescaleIntercept)
        
        # Generate low-dose version
        recon, _ = sim_low_dose(image, dose)
        
        # Create new DICOM object with low-dose image
        new_dcm = pydicom.Dataset()
        new_dcm = dcm.copy()
        
        # Convert back to original data type and range
        recon = ((recon - dcm.RescaleIntercept) / dcm.RescaleSlope).astype(dcm.pixel_array.dtype)
        new_dcm.PixelData = recon.tobytes()
        
        # Add description of modification
        new_dcm.SeriesDescription = f"{dcm.get('SeriesDescription', 'Unknown')} - Low Dose {dose}"
        
        # Save new DICOM
        new_dcm.save_as(output_path)
        return True
    except Exception as e:
        print(f"Error processing {input_path}: {str(e)}")
        return False
    finally:
        astra.clear()

def signal_handler(signum, frame):
    print("\nCtrl+C pressed. Cleaning up ASTRA objects and exiting...")
    STOP_PROCESSING.set()  # Set the flag to stop processing
    astra.clear()
    sys.exit(0)

def create_comparison_plot(original_image, low_dose_image, title):
    """Create a side-by-side comparison plot of original and low-dose images."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    
    # Calculate window/level automatically based on image statistics
    window = np.percentile(original_image, 99) - np.percentile(original_image, 1)
    center = np.percentile(original_image, 50)
    
    # Apply same windowing to both images
    orig_windowed = apply_window(original_image, center, window)
    low_windowed = apply_window(low_dose_image, center, window)
    
    ax1.imshow(orig_windowed, cmap='gray')
    ax1.set_title('Original')
    ax1.axis('off')
    
    ax2.imshow(low_windowed, cmap='gray')
    ax2.set_title(f'Low Dose ({title})')
    ax2.axis('off')
    
    plt.tight_layout()
    return fig

def main():
    STOP_PROCESSING.clear()
    signal.signal(signal.SIGINT, signal_handler)
    
    parser = argparse.ArgumentParser(description='Generate low-dose versions of DICOM images')
    parser.add_argument('input_dir', help='Input directory containing DICOM studies')
    parser.add_argument('output_dir', help='Output directory for low-dose DICOM files')
    parser.add_argument('--dose', type=float, default=0.9,
                       help='Dose level (0-1), default: 0.9')
    parser.add_argument('--visualize', action='store_true', default=True,
                       help='Generate visualization images (default: True)')
    parser.add_argument('--no-visualize', dest='visualize', action='store_false',
                       help='Disable visualization generation')
    parser.add_argument('--num-samples', type=int, default=5,
                       help='Number of random samples to visualize (default: 5)')
    
    args = parser.parse_args()
    
    # Create base output directory with proper structure
    transform_name = f"dose_{int(args.dose*100)}"
    output_base = os.path.join(args.output_dir, transform_name)
    processed_dir = os.path.join(output_base, 'processed_files')
    os.makedirs(processed_dir, exist_ok=True)

    # Create visualization directory if needed
    if args.visualize:
        vis_dir = os.path.join(output_base, 'visualization')
        os.makedirs(vis_dir, exist_ok=True)

    # Store all DICOM files for random sampling
    dicom_files = []
    
    try:
        # First pass: collect all DICOM files
        for root, dirs, files in os.walk(args.input_dir):
            for file in files:
                input_file = os.path.join(root, file)
                try:
                    pydicom.dcmread(input_file, stop_before_pixels=True)
                    dicom_files.append((root, file))
                except:
                    continue
        
        # Randomly sample files for visualization
        if dicom_files:
            sample_files = random.sample(dicom_files, min(args.num_samples, len(dicom_files)))
            
            # Process samples and create visualizations
            for idx, (root, file) in enumerate(sample_files):
                input_file = os.path.join(root, file)
                print(f"\nProcessing sample {idx+1}/{len(sample_files)}: {input_file}")
                
                # Read original DICOM
                dcm = pydicom.dcmread(input_file)
                original_image = rescale_image(dcm.pixel_array, dcm.RescaleSlope, dcm.RescaleIntercept)
                
                # Generate low-dose version
                low_dose_image, _ = sim_low_dose(original_image, args.dose)
                
                # Create and save visualization
                fig = create_comparison_plot(original_image, low_dose_image, f"Dose {args.dose}")
                fig.savefig(os.path.join(vis_dir, f'comparison_{idx+1}.png'))
                plt.close(fig)
        
        # Continue with normal processing
        for root, dirs, files in os.walk(args.input_dir):
            if STOP_PROCESSING.is_set():
                break
                
            for file in files:
                if STOP_PROCESSING.is_set():
                    break
                    
                input_file = os.path.join(root, file)
                try:
                    # Quick check if file is DICOM
                    pydicom.dcmread(input_file, stop_before_pixels=True)
                    
                    if STOP_PROCESSING.is_set():
                        break
                        
                    # If we get here, it's a DICOM file
                    rel_path = os.path.relpath(root, args.input_dir)
                    output_subdir = os.path.join(processed_dir, rel_path)
                    os.makedirs(output_subdir, exist_ok=True)
                    
                    output_file = os.path.join(output_subdir, file)
                    
                    # Skip if output file already exists
                    if os.path.exists(output_file):
                        print(f"Skipping {input_file} - output already exists")
                        continue
                    
                    print(f"Processing: {input_file}")
                    success = process_dicom(input_file, output_file, args.dose)
                    if success:
                        print(f"Saved to: {output_file}")
                except KeyboardInterrupt:
                    STOP_PROCESSING.set()
                    print("\nInterrupted by user. Cleaning up...")
                    astra.clear()
                    sys.exit(0)
                except:
                    continue
                    
    except KeyboardInterrupt:
        STOP_PROCESSING.set()
        print("\nInterrupted by user. Cleaning up...")
        astra.clear()
        sys.exit(0)


if __name__ == "__main__":
    main()