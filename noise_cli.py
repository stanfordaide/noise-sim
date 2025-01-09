import os
import argparse
import pydicom
import numpy as np
import matplotlib.pyplot as plt
import threading
import signal
import sys
from tqdm import tqdm

STOP_PROCESSING = threading.Event()

def signal_handler(signum, frame):
    print("\nInterrupt received. Cleaning up...")
    STOP_PROCESSING.set()

def add_gaussian_noise(image, mean=0, std=50):
    """
    Add Gaussian noise to the image.
    Args:
        image: Input image
        mean: Mean of the Gaussian noise (default: 0)
        std: Standard deviation of the noise (default: 50)
    """
    noise = np.random.normal(mean, std, image.shape)
    noisy_image = image + noise
    return noisy_image

def add_salt_and_pepper(image, prob=0.05):
    """
    Add salt and pepper noise to the image.
    Args:
        image: Input image
        prob: Probability of noise (default: 0.05)
    """
    noisy_image = image.copy()
    
    # Salt noise
    salt_mask = np.random.random(image.shape) < (prob/2)
    noisy_image[salt_mask] = np.max(image)
    
    # Pepper noise
    pepper_mask = np.random.random(image.shape) < (prob/2)
    noisy_image[pepper_mask] = np.min(image)
    
    return noisy_image

def visualize_noise_effect(original, noisy, output_path, title):
    """Create side-by-side visualization of original and noisy images."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    
    # Display original image
    im1 = ax1.imshow(original, cmap='gray')
    ax1.set_title('Original')
    ax1.axis('off')
    plt.colorbar(im1, ax=ax1)
    
    # Display noisy image
    im2 = ax2.imshow(noisy, cmap='gray')
    ax2.set_title(f'With {title}')
    ax2.axis('off')
    plt.colorbar(im2, ax=ax2)
    
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def process_dicom(input_path, output_path, noise_type, params, visualization_path=None):
    """Process a single DICOM file with noise."""
    if STOP_PROCESSING.is_set():
        return False
        
    try:
        # Read DICOM
        dcm = pydicom.dcmread(input_path)
        
        # Get original image and rescale to HU
        original = dcm.pixel_array * dcm.RescaleSlope + dcm.RescaleIntercept
        
        # Apply noise
        if noise_type == "gaussian":
            noisy = add_gaussian_noise(original, params['mean'], params['std'])
        elif noise_type == "salt_and_pepper":
            noisy = add_salt_and_pepper(original, params['prob'])
        else:
            raise ValueError(f"Unknown noise type: {noise_type}")
        
        # Create visualization if requested
        if visualization_path:
            visualize_noise_effect(
                original, 
                noisy, 
                visualization_path,
                f"{noise_type} noise"
            )
        
        # Convert back to original scale
        pixel_array = (noisy - dcm.RescaleIntercept) / dcm.RescaleSlope
        pixel_array = np.clip(pixel_array, np.min(dcm.pixel_array), np.max(dcm.pixel_array))
        
        # Create new DICOM with noisy image
        new_dcm = dcm.copy()
        new_dcm.PixelData = pixel_array.astype(dcm.pixel_array.dtype).tobytes()
        new_dcm.SeriesDescription = f"{dcm.get('SeriesDescription', 'Unknown')} - {noise_type} noise"
        
        # Save new DICOM
        new_dcm.save_as(output_path)
        return True
        
    except Exception as e:
        print(f"Error processing {input_path}: {str(e)}")
        return False

def main():
    STOP_PROCESSING.clear()
    signal.signal(signal.SIGINT, signal_handler)
    
    parser = argparse.ArgumentParser(description='Add noise to DICOM images')
    parser.add_argument('input_dir', help='Input directory containing DICOM studies')
    parser.add_argument('output_dir', help='Output directory for noisy DICOM files')
    parser.add_argument('--noise-type', choices=['gaussian', 'salt_and_pepper'],
                       required=True, help='Type of noise to add')
    parser.add_argument('--visualize', action='store_true', help='Generate visualizations')
    
    # Noise-specific parameters
    parser.add_argument('--mean', type=float, default=0,
                       help='Mean for Gaussian noise (default: 0)')
    parser.add_argument('--std', type=float, default=50,
                       help='Standard deviation for Gaussian noise (default: 50)')
    parser.add_argument('--prob', type=float, default=0.05,
                       help='Probability for salt and pepper noise (default: 0.05)')
    
    args = parser.parse_args()
    
    # Create output directory structure
    noise_params = {
        'gaussian': f"mean{args.mean}_std{args.std}",
        'salt_and_pepper': f"prob{args.prob}"
    }[args.noise_type]
    
    transform_name = f"{args.noise_type}_noise_{noise_params}"
    output_base = os.path.join(args.output_dir, transform_name)
    processed_dir = os.path.join(output_base, "processed_files")
    visualization_dir = os.path.join(output_base, "visualization") if args.visualize else None
    
    os.makedirs(processed_dir, exist_ok=True)
    if visualization_dir:
        os.makedirs(visualization_dir, exist_ok=True)
    
    # Set noise parameters
    params = {
        'mean': args.mean,
        'std': args.std,
        'prob': args.prob
    }
    
    try:
        # Process each file in the directory structure
        for root, _, files in os.walk(args.input_dir):
            if STOP_PROCESSING.is_set():
                break
                
            for file in tqdm(files, desc=f"Processing {root}"):
                if STOP_PROCESSING.is_set():
                    break
                    
                input_path = os.path.join(root, file)
                try:
                    # Quick check if file is DICOM
                    pydicom.dcmread(input_path, stop_before_pixels=True)
                    
                    # Create output paths
                    rel_path = os.path.relpath(root, args.input_dir)
                    output_subdir = os.path.join(processed_dir, rel_path)
                    os.makedirs(output_subdir, exist_ok=True)
                    
                    # Create visualization subdir matching input structure
                    if visualization_dir:
                        vis_subdir = os.path.join(visualization_dir, rel_path)
                        os.makedirs(vis_subdir, exist_ok=True)
                        vis_path = os.path.join(vis_subdir, f"{os.path.splitext(file)[0]}_vis.png")
                    else:
                        vis_path = None
                    
                    output_path = os.path.join(output_subdir, file)
                    
                    # Process the file
                    success = process_dicom(
                        input_path,
                        output_path,
                        args.noise_type,
                        params,
                        vis_path
                    )
                    
                    if success:
                        print(f"Processed: {input_path}")
                        
                except KeyboardInterrupt:
                    STOP_PROCESSING.set()
                except:
                    continue
                    
    except KeyboardInterrupt:
        STOP_PROCESSING.set()
        print("\nInterrupted by user. Cleaning up...")
        sys.exit(0)

if __name__ == "__main__":
    main() 