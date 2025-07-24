#!/usr/bin/env python3
"""
Example usage of the HLS Sentinel-2 data downloader.
This script demonstrates how to use the HLSDownloader class programmatically.
"""

from download_hls_data import HLSDownloader, parse_coordinates_file


def example_download_with_coordinates_file():
    """Example: Download data using coordinates from a file."""
    print("=== Example 1: Download using coordinates file ===")
    
    # Parse coordinates from existing file
    coords_file = "../data/sentinel/region-0/coordinates.txt"
    try:
        sw_coords, ne_coords = parse_coordinates_file(coords_file)
        print(f"Loaded coordinates - SW: {sw_coords}, NE: {ne_coords}")
    except FileNotFoundError:
        print(f"Coordinates file not found: {coords_file}")
        print("Using example coordinates instead...")
        sw_coords = (45.24301, 78.44504)
        ne_coords = (45.2912, 78.49116)
    
    # Initialize downloader
    downloader = HLSDownloader()
    
    # Download specific bands for a recent date
    downloaded_files = downloader.download_hls_data(
        sw_coords=sw_coords,
        ne_coords=ne_coords,
        date="2024-07-15",  # Single date
        bands=["B02", "B03", "B04"],  # Blue, Green, Red bands
        output_dir="./downloaded_data/example1",
        max_results=10
    )
    
    print(f"Downloaded {len(downloaded_files)} files")


def example_download_date_range():
    """Example: Download data for a date range."""
    print("\n=== Example 2: Download for date range ===")
    
    # Use coordinates directly
    sw_coords = (45.24301, 78.44504)
    ne_coords = (45.2912, 78.49116)
    
    downloader = HLSDownloader()
    
    # Download data for a date range
    downloaded_files = downloader.download_hls_data(
        sw_coords=sw_coords,
        ne_coords=ne_coords,
        date="2024-07-01,2024-07-31",  # Date range
        bands=["B8A", "B11", "B12"],  # NIR, SWIR bands
        output_dir="./downloaded_data/example2",
        max_results=20
    )
    
    print(f"Downloaded {len(downloaded_files)} files")


def example_list_available_data():
    """Example: List available data without downloading."""
    print("\n=== Example 3: List available data ===")
    
    sw_coords = (45.24301, 78.44504)
    ne_coords = (45.2912, 78.49116)
    
    downloader = HLSDownloader()
    
    # List available data for a recent date
    downloader.list_available_data(
        sw_coords=sw_coords,
        ne_coords=ne_coords,
        date="2024-07-15",
        max_results=5
    )


def example_download_all_bands():
    """Example: Download all available bands."""
    print("\n=== Example 4: Download all bands ===")
    
    sw_coords = (45.24301, 78.44504)
    ne_coords = (45.2912, 78.49116)
    
    downloader = HLSDownloader()
    
    # Download all common HLS bands
    all_bands = ["B02", "B03", "B04", "B05", "B06", "B07", "B8A", "B11", "B12"]
    
    downloaded_files = downloader.download_hls_data(
        sw_coords=sw_coords,
        ne_coords=ne_coords,
        date="2024-07-15",
        bands=all_bands,
        output_dir="./downloaded_data/example4",
        max_results=30
    )
    
    print(f"Downloaded {len(downloaded_files)} files")


if __name__ == "__main__":
    print("HLS Sentinel-2 Data Downloader - Example Usage")
    print("=" * 50)
    
    try:
        # Run examples
        example_list_available_data()
        example_download_with_coordinates_file()
        example_download_date_range()
        example_download_all_bands()
        
        print("\n✓ All examples completed!")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        print("Make sure you have:")
        print("1. Valid NASA Earthdata credentials")
        print("2. Internet connection")
        print("3. Installed required packages: pip install -r requirements.txt") 