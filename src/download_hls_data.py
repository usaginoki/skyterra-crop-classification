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
import logging

# Load environment variables from .env file
load_dotenv()

# Add verbose logging support
def setup_logging(verbose=False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


class HLSDownloader:
    """Enhanced class to handle HLS Sentinel-2 data downloads from NASA Earthdata."""
    
    def __init__(self, verbose=False):
        """Initialize the downloader and authenticate with NASA Earthdata."""
        self.logger = setup_logging(verbose)
        self.logger.info("🔄 Initializing HLS Downloader...")
        
        try:
            # Try to authenticate using environment variables first
            username = os.getenv('EARTHDATA_USERNAME')
            password = os.getenv('EARTHDATA_PASSWORD')
            
            if username and password:
                self.logger.info("🔐 Using credentials from environment variables...")
                # Set environment variables for earthaccess to use
                os.environ['EARTHDATA_USERNAME'] = username
                os.environ['EARTHDATA_PASSWORD'] = password
                earthaccess.login(strategy='environment')
                self.logger.info("✓ Successfully authenticated with NASA Earthdata (from .env)")
            else:
                self.logger.info("🔐 No credentials found in environment, using interactive login...")
                self.logger.info("   (Tip: Create a .env file with EARTHDATA_USERNAME and EARTHDATA_PASSWORD)")
                earthaccess.login()
                self.logger.info("✓ Successfully authenticated with NASA Earthdata (interactive)")
                
        except Exception as e:
            self.logger.error(f"❌ Authentication failed: {e}")
            self.logger.error("Please ensure you have valid NASA Earthdata credentials")
            self.logger.error("Option 1: Create a .env file with your credentials (see env.example)")
            self.logger.error("Option 2: Use interactive login (script will prompt you)")
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
            self.logger.warning(f"Warning: Could not extract granule ID from result: {e}")
            # Fallback to using string representation
            return f"unknown_granule_{hash(str(result)) % 10000}"
    
    def _group_results_by_granule(self, results) -> Dict[str, List]:
        """Group search results by granule identifier."""
        granule_groups = defaultdict(list)
        
        for result in results:
            granule_id = self._extract_granule_id(result)
            granule_groups[granule_id].append(result)
        
        return dict(granule_groups)
    
    def _group_file_urls_by_granule(self, file_urls) -> Dict[str, List]:
        """Group file URLs by granule identifier."""
        granule_groups = defaultdict(list)
        
        for url, result in file_urls:
            # Extract granule ID from the filename in the URL
            filename = url.split('/')[-1] if 'http' in url else url
            
            # Remove .tif extension if present
            if filename.endswith('.tif'):
                filename = filename[:-4]
            
            # Split by dots and remove the last part (band identifier)
            parts = filename.split('.')
            if len(parts) >= 2:
                # Check if last part looks like a band or other identifier
                last_part = parts[-1]
                if (last_part.startswith('B') and len(last_part) <= 4) or last_part in ['Fmask', 'VAA', 'VZA', 'SAA', 'SZA']:
                    # Remove the band/mask identifier
                    granule_id = '.'.join(parts[:-1])
                else:
                    # Keep all parts if last part doesn't look like a band
                    granule_id = filename
            else:
                granule_id = filename
            
            granule_groups[granule_id].append((url, result))
        
        return dict(granule_groups)
    
    def _select_granules_interactive(self, granule_groups: Dict[str, List]) -> List[str]:
        """Allow user to interactively select granules."""
        granule_ids = list(granule_groups.keys())
        
        print(f"\n🔍 Found {len(granule_ids)} granules:")
        for i, granule_id in enumerate(granule_ids, 1):
            file_count = len(granule_groups[granule_id])
            print(f"   {i}. {granule_id} ({file_count} files)")
        
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
        Enhanced download method with better error handling and logging.
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
        
        self.logger.info(f"🔍 Searching NASA Earthdata for HLS Sentinel-2 data...")
        self.logger.info(f"   Bounding box: {bounding_box}")
        self.logger.info(f"   Date range: {temporal}")
        self.logger.info(f"   Bands: {bands}")
        
        try:
            # Search for HLS Sentinel-2 data
            results = earthaccess.search_data(
                short_name='HLSS30',  # HLS Sentinel-2 short name
                bounding_box=bounding_box,
                temporal=temporal,
                count=max_results
            )
            
            self.logger.info(f"📊 Found {len(results)} granule objects")
            
            if not results:
                self.logger.error("❌ No data found for the specified criteria")
                self.logger.error(f"   Search parameters:")
                self.logger.error(f"   - Bounding box: {bounding_box}")
                self.logger.error(f"   - Date range: {temporal}")
                self.logger.error(f"   - Bands: {bands}")
                self.logger.error("💡 Suggestions:")
                self.logger.error("   - Try a larger bounding box")
                self.logger.error("   - Try a different date range (historical dates work better)")
                self.logger.error("   - Check if the area has satellite coverage")
                return []
            
            # Extract all individual file URLs from granule objects
            all_file_urls = []
            for result in results:
                try:
                    # Get the data URLs from the earthaccess result object
                    if hasattr(result, 'data_links') and result.data_links():
                        urls = result.data_links()
                    elif hasattr(result, 'data') and result.data:
                        urls = result.data if isinstance(result.data, list) else [result.data]
                    else:
                        continue
                    
                    # Add all URLs from this granule
                    for url in urls:
                        all_file_urls.append((str(url), result))  # Store URL and original result object
                        
                except Exception as e:
                    self.logger.warning(f"Warning: Could not extract URLs from result: {e}")
                    continue
            
            self.logger.info(f"📊 Total individual files available: {len(all_file_urls)}")
            
            # Filter individual files by bands if specified
            if bands:
                filtered_file_urls = []
                for url, result in all_file_urls:
                    filename = url.split('/')[-1] if 'http' in url else url
                    for band in bands:
                        if f".{band}." in filename:
                            filtered_file_urls.append((url, result))
                            break
                
                all_file_urls = filtered_file_urls
                self.logger.info(f"📊 After band filtering: {len(all_file_urls)} files")
            
            if not all_file_urls:
                self.logger.error("❌ No files found matching the specified bands")
                return []
            
            # Group file URLs by granule
            granule_groups = self._group_file_urls_by_granule(all_file_urls)
            num_granules = len(granule_groups)
            
            self.logger.info(f"📊 Organized into {num_granules} granules")
            
            # Select granules to download
            if auto_download:
                # In auto-download mode, download only the first granule
                selected_granule_ids = [list(granule_groups.keys())[0]]
                self.logger.info(f"🤖 Auto-download mode: downloading first granule only ({selected_granule_ids[0]})")
                if num_granules > 1:
                    self.logger.info(f"   Found {num_granules} granules total, selecting the first one")
            else:
                # Interactive mode - keep the 3 granule limit for user safety
                if num_granules > 3:
                    self.logger.error(f"❌ Error: Found {num_granules} granules, but maximum allowed is 3 in interactive mode")
                    self.logger.error("   Please narrow your search criteria (smaller area or date range)")
                    self.logger.error("   Or use --auto-download to automatically select the first granule")
                    return []
                    
                selected_granule_ids = self._select_granules_interactive(granule_groups)
            
            if not selected_granule_ids:
                self.logger.error("❌ No granules selected for download")
                return []
            
            # Create main output directory
            os.makedirs(output_dir, exist_ok=True)
            
            all_downloaded_files = []
            
            # Download each selected granule to its own folder
            for granule_id in selected_granule_ids:
                granule_file_urls = granule_groups[granule_id]
                
                # Extract just the URLs for downloading
                urls_to_download = [url for url, result in granule_file_urls]
                
                # Create granule-specific folder
                granule_folder = os.path.join(output_dir, granule_id)
                os.makedirs(granule_folder, exist_ok=True)
                
                self.logger.info(f"\n⬇️  Downloading granule: {granule_id}")
                self.logger.info(f"   Files: {len(urls_to_download)}")
                self.logger.info(f"   Folder: {granule_folder}")
                
                # Download files for this granule
                try:
                    downloaded_files = earthaccess.download(urls_to_download, granule_folder)
                    all_downloaded_files.extend(downloaded_files)
                    self.logger.info(f"   ✓ Downloaded {len(downloaded_files)} files")
                except Exception as e:
                    self.logger.error(f"   ❌ Error downloading granule {granule_id}: {e}")
                    continue
            
            self.logger.info(f"\n✓ Successfully downloaded {len(all_downloaded_files)} files total")
            self.logger.info(f"📁 Files organized in {len(selected_granule_ids)} granule folders under: {output_dir}")
            
            return all_downloaded_files
            
        except Exception as e:
            self.logger.error(f"❌ Error during search/download: {e}")
            self.logger.error(f"   Exception type: {type(e).__name__}")
            import traceback
            self.logger.debug(f"   Full traceback: {traceback.format_exc()}")
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
        
        self.logger.info(f"🔍 Listing available HLS Sentinel-2 data...")
        self.logger.info(f"   Bounding box: {bounding_box}")
        self.logger.info(f"   Date range: {temporal}")
        
        try:
            results = earthaccess.search_data(
                short_name='HLSS30',
                bounding_box=bounding_box,
                temporal=temporal,
                count=max_results
            )
            
            self.logger.info(f"\n📊 Found {len(results)} granules:")
            for i, result in enumerate(results[:max_results], 1):
                self.logger.info(f"   {i}. {result}")
                
        except Exception as e:
            self.logger.error(f"❌ Error during search: {e}")


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
    """Enhanced main function with better error handling."""
    parser = argparse.ArgumentParser(
        description="Download HLS Sentinel-2 data from NASA Earthdata (Enhanced)",
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
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging for debugging')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    
    # Parse coordinates
    if args.coords_file:
        sw_coords, ne_coords = parse_coordinates_file(args.coords_file)
        logger.info(f"📍 Loaded coordinates from {args.coords_file}")
    elif args.coords_direct:
        sw_coords = (args.coords_direct[0], args.coords_direct[1])
        ne_coords = (args.coords_direct[2], args.coords_direct[3])
    elif all([args.sw_lat, args.sw_lon, args.ne_lat, args.ne_lon]):
        sw_coords = (args.sw_lat, args.sw_lon)
        ne_coords = (args.ne_lat, args.ne_lon)
    else:
        logger.error("❌ Error: Must provide coordinates either via file or direct input")
        return 1
    
    logger.info(f"📍 Southwest: {sw_coords}")
    logger.info(f"📍 Northeast: {ne_coords}")
    
    # Initialize downloader with verbose flag
    try:
        downloader = HLSDownloader(verbose=args.verbose)
    except Exception as e:
        logger.error(f"❌ Failed to initialize downloader: {e}")
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
            logger.info(f"\n✓ Downloaded {len(downloaded_files)} files:")
            for file_path in downloaded_files:
                logger.info(f"   {file_path}")
        else:
            logger.info("\n❌ No files were downloaded")
            return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 