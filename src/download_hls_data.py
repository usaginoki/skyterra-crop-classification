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
from typing import List, Tuple, Optional, Dict
import argparse
from dotenv import load_dotenv
import re
from collections import defaultdict

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
    
    def _extract_granule_id(self, result) -> str:
        """
        Extract granule identifier from search result.
        
        HLS granule names follow pattern: HLS.S30.T42UXB.2025188T061639.v2.0.B11.tif
        Granule ID is everything except the band: HLS.S30.T42UXB.2025188T061639.v2.0
        """
        try:
            # Get the data URLs from the earthaccess result object
            if hasattr(result, 'data_links') and result.data_links():
                # Use the first data link to extract granule ID
                first_url = result.data_links()[0]
            elif hasattr(result, 'data') and result.data:
                # Alternative way to access data URLs
                first_url = result.data[0] if isinstance(result.data, list) else str(result.data)
            else:
                # Fallback: try to get URLs from the result object
                first_url = str(result)
            
            # Extract filename from URL
            if 'http' in first_url:
                # Extract filename from URL path
                filename = first_url.split('/')[-1]
            else:
                filename = first_url
            
            # Remove .tif extension if present
            if filename.endswith('.tif'):
                filename = filename[:-4]
            
            # Split by dots and remove the last part (band identifier)
            parts = filename.split('.')
            if len(parts) >= 2:
                # Check if last part looks like a band (B02, B03, etc.) or other identifier
                last_part = parts[-1]
                if (last_part.startswith('B') and len(last_part) <= 4) or last_part in ['Fmask', 'VAA', 'VZA', 'SAA', 'SZA']:
                    # Remove the band/mask identifier
                    granule_id = '.'.join(parts[:-1])
                else:
                    # Keep all parts if last part doesn't look like a band
                    granule_id = filename
            else:
                granule_id = filename
                
            return granule_id
            
        except Exception as e:
            print(f"Warning: Could not extract granule ID from result: {e}")
            # Fallback to using string representation
            return f"unknown_granule_{hash(str(result)) % 10000}"
    
    def _group_results_by_granule(self, results) -> Dict[str, List]:
        """Group search results by granule identifier."""
        granule_groups = defaultdict(list)
        
        for result in results:
            granule_id = self._extract_granule_id(result)
            granule_groups[granule_id].append(result)
        
        return dict(granule_groups)
    
    def _select_granules_interactive(self, granule_groups: Dict[str, List]) -> List[str]:
        """Allow user to interactively select granules."""
        granule_ids = list(granule_groups.keys())
        
        print(f"\n🔍 Found {len(granule_ids)} granules:")
        for i, granule_id in enumerate(granule_ids, 1):
            band_count = len(granule_groups[granule_id])
            print(f"   {i}. {granule_id} ({band_count} bands)")
        
        print(f"\nOptions:")
        print(f"   - Enter granule numbers (1-{len(granule_ids)}) separated by commas to select specific granules")
        print(f"   - Press Enter to download all granules")
        print(f"   - Type 'abort' to cancel")
        
        while True:
            try:
                selection = input(f"\nYour choice: ").strip()
                
                if selection.lower() == 'abort':
                    print("❌ Download aborted by user")
                    return []
                
                if not selection:
                    # Download all granules
                    return granule_ids
                
                # Parse selected numbers
                selected_numbers = [int(x.strip()) for x in selection.split(',')]
                
                # Validate numbers
                if all(1 <= num <= len(granule_ids) for num in selected_numbers):
                    selected_granules = [granule_ids[num - 1] for num in selected_numbers]
                    return selected_granules
                else:
                    print(f"❌ Invalid selection. Please enter numbers between 1 and {len(granule_ids)}")
                    
            except ValueError:
                print("❌ Invalid input. Please enter numbers separated by commas or press Enter for all")
            except KeyboardInterrupt:
                print("\n❌ Download aborted by user")
                return []
    
    def download_hls_data(
        self,
        sw_coords: Tuple[float, float],
        ne_coords: Tuple[float, float], 
        date: str,
        bands: List[str],
        output_dir: str = "./data",
        max_results: int = 50,
        auto_download: bool = False
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
            auto_download: If True, automatically download all granules without user interaction
            
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
            
            print(f"📊 Found {len(results)} total files")
            
            if not results:
                print("❌ No data found for the specified criteria")
                return []
            
            # Filter results by bands if specified
            if bands:
                filtered_results = []
                for result in results:
                    # Extract filename from the result object to check bands
                    try:
                        # Get the data URLs from the earthaccess result object
                        if hasattr(result, 'data_links') and result.data_links():
                            # Check all data links for this result
                            urls = result.data_links()
                        elif hasattr(result, 'data') and result.data:
                            # Alternative way to access data URLs
                            urls = result.data if isinstance(result.data, list) else [result.data]
                        else:
                            # Skip if we can't get URLs
                            continue
                        
                        # Check if any URL contains the requested bands
                        for url in urls:
                            filename = url.split('/')[-1] if 'http' in str(url) else str(url)
                            for band in bands:
                                if f".{band}." in filename:
                                    filtered_results.append(result)
                                    break
                            else:
                                continue
                            break  # Found a matching band, no need to check more URLs
                            
                    except Exception as e:
                        print(f"Warning: Could not check bands for result: {e}")
                        continue
                
                results = filtered_results
                print(f"📊 After band filtering: {len(results)} files")
            
            if not results:
                print("❌ No files found matching the specified bands")
                return []
            
            # Group results by granule
            granule_groups = self._group_results_by_granule(results)
            num_granules = len(granule_groups)
            
            print(f"📊 Organized into {num_granules} granules")
            
            # Check if more than 3 granules - abort if so
            if num_granules > 3:
                print(f"❌ Error: Found {num_granules} granules, but maximum allowed is 3")
                print("   Please narrow your search criteria (smaller area or date range)")
                return []
            
            # Select granules to download
            if auto_download:
                selected_granule_ids = [list(granule_groups.keys())[0]]
                print(f"🤖 Auto-download mode: downloading first granule only ({selected_granule_ids[0]})")
            else:
                selected_granule_ids = self._select_granules_interactive(granule_groups)
            
            if not selected_granule_ids:
                print("❌ No granules selected for download")
                return []
            
            # Create main output directory
            os.makedirs(output_dir, exist_ok=True)
            
            all_downloaded_files = []
            
            # Download each selected granule to its own folder
            for granule_id in selected_granule_ids:
                granule_results = granule_groups[granule_id]
                
                # Create granule-specific folder
                granule_folder = os.path.join(output_dir, granule_id)
                os.makedirs(granule_folder, exist_ok=True)
                
                print(f"\n⬇️  Downloading granule: {granule_id}")
                print(f"   Files: {len(granule_results)}")
                print(f"   Folder: {granule_folder}")
                
                # Download files for this granule
                try:
                    downloaded_files = earthaccess.download(granule_results, granule_folder)
                    all_downloaded_files.extend(downloaded_files)
                    print(f"   ✓ Downloaded {len(downloaded_files)} files")
                except Exception as e:
                    print(f"   ❌ Error downloading granule {granule_id}: {e}")
                    continue
            
            print(f"\n✓ Successfully downloaded {len(all_downloaded_files)} files total")
            print(f"📁 Files organized in {len(selected_granule_ids)} granule folders under: {output_dir}")
            
            return all_downloaded_files
            
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
  # Download specific bands for a date using coordinate file (interactive mode)
  python download_hls_data.py --coords-file data/sentinel/region-0/coordinates.txt --date 2025-01-15 --bands B02 B03 B04

  # Download data using direct coordinates (interactive mode)
  python download_hls_data.py --sw-lat 45.24301 --sw-lon 78.44504 --ne-lat 45.2912 --ne-lon 78.49116 --date 2025-01-15

  # Download data for a date range with automatic download (no user interaction)
  python download_hls_data.py --coords-file coords.txt --date "2025-01-01,2025-01-31" --bands B8A B11 B12 --auto-download

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
    parser.add_argument('--auto-download', action='store_true',
                       help='Automatically download all granules without user interaction')
    
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
            max_results=args.max_results,
            auto_download=args.auto_download
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