import numpy as np
import matplotlib.pyplot as plt
import rioxarray
import rasterio
from pathlib import Path

def load_18_band_image(file_path):
    """Load an 18-band satellite image using rioxarray (same as your pipeline)."""
    try:
        # Using the same method as your geospatial_pipelines.py
        data = rioxarray.open_rasterio(file_path)
        # Convert to numpy array (channels, height, width)
        img_array = data.to_numpy()
        print(f"Original shape: {img_array.shape}")
        
        # Convert to channels-last format (height, width, channels) like your pipeline
        img_array = np.transpose(img_array, (1, 2, 0))
        print(f"Channels-last shape: {img_array.shape}")
        
        return img_array, data
    except Exception as e:
        print(f"Error loading with rioxarray: {e}")
        return None, None

def display_rgb_composite(img_array, bands_rgb=[2, 1, 0], title="RGB Composite"):
    """Display RGB composite from selected bands (0-indexed)."""
    if img_array is None:
        print("No image data to display")
        return
    
    # Extract RGB bands and normalize
    rgb_bands = img_array[:, :, bands_rgb]
    
    # Normalize to 0-1 range for display
    rgb_normalized = np.zeros_like(rgb_bands, dtype=np.float32)
    for i in range(3):
        band = rgb_bands[:, :, i]
        band_min, band_max = np.percentile(band, [2, 98])  # 2-98% stretch
        rgb_normalized[:, :, i] = np.clip((band - band_min) / (band_max - band_min), 0, 1)
    
    plt.figure(figsize=(10, 8))
    plt.imshow(rgb_normalized)
    plt.title(f"{title} (Bands {bands_rgb})")
    plt.axis('off')
    plt.show()

def display_all_bands_grid(img_array, max_cols=6):
    """Display all 18 bands in a grid."""
    if img_array is None:
        print("No image data to display")
        return
    
    num_bands = img_array.shape[2]
    cols = min(max_cols, num_bands)
    rows = (num_bands + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(15, 3*rows))
    axes = axes.flatten() if rows > 1 else [axes] if cols == 1 else axes
    
    for i in range(num_bands):
        band_data = img_array[:, :, i]
        # Apply 2-98% stretch for better visualization
        vmin, vmax = np.percentile(band_data, [2, 98])
        
        axes[i].imshow(band_data, cmap='gray', vmin=vmin, vmax=vmax)
        axes[i].set_title(f'Band {i+1}')
        axes[i].axis('off')
    
    # Hide unused subplots
    for i in range(num_bands, len(axes)):
        axes[i].axis('off')
    
    plt.tight_layout()
    plt.show()

def display_band_statistics(img_array):
    """Print statistics for each band."""
    if img_array is None:
        print("No image data to analyze")
        return
    
    print("\nBand Statistics:")
    print("-" * 50)
    for i in range(img_array.shape[2]):
        band = img_array[:, :, i]
        print(f"Band {i+1:2d}: min={band.min():8.2f}, max={band.max():8.2f}, "
              f"mean={band.mean():8.2f}, std={band.std():8.2f}")

def create_false_color_composites(img_array):
    """Create common false color composites for satellite imagery."""
    if img_array is None or img_array.shape[2] < 9:
        print("Need at least 9 bands for standard composites")
        return
    
    # Assuming standard HLS band order: B02, B03, B04, B05, B06, B07, B8A, B11, B12
    # If you have 18 bands, these might be duplicated or from different time periods
    
    composites = {
        "Natural Color (RGB)": [2, 1, 0],  # Red, Green, Blue
        "False Color (NIR)": [6, 2, 1],    # NIR, Red, Green  
        "Agriculture": [6, 5, 2],          # NIR, Red Edge, Red
        "Urban": [7, 6, 2],               # SWIR1, NIR, Red
        "Vegetation": [6, 3, 2],          # NIR, Red Edge 1, Red
    }
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    for i, (name, bands) in enumerate(composites.items()):
        if i >= len(axes):
            break
            
        # Check if bands exist
        if max(bands) < img_array.shape[2]:
            rgb_data = img_array[:, :, bands]
            
            # Normalize each band
            rgb_normalized = np.zeros_like(rgb_data, dtype=np.float32)
            for j in range(3):
                band = rgb_data[:, :, j]
                vmin, vmax = np.percentile(band, [2, 98])
                rgb_normalized[:, :, j] = np.clip((band - vmin) / (vmax - vmin), 0, 1)
            
            axes[i].imshow(rgb_normalized)
            axes[i].set_title(f"{name}\nBands: {bands}")
            axes[i].axis('off')
        else:
            axes[i].text(0.5, 0.5, f"{name}\nBands {bands}\nnot available", 
                        ha='center', va='center', transform=axes[i].transAxes)
            axes[i].axis('off')
    
    # Hide last subplot if needed
    if len(composites) < len(axes):
        axes[-1].axis('off')
    
    plt.tight_layout()
    plt.show()

# Example usage
if __name__ == "__main__":
    # Replace with your actual image path
    # This could be a multi-band TIFF file from your HLS data
    image_path = "../classified/45_pred.tif"
    
    # Example paths based on your project structure:
    # image_path = "./data/downloaded/HLS.S30.T43TGL.2024196T053649.v2.0/stacked_bands.tif"
    # image_path = "./data/your_18_band_image.tif"
    
    print("Loading 18-band satellite image...")
    img_array, data_info = load_18_band_image(image_path)
    
    if img_array is not None:
        print(f"Successfully loaded image with shape: {img_array.shape}")
        
        # Display band statistics
        display_band_statistics(img_array)
        
        # Show all bands in a grid
        print("\nDisplaying all bands...")
        display_all_bands_grid(img_array)
        
        # Show RGB composite (assuming first 3 bands can make a reasonable RGB)
        print("\nDisplaying RGB composite...")
        display_rgb_composite(img_array, bands_rgb=[2, 1, 0], title="RGB Composite")
        
        # Show false color composites if you have standard satellite bands
        print("\nDisplaying false color composites...")
        create_false_color_composites(img_array)
        
        # If you have multi-temporal data (3 time periods), you can compare them:
        if img_array.shape[2] == 18:
            print("\nAssuming 18 bands = 3 time periods × 6 bands each")
            
            # Split into three time periods (6 bands each)
            time1 = img_array[:, :, :6]
            time2 = img_array[:, :, 6:12] 
            time3 = img_array[:, :, 12:18]
            
            # Display RGB for all three time periods
            fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 6))
            
            # Time 1 RGB (assuming bands 2,1,0 are Red,Green,Blue)
            rgb1 = time1[:, :, [2, 1, 0]]
            rgb1_norm = np.zeros_like(rgb1, dtype=np.float32)
            for i in range(3):
                band = rgb1[:, :, i]
                vmin, vmax = np.percentile(band, [2, 98])
                rgb1_norm[:, :, i] = np.clip((band - vmin) / (vmax - vmin), 0, 1)
            
            ax1.imshow(rgb1_norm)
            ax1.set_title("Time Period 1 - RGB")
            ax1.axis('off')
            
            # Time 2 RGB
            rgb2 = time2[:, :, [2, 1, 0]]
            rgb2_norm = np.zeros_like(rgb2, dtype=np.float32)
            for i in range(3):
                band = rgb2[:, :, i]
                vmin, vmax = np.percentile(band, [2, 98])
                rgb2_norm[:, :, i] = np.clip((band - vmin) / (vmax - vmin), 0, 1)
            
            ax2.imshow(rgb2_norm)
            ax2.set_title("Time Period 2 - RGB")
            ax2.axis('off')
            
            # Time 3 RGB
            rgb3 = time3[:, :, [2, 1, 0]]
            rgb3_norm = np.zeros_like(rgb3, dtype=np.float32)
            for i in range(3):
                band = rgb3[:, :, i]
                vmin, vmax = np.percentile(band, [2, 98])
                rgb3_norm[:, :, i] = np.clip((band - vmin) / (vmax - vmin), 0, 1)
            
            ax3.imshow(rgb3_norm)
            ax3.set_title("Time Period 3 - RGB")
            ax3.axis('off')
            
            plt.tight_layout()
            plt.show()
            
            # Show individual bands for each time period
            print("\nDisplaying bands for each time period...")
            
            for t, (time_data, period_name) in enumerate([(time1, "Time Period 1"), 
                                                          (time2, "Time Period 2"), 
                                                          (time3, "Time Period 3")]):
                fig, axes = plt.subplots(2, 3, figsize=(12, 8))
                axes = axes.flatten()
                
                for i in range(6):  # 6 bands per time period
                    band_data = time_data[:, :, i]
                    vmin, vmax = np.percentile(band_data, [2, 98])
                    
                    axes[i].imshow(band_data, cmap='gray', vmin=vmin, vmax=vmax)
                    axes[i].set_title(f'{period_name}\nBand {i+1}')
                    axes[i].axis('off')
                
                plt.suptitle(f"{period_name} - All Bands")
                plt.tight_layout()
                plt.show()
            
            # Create change detection visualization
            print("\nCreating change detection visualization...")
            
            # Calculate differences between time periods
            # Using a representative band (e.g., band 3 - typically red or NIR)
            change_band_idx = 3  # Adjust this based on your band configuration
            
            if change_band_idx < 6:
                band1 = time1[:, :, change_band_idx]
                band2 = time2[:, :, change_band_idx] 
                band3 = time3[:, :, change_band_idx]
                
                # Calculate differences
                diff_1_2 = band2 - band1
                diff_2_3 = band3 - band2
                diff_1_3 = band3 - band1
                
                fig, axes = plt.subplots(2, 2, figsize=(12, 10))
                
                # Original band from each time period
                vmin_orig = min(band1.min(), band2.min(), band3.min())
                vmax_orig = max(band1.max(), band2.max(), band3.max())
                
                im1 = axes[0,0].imshow(band1, cmap='gray', vmin=vmin_orig, vmax=vmax_orig)
                axes[0,0].set_title(f'Time 1 - Band {change_band_idx+1}')
                axes[0,0].axis('off')
                
                # Difference visualizations
                diff_max = max(abs(diff_1_2).max(), abs(diff_2_3).max(), abs(diff_1_3).max())
                
                im2 = axes[0,1].imshow(diff_1_2, cmap='RdBu', vmin=-diff_max, vmax=diff_max)
                axes[0,1].set_title('Change: Time 2 - Time 1')
                axes[0,1].axis('off')
                
                im3 = axes[1,0].imshow(diff_2_3, cmap='RdBu', vmin=-diff_max, vmax=diff_max)
                axes[1,0].set_title('Change: Time 3 - Time 2')
                axes[1,0].axis('off')
                
                im4 = axes[1,1].imshow(diff_1_3, cmap='RdBu', vmin=-diff_max, vmax=diff_max)
                axes[1,1].set_title('Total Change: Time 3 - Time 1')
                axes[1,1].axis('off')
                
                # Add colorbar for change images
                plt.colorbar(im4, ax=axes, shrink=0.8, label='Change Magnitude')
                
                plt.tight_layout()
                plt.show()
    
    else:
        print("Failed to load image. Please check the file path and format.")
        print("\nTroubleshooting tips:")
        print("1. Make sure the file exists and is a valid TIFF/GeoTIFF")
        print("2. Check that you have the required libraries: rioxarray, rasterio")
        print("3. Try with a sample file first")

