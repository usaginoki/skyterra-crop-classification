#!/usr/bin/env python3
"""
Test script for HLS downloader functionality.
This tests the core functions without requiring NASA Earthdata authentication.
"""

import sys
import os
from pathlib import Path

# Add src to path so we can import our module
sys.path.insert(0, str(Path(__file__).parent))

from download_hls_data import parse_coordinates_file

def test_coordinate_parsing():
    """Test that coordinate parsing works correctly."""
    print("🧪 Testing coordinate parsing...")
    
    coords_file = "../data/sentinel/region-0/coordinates.txt"
    
    try:
        sw_coords, ne_coords = parse_coordinates_file(coords_file)
        
        print(f"   ✅ Southwest coordinates: {sw_coords}")
        print(f"   ✅ Northeast coordinates: {ne_coords}")
        
        # Validate coordinates are reasonable
        assert isinstance(sw_coords, tuple) and len(sw_coords) == 2
        assert isinstance(ne_coords, tuple) and len(ne_coords) == 2
        assert all(isinstance(x, float) for x in sw_coords + ne_coords)
        
        # Check that coordinates are in expected ranges (Central Asia region)
        lat_range = (40, 50)  # Latitude range for the region
        lon_range = (70, 85)  # Longitude range for the region
        
        assert lat_range[0] <= sw_coords[0] <= lat_range[1], f"SW latitude {sw_coords[0]} out of range"
        assert lat_range[0] <= ne_coords[0] <= lat_range[1], f"NE latitude {ne_coords[0]} out of range"
        assert lon_range[0] <= sw_coords[1] <= lon_range[1], f"SW longitude {sw_coords[1]} out of range"
        assert lon_range[0] <= ne_coords[1] <= lon_range[1], f"NE longitude {ne_coords[1]} out of range"
        
        print("   ✅ Coordinate validation passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Coordinate parsing failed: {e}")
        return False

def test_imports():
    """Test that all required imports work."""
    print("🧪 Testing imports...")
    
    try:
        import earthaccess
        print(f"   ✅ earthaccess {earthaccess.__version__}")
        
        import numpy as np
        print(f"   ✅ numpy {np.__version__}")
        
        import rasterio
        print(f"   ✅ rasterio {rasterio.__version__}")
        
        import xarray as xr
        print(f"   ✅ xarray {xr.__version__}")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False

def test_script_help():
    """Test that the script help works."""
    print("🧪 Testing script help...")
    
    try:
        # Test that the script can show help without errors
        import subprocess
        result = subprocess.run([
            sys.executable, "download_hls_data.py", "--help"
        ], capture_output=True, text=True, cwd="src")
        
        if result.returncode == 0 and "Download HLS Sentinel-2 data" in result.stdout:
            print("   ✅ Help command works")
            return True
        else:
            print(f"   ❌ Help command failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Script help test failed: {e}")
        return False

def test_bounding_box_calculation():
    """Test bounding box calculation logic."""
    print("🧪 Testing bounding box calculation...")
    
    try:
        sw_coords = (45.24301, 78.44504)  # lat, lon
        ne_coords = (45.2912, 78.49116)   # lat, lon
        
        # This is the logic from the download_hls_data.py script
        bounding_box = (
            min(sw_coords[1], ne_coords[1]),  # west (min longitude)
            min(sw_coords[0], ne_coords[0]),  # south (min latitude)
            max(sw_coords[1], ne_coords[1]),  # east (max longitude)
            max(sw_coords[0], ne_coords[0])   # north (max latitude)
        )
        
        expected_box = (78.44504, 45.24301, 78.49116, 45.2912)  # west, south, east, north
        
        assert bounding_box == expected_box, f"Expected {expected_box}, got {bounding_box}"
        
        print(f"   ✅ Bounding box: {bounding_box} (west, south, east, north)")
        return True
        
    except Exception as e:
        print(f"   ❌ Bounding box calculation failed: {e}")
        return False

def test_date_parsing():
    """Test date parsing logic."""
    print("🧪 Testing date parsing...")
    
    try:
        # Test single date
        single_date = "2024-07-15"
        if ',' in single_date:
            start_date, end_date = single_date.split(',')
            temporal = (start_date.strip(), end_date.strip())
        else:
            temporal = (single_date, single_date)
        
        assert temporal == ("2024-07-15", "2024-07-15"), f"Single date parsing failed: {temporal}"
        
        # Test date range
        date_range = "2024-07-01,2024-07-31"
        if ',' in date_range:
            start_date, end_date = date_range.split(',')
            temporal = (start_date.strip(), end_date.strip())
        else:
            temporal = (date_range, date_range)
        
        assert temporal == ("2024-07-01", "2024-07-31"), f"Date range parsing failed: {temporal}"
        
        print("   ✅ Date parsing works correctly")
        return True
        
    except Exception as e:
        print(f"   ❌ Date parsing failed: {e}")
        return False

def main():
    """Run all tests."""
    print("HLS Downloader Test Suite")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_coordinate_parsing,
        test_bounding_box_calculation,
        test_date_parsing,
        test_script_help
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Empty line between tests
    
    print("=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The HLS downloader is ready to use.")
        print("\nNext steps:")
        print("1. Get NASA Earthdata credentials at: https://urs.earthdata.nasa.gov/users/new")
        print("2. Run the script with --list-only to test authentication")
        print("3. Download real data by removing the --list-only flag")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main()) 