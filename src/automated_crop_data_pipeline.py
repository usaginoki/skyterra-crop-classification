#!/usr/bin/env python3
"""
Automated Crop Classification Data Pipeline

This script automates the entire process of downloading and assembling HLS satellite data
for crop classification. Given a center coordinate and date range, it:

1. Creates a square bounding box around the center point
2. Calculates 3 evenly spaced dates (t0, t1, t2) 
3. Downloads HLS data for each date with ±3 day windows
4. Assembles the data into a single 18-band multi-temporal image

Usage:
    python automated_crop_data_pipeline.py --center-lat 51.024681 --center-lon 71.841594 --start-date 2025-01-01 --end-date 2025-01-31 --output-dir ./pipeline_output

Author: Generated for crop-classification project
"""

import os
import sys
import argparse
import subprocess
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import glob
from typing import Tuple, List


class CropDataPipeline:
    """Automated pipeline for downloading and assembling crop classification data."""
    
    def __init__(self, center_lat: float, center_lon: float, start_date: str, end_date: str, 
                 bbox_size: float = 0.01, output_dir: str = "./pipeline_output"):
        """
        Initialize the pipeline.
        
        Args:
            center_lat: Center latitude coordinate
            center_lon: Center longitude coordinate  
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            bbox_size: Half-width of bounding box in decimal degrees (default: 0.01 = ~1km)
            output_dir: Directory for all pipeline outputs
        """
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        self.bbox_size = bbox_size
        self.output_dir = output_dir
        self.bands = ['B02', 'B03', 'B04', 'B8A', 'B11', 'B12']
        
        # Create output directories
        os.makedirs(self.output_dir, exist_ok=True)
        self.downloads_dir = os.path.join(self.output_dir, 'downloads')
        self.organized_dir = os.path.join(self.output_dir, 'organized')
        os.makedirs(self.downloads_dir, exist_ok=True)
        os.makedirs(self.organized_dir, exist_ok=True)
        
        print(f"🚀 Initializing Crop Data Pipeline")
        print(f"   Center: ({self.center_lat}, {self.center_lon})")
        print(f"   Date range: {start_date} to {end_date}")
        print(f"   Bounding box size: ±{self.bbox_size}°")
        print(f"   Output directory: {self.output_dir}")
    
    def create_bounding_box(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Create a square bounding box around the center point.
        
        Returns:
            Tuple of (sw_coords, ne_coords) where each coord is (lat, lon)
        """
        sw_lat = self.center_lat - self.bbox_size
        sw_lon = self.center_lon - self.bbox_size
        ne_lat = self.center_lat + self.bbox_size
        ne_lon = self.center_lon + self.bbox_size
        
        sw_coords = (sw_lat, sw_lon)
        ne_coords = (ne_lat, ne_lon)
        
        print(f"📍 Created bounding box:")
        print(f"   SW: {sw_coords} (lat, lon)")
        print(f"   NE: {ne_coords} (lat, lon)")
        print(f"   Size: {2 * self.bbox_size}° x {2 * self.bbox_size}°")
        
        return sw_coords, ne_coords
    
    def calculate_time_points(self) -> List[datetime]:
        """
        Calculate 3 evenly spaced time points between start and end dates.
        
        Returns:
            List of 3 datetime objects [t0, t1, t2]
        """
        total_days = (self.end_date - self.start_date).days
        
        if total_days < 2:
            raise ValueError("Date range must be at least 2 days to create 3 time points")
        
        # Calculate evenly spaced intervals
        interval_days = total_days / 2
        
        t0 = self.start_date
        t1 = self.start_date + timedelta(days=interval_days)
        t2 = self.end_date
        
        time_points = [t0, t1, t2]
        
        print(f"📅 Calculated time points:")
        for i, tp in enumerate(time_points):
            print(f"   t{i}: {tp.strftime('%Y-%m-%d')}")
        
        return time_points
    
    def create_coordinates_file(self, sw_coords: Tuple[float, float], ne_coords: Tuple[float, float]) -> str:
        """
        Create a coordinates.txt file for the download script.
        
        Args:
            sw_coords: Southwest coordinates (lat, lon)
            ne_coords: Northeast coordinates (lat, lon)
            
        Returns:
            Path to the created coordinates file
        """
        coords_file = os.path.join(self.output_dir, 'coordinates.txt')
        
        with open(coords_file, 'w') as f:
            f.write(f"sw {sw_coords[0]},{sw_coords[1]}\n")
            f.write(f"ne {ne_coords[0]},{ne_coords[1]}\n")
        
        print(f"📝 Created coordinates file: {coords_file}")
        return coords_file
    
    def download_for_time_point(self, time_point: datetime, time_index: int, coords_file: str) -> str:
        """
        Download HLS data for a specific time point with ±3 day window.
        
        Args:
            time_point: Target date for download
            time_index: Time index (0, 1, or 2) for folder naming
            coords_file: Path to coordinates file
            
        Returns:
            Path to download directory for this time point
        """
        # Create ±3 day window
        start_window = time_point - timedelta(days=3)
        end_window = time_point + timedelta(days=3)
        date_range = f"{start_window.strftime('%Y-%m-%d')},{end_window.strftime('%Y-%m-%d')}"
        
        # Create time-specific download directory
        time_download_dir = os.path.join(self.downloads_dir, f't{time_index}')
        os.makedirs(time_download_dir, exist_ok=True)
        
        print(f"\n⬇️  Downloading data for t{time_index}: {time_point.strftime('%Y-%m-%d')}")
        print(f"   Search window: {date_range}")
        print(f"   Download directory: {time_download_dir}")
        
        # Construct download command
        script_path = os.path.join(os.path.dirname(__file__), 'download_hls_data.py')
        cmd = [
            sys.executable, script_path,
            '--coords-file', coords_file,
            '--date', date_range,
            '--bands'] + self.bands + [
            '--output-dir', time_download_dir,
            '--auto-download'  # Automatically download first granule
        ]
        
        print(f"   Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"   ✓ Download completed for t{time_index}")
            if result.stdout:
                print(f"   Output: {result.stdout.split('✓ Successfully downloaded')[-1].strip() if '✓ Successfully downloaded' in result.stdout else 'Download completed'}")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Download failed for t{time_index}: {e}")
            print(f"   Error output: {e.stderr}")
            raise
        
        return time_download_dir
    
    def organize_downloaded_files(self, download_dirs: List[str]) -> str:
        """
        Organize downloaded files into the structure expected by assemble_rasterio.py.
        
        Args:
            download_dirs: List of download directories for each time point
            
        Returns:
            Path to organized directory ready for assembly
        """
        print(f"\n📁 Organizing downloaded files...")
        
        for time_index, download_dir in enumerate(download_dirs):
            time_organized_dir = os.path.join(self.organized_dir, f't{time_index}')
            os.makedirs(time_organized_dir, exist_ok=True)
            
            print(f"   Processing t{time_index}...")
            
            # Find all .tif files in the download directory (including subdirectories)
            tif_files = []
            for root, dirs, files in os.walk(download_dir):
                for file in files:
                    if file.endswith('.tif') and not file.endswith('.aux.xml'):
                        tif_files.append(os.path.join(root, file))
            
            print(f"   Found {len(tif_files)} .tif files")
            
            # Group files by band and copy the first one found for each band
            bands_found = {}
            for tif_file in tif_files:
                filename = os.path.basename(tif_file)
                for band in self.bands:
                    if f'.{band}.' in filename and band not in bands_found:
                        dest_path = os.path.join(time_organized_dir, f"{band}.tif")
                        shutil.copy2(tif_file, dest_path)
                        bands_found[band] = dest_path
                        print(f"     Copied {band}: {os.path.basename(tif_file)}")
                        break
            
            # Check if all bands were found
            missing_bands = set(self.bands) - set(bands_found.keys())
            if missing_bands:
                print(f"   ⚠️  Warning: Missing bands for t{time_index}: {missing_bands}")
            else:
                print(f"   ✓ All {len(self.bands)} bands organized for t{time_index}")
        
        # Create coordinates.txt in organized directory for assembly script
        coords_source = os.path.join(self.output_dir, 'coordinates.txt')
        coords_dest = os.path.join(self.organized_dir, 'coordinates.txt')
        if os.path.exists(coords_source):
            shutil.copy2(coords_source, coords_dest)
            print(f"   📝 Copied coordinates.txt to organized directory")
        
        print(f"   ✓ Files organized in: {self.organized_dir}")
        return self.organized_dir
    
    def assemble_final_image(self, organized_dir: str) -> str:
        """
        Assemble the organized files into a single 18-band image.
        
        Args:
            organized_dir: Directory with organized t0, t1, t2 folders
            
        Returns:
            Path to the final assembled image
        """
        output_image = os.path.join(self.output_dir, 'assembled_18band.tif')
        
        print(f"\n🔨 Assembling 18-band image...")
        print(f"   Input directory: {organized_dir}")
        print(f"   Output image: {output_image}")
        
        # Construct assembly command
        script_path = os.path.join(os.path.dirname(__file__), 'assemble_rasterio.py')
        cmd = [
            sys.executable, script_path,
            organized_dir,
            '--output', output_image
        ]
        
        print(f"   Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"   ✓ Assembly completed!")
            print(f"   Final image: {output_image}")
            if result.stdout:
                # Extract relevant info from assembly output
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Output shape:' in line or 'Assembly complete!' in line:
                        print(f"   {line.strip()}")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Assembly failed: {e}")
            print(f"   Error output: {e.stderr}")
            raise
        
        return output_image
    
    def run_pipeline(self) -> str:
        """
        Run the complete pipeline.
        
        Returns:
            Path to the final assembled 18-band image
        """
        print(f"\n{'='*60}")
        print(f"🚀 STARTING AUTOMATED CROP DATA PIPELINE")
        print(f"{'='*60}")
        
        try:
            # Step 1: Create bounding box
            print(f"\n📍 STEP 1: Creating bounding box")
            sw_coords, ne_coords = self.create_bounding_box()
            
            # Step 2: Calculate time points
            print(f"\n📅 STEP 2: Calculating time points")
            time_points = self.calculate_time_points()
            
            # Step 3: Create coordinates file
            print(f"\n📝 STEP 3: Creating coordinates file")
            coords_file = self.create_coordinates_file(sw_coords, ne_coords)
            
            # Step 4: Download data for each time point
            print(f"\n⬇️  STEP 4: Downloading HLS data")
            download_dirs = []
            for i, time_point in enumerate(time_points):
                download_dir = self.download_for_time_point(time_point, i, coords_file)
                download_dirs.append(download_dir)
            
            # Step 5: Organize files
            print(f"\n📁 STEP 5: Organizing files")
            organized_dir = self.organize_downloaded_files(download_dirs)
            
            # Step 6: Assemble final image
            print(f"\n🔨 STEP 6: Assembling final image")
            final_image = self.assemble_final_image(organized_dir)
            
            # Success summary
            print(f"\n{'='*60}")
            print(f"✅ PIPELINE COMPLETED SUCCESSFULLY!")
            print(f"{'='*60}")
            print(f"📊 Summary:")
            print(f"   Center coordinate: ({self.center_lat}, {self.center_lon})")
            print(f"   Date range: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
            print(f"   Bounding box: ±{self.bbox_size}° ({2*self.bbox_size}° x {2*self.bbox_size}°)")
            print(f"   Time points: {len(time_points)} dates")
            print(f"   Bands per time: {len(self.bands)}")
            print(f"   Total bands: {len(time_points) * len(self.bands)}")
            print(f"   Final image: {final_image}")
            print(f"   Output directory: {self.output_dir}")
            
            return final_image
            
        except Exception as e:
            print(f"\n{'='*60}")
            print(f"❌ PIPELINE FAILED!")
            print(f"{'='*60}")
            print(f"Error: {e}")
            raise


def main():
    """Main entry point with command line interface."""
    parser = argparse.ArgumentParser(
        description="Automated Crop Classification Data Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with center coordinates and date range
  python automated_crop_data_pipeline.py --center-lat 51.024681 --center-lon 71.841594 --start-date 2025-03-01 --end-date 2025-06-30

  # Custom bounding box size and output directory
  python automated_crop_data_pipeline.py --center-lat 45.24301 --center-lon 78.44504 --start-date 2025-01-15 --end-date 2025-02-15 --bbox-size 0.02 --output-dir ./custom_output

  # Smaller bounding box for detailed analysis
  python automated_crop_data_pipeline.py --center-lat 52.1234 --center-lon 5.6789 --start-date 2025-03-01 --end-date 2025-05-01 --bbox-size 0.005
        """
    )
    
    # Required parameters
    parser.add_argument('--center-lat', type=float, required=True,
                       help='Center latitude coordinate (decimal degrees)')
    parser.add_argument('--center-lon', type=float, required=True,
                       help='Center longitude coordinate (decimal degrees)')
    parser.add_argument('--start-date', required=True,
                       help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', required=True,
                       help='End date in YYYY-MM-DD format')
    
    # Optional parameters
    parser.add_argument('--bbox-size', type=float, default=0.01,
                       help='Half-width of bounding box in decimal degrees (default: 0.01 ≈ 1km)')
    parser.add_argument('--output-dir', default='./pipeline_output',
                       help='Output directory for all pipeline files (default: ./pipeline_output)')
    
    args = parser.parse_args()
    
    try:
        # Validate coordinates
        if not (-90 <= args.center_lat <= 90):
            raise ValueError("Center latitude must be between -90 and 90 degrees")
        if not (-180 <= args.center_lon <= 180):
            raise ValueError("Center longitude must be between -180 and 180 degrees")
        
        # Validate bbox size
        if args.bbox_size <= 0 or args.bbox_size > 1:
            raise ValueError("Bounding box size must be between 0 and 1 degrees")
        
        # Validate dates
        try:
            start_dt = datetime.strptime(args.start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(args.end_date, '%Y-%m-%d')
            if start_dt >= end_dt:
                raise ValueError("Start date must be before end date")
        except ValueError as e:
            if "time data" in str(e):
                raise ValueError("Dates must be in YYYY-MM-DD format")
            raise
        
        # Initialize and run pipeline
        pipeline = CropDataPipeline(
            center_lat=args.center_lat,
            center_lon=args.center_lon,
            start_date=args.start_date,
            end_date=args.end_date,
            bbox_size=args.bbox_size,
            output_dir=args.output_dir
        )
        
        final_image = pipeline.run_pipeline()
        print(f"\n🎉 SUCCESS! Final 18-band image ready: {final_image}")
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit(main()) 