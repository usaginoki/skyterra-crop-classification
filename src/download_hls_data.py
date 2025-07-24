#!/usr/bin/env python3
"""
HLS Sentinel-2 Data Downloader
Downloads HLS Sentinel-2 Multi-spectral Instrument Surface Reflectance data 
from NASA Earthdata using the earthaccess library.

Dataset: HLS Sentinel-2 Multi-spectral Instrument Surface Reflectance Daily Global 30m v2.0
Short Name: HLSS30
"""

import earthaccess
import os
from datetime import datetime
from typing import List, Tuple, Optional
import argparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class HLSDownloader:
    """Class to handle HLS Sentinel-2 data downloads from NASA Earthdata."""
    
    def __init__(self):
        """Initialize the downloader and authenticate with NASA Earthdata."""
        try:
            # Try to authenticate using environment variables first
            username = os.getenv('EARTHDATA_USERNAME')
            password = os.getenv('EARTHDATA_PASSWORD')
            
            if username and password:
                print("🔐 Using credentials from environment variables...")
                # Set environment variables for earthaccess to use
                os.environ['EARTHDATA_USERNAME'] = username
                os.environ['EARTHDATA_PASSWORD'] = password
                earthaccess.login(strategy='environment')
                print("✓ Successfully authenticated with NASA Earthdata (from .env)")
            else:
                print("🔐 No credentials found in environment, using interactive login...")
                print("   (Tip: Create a .env file with EARTHDATA_USERNAME and EARTHDATA_PASSWORD)")
                earthaccess.login()
                print("✓ Successfully authenticated with NASA Earthdata (interactive)")
                
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            print("Please ensure you have valid NASA Earthdata credentials")
            print("Option 1: Create a .env file with your credentials (see env.example)")
            print("Option 2: Use interactive login (script will prompt you)")
            raise
    
    def download_hls_data(
        self,
        sw_coords: Tuple[float, float],
        ne_coords: Tuple[float, float], 
        date: str,
        bands: List[str],
        output_dir: str = "./data",
        max_results: int = 50
    ) -> List[str]:
        """
        Download HLS Sentinel-2 data for specified parameters.
        
        Args:
            sw_coords: Southwest coordinates (lat, lon)
            ne_coords: Northeast coordinates (lat, lon)
            date: Date in YYYY-MM-DD format or date range like "2025-01-01,2025-01-31"
            bands: List of bands to download (e.g., ['B02', 'B03', 'B04', 'B8A', 'B11', 'B12'])
            output_dir: Directory to save downloaded files
            max_results: Maximum number of results to return
            
        Returns:
            List of downloaded file paths
        """
        
        # Create bounding box (west, south, east, north)
        bounding_box = (
            min(sw_coords[1], ne_coords[1]),  # west (min longitude)
            min(sw_coords[0], ne_coords[0]),  # south (min latitude)
            max(sw_coords[1], ne_coords[1]),  # east (max longitude)
            max(sw_coords[0], ne_coords[0])   # north (max latitude)
        )
        
        # Parse date parameter
        if ',' in date:
            # Date range provided
            start_date, end_date = date.split(',')
            temporal = (start_date.strip(), end_date.strip())
        else:
            # Single date provided, search for that day
            temporal = (date, date)
        
        print(f"🔍 Searching for HLS Sentinel-2 data...")
        print(f"   Bounding box: {bounding_box}")
        print(f"   Date range: {temporal}")
        print(f"   Bands: {bands}")
        
        try:
            # Search for HLS Sentinel-2 data
            results = earthaccess.search_data(
                short_name='HLSS30',  # HLS Sentinel-2 short name
                bounding_box=bounding_box,
                temporal=temporal,
                count=max_results
            )
            
            print(f"📊 Found {len(results)} granules")
            
            if not results:
                print("❌ No data found for the specified criteria")
                return []
            
            # Filter results by bands if specified
            if bands:
                filtered_results = []
                for result in results:
                    # Check if any of the requested bands are in the granule name
                    granule_name = str(result)
                    for band in bands:
                        if f".{band}." in granule_name:
                            filtered_results.append(result)
                            break
                
                results = filtered_results
                print(f"📊 After band filtering: {len(results)} files")
            
            if not results:
                print("❌ No files found matching the specified bands")
                return []
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Download the data
            print(f"⬇️  Downloading files to {output_dir}...")
            downloaded_files = earthaccess.download(results, output_dir)
            
            print(f"✓ Successfully downloaded {len(downloaded_files)} files")
            
            return downloaded_files
            
        except Exception as e:
            print(f"❌ Error during search/download: {e}")
            return []
    
    def list_available_data(
        self,
        sw_coords: Tuple[float, float],
        ne_coords: Tuple[float, float],
        date: str,
        max_results: int = 10
    ):
        """
        List available HLS data for the specified area and date without downloading.
        
        Args:
            sw_coords: Southwest coordinates (lat, lon)
            ne_coords: Northeast coordinates (lat, lon)
            date: Date in YYYY-MM-DD format or date range
            max_results: Maximum number of results to display
        """
        
        # Create bounding box
        bounding_box = (
            min(sw_coords[1], ne_coords[1]),
            min(sw_coords[0], ne_coords[0]),
            max(sw_coords[1], ne_coords[1]),
            max(sw_coords[0], ne_coords[0])
        )
        
        # Parse date
        if ',' in date:
            start_date, end_date = date.split(',')
            temporal = (start_date.strip(), end_date.strip())
        else:
            temporal = (date, date)
        
        print(f"🔍 Listing available HLS Sentinel-2 data...")
        print(f"   Bounding box: {bounding_box}")
        print(f"   Date range: {temporal}")
        
        try:
            results = earthaccess.search_data(
                short_name='HLSS30',
                bounding_box=bounding_box,
                temporal=temporal,
                count=max_results
            )
            
            print(f"\n📊 Found {len(results)} granules:")
            for i, result in enumerate(results[:max_results], 1):
                print(f"   {i}. {result}")
                
        except Exception as e:
            print(f"❌ Error during search: {e}")


def parse_coordinates_file(file_path: str) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """
    Parse coordinates from a text file in the format used in the project.
    
    Args:
        file_path: Path to coordinates file
        
    Returns:
        Tuple of (sw_coords, ne_coords)
    """
    sw_coords = None
    ne_coords = None
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('sw '):
                    # Parse southwest coordinates
                    coords_str = line.replace('sw ', '')
                    lat, lon = map(float, coords_str.split(','))
                    sw_coords = (lat, lon)
                elif line.startswith('ne '):
                    # Parse northeast coordinates  
                    coords_str = line.replace('ne ', '')
                    lat, lon = map(float, coords_str.split(','))
                    ne_coords = (lat, lon)
        
        if sw_coords is None or ne_coords is None:
            raise ValueError("Could not find both sw and ne coordinates in file")
            
        return sw_coords, ne_coords
        
    except Exception as e:
        print(f"❌ Error parsing coordinates file: {e}")
        raise


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(
        description="Download HLS Sentinel-2 data from NASA Earthdata",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download specific bands for a date using coordinate file
  python download_hls_data.py --coords-file data/sentinel/region-0/coordinates.txt --date 2025-01-15 --bands B02 B03 B04

  # Download data using direct coordinates
  python download_hls_data.py --sw-lat 45.24301 --sw-lon 78.44504 --ne-lat 45.2912 --ne-lon 78.49116 --date 2025-01-15

  # Download data for a date range
  python download_hls_data.py --coords-file coords.txt --date "2025-01-01,2025-01-31" --bands B8A B11 B12

  # List available data without downloading
  python download_hls_data.py --coords-file coords.txt --date 2025-01-15 --list-only
        """
    )
    
    # Coordinate options (either file or direct input)
    coord_group = parser.add_mutually_exclusive_group(required=True)
    coord_group.add_argument('--coords-file', help='Path to coordinates file (sw/ne format)')
    coord_group.add_argument('--coords-direct', nargs=4, type=float, metavar=('SW_LAT', 'SW_LON', 'NE_LAT', 'NE_LON'),
                           help='Direct coordinates: sw_lat sw_lon ne_lat ne_lon')
    
    # Individual coordinate arguments (alternative to coords-direct)
    parser.add_argument('--sw-lat', type=float, help='Southwest latitude')
    parser.add_argument('--sw-lon', type=float, help='Southwest longitude')
    parser.add_argument('--ne-lat', type=float, help='Northeast latitude')
    parser.add_argument('--ne-lon', type=float, help='Northeast longitude')
    
    # Required parameters
    parser.add_argument('--date', required=True, 
                       help='Date (YYYY-MM-DD) or date range (YYYY-MM-DD,YYYY-MM-DD)')
    
    # Optional parameters
    parser.add_argument('--bands', nargs='+', default=['B02', 'B03', 'B04', 'B8A', 'B11', 'B12'],
                       help='Bands to download (default: B02 B03 B04 B8A B11 B12)')
    parser.add_argument('--output-dir', 
                       default=os.getenv('DEFAULT_OUTPUT_DIR', './data/downloaded'), 
                       help='Output directory (default: ./data/downloaded or DEFAULT_OUTPUT_DIR from .env)')
    parser.add_argument('--max-results', type=int, 
                       default=int(os.getenv('DEFAULT_MAX_RESULTS', '50')),
                       help='Maximum number of results (default: 50 or DEFAULT_MAX_RESULTS from .env)')
    parser.add_argument('--list-only', action='store_true',
                       help='Only list available data, do not download')
    
    args = parser.parse_args()
    
    # Parse coordinates
    if args.coords_file:
        sw_coords, ne_coords = parse_coordinates_file(args.coords_file)
        print(f"📍 Loaded coordinates from {args.coords_file}")
    elif args.coords_direct:
        sw_coords = (args.coords_direct[0], args.coords_direct[1])
        ne_coords = (args.coords_direct[2], args.coords_direct[3])
    elif all([args.sw_lat, args.sw_lon, args.ne_lat, args.ne_lon]):
        sw_coords = (args.sw_lat, args.sw_lon)
        ne_coords = (args.ne_lat, args.ne_lon)
    else:
        print("❌ Error: Must provide coordinates either via file or direct input")
        return 1
    
    print(f"📍 Southwest: {sw_coords}")
    print(f"📍 Northeast: {ne_coords}")
    
    # Initialize downloader
    try:
        downloader = HLSDownloader()
    except Exception:
        return 1
    
    # List or download data
    if args.list_only:
        downloader.list_available_data(sw_coords, ne_coords, args.date, args.max_results)
    else:
        downloaded_files = downloader.download_hls_data(
            sw_coords=sw_coords,
            ne_coords=ne_coords,
            date=args.date,
            bands=args.bands,
            output_dir=args.output_dir,
            max_results=args.max_results
        )
        
        if downloaded_files:
            print(f"\n✓ Downloaded {len(downloaded_files)} files:")
            for file_path in downloaded_files:
                print(f"   {file_path}")
        else:
            print("\n❌ No files were downloaded")
            return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 