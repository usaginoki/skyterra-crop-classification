#!/usr/bin/env python3
"""
Assemble 18-band multi-temporal satellite images using rasterio (no QGIS required).

This script takes a directory containing 3 time folders (t0, t1, t2), each with 6 band files
(B02, B03, B04, B8A, B11, B12), and assembles them into a single 18-band GeoTIFF image.

Usage:
    python assemble_rasterio.py <input_directory> [--bbox sw_lat,sw_lon,ne_lat,ne_lon] [--output output.tif]

Author: Generated for crop-classification project
Requires: rasterio, numpy (lightweight dependencies)
"""

import os
import sys
import argparse
import glob
from pathlib import Path
import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.mask import mask
from rasterio.windows import from_bounds
from rasterio.transform import from_bounds as transform_from_bounds
from rasterio.crs import CRS
from rasterio.warp import transform_bounds
from shapely.geometry import box
import warnings

# Suppress rasterio warnings
warnings.filterwarnings("ignore", category=rasterio.errors.NotGeoreferencedWarning)


def parse_coordinates_file(coords_file):
    """Parse coordinates.txt file to extract bounding box."""
    print(f"Looking for coordinates file: {coords_file}")
    if not os.path.exists(coords_file):
        print(f"Coordinates file not found: {coords_file}")
        return None
    
    print(f"Reading coordinates from: {coords_file}")
    sw_coords = None
    ne_coords = None
    
    with open(coords_file, 'r') as f:
        for line in f:
            line = line.strip()
            print(f"  Line: {line}")
            if line.startswith('sw '):
                coords = line.split(' ')[1].split(',')
                sw_coords = (float(coords[0]), float(coords[1]))  # lat, lon
                print(f"  Parsed SW: {sw_coords} (lat, lon)")
            elif line.startswith('ne '):
                coords = line.split(' ')[1].split(',')
                ne_coords = (float(coords[0]), float(coords[1]))  # lat, lon
                print(f"  Parsed NE: {ne_coords} (lat, lon)")
    
    if sw_coords and ne_coords:
        # Create standard bbox format (minx, miny, maxx, maxy) for transform_bounds
        # sw_coords = (lat, lon), ne_coords = (lat, lon)
        bbox = (sw_coords[1], sw_coords[0], ne_coords[1], ne_coords[0])  # (minx, miny, maxx, maxy)
        print(f"Converted to WGS84 bbox (minx, miny, maxx, maxy): {bbox}")
        return bbox
    
    print("Could not parse valid coordinates")
    return None


def transform_bbox_to_crs(bbox, src_crs, dst_crs):
    """Transform bounding box from one CRS to another."""
    print(f"Transforming bbox from {src_crs} to {dst_crs}")
    print(f"Input bbox: {bbox}")
    
    try:
        # Transform the bounding box
        transformed_bbox = transform_bounds(src_crs, dst_crs, *bbox)
        print(f"Transformed bbox: {transformed_bbox}")
        return transformed_bbox
    except Exception as e:
        print(f"Error transforming bbox: {e}")
        return None


def find_band_files(time_folder, bands=['B02', 'B03', 'B04', 'B8A', 'B11', 'B12']):
    """Find band files in a time folder."""
    band_files = {}
    print(f"  Looking for bands in: {time_folder}")
    
    for band in bands:
        # Look for files containing the band name
        pattern = os.path.join(time_folder, f"*{band}.tiff")
        files = glob.glob(pattern)
        if not files:
            # Try .tif extension
            pattern = os.path.join(time_folder, f"*{band}.tif")
            files = glob.glob(pattern)
        
        if files:
            band_files[band] = files[0]  # Take first match
            print(f"    Found {band}: {os.path.basename(files[0])}")
        else:
            print(f"    Warning: Could not find {band} file in {time_folder}")
    
    print(f"  Total bands found: {len(band_files)}/6")
    return band_files


def get_raster_bounds_and_crs(raster_path):
    """Get bounds and CRS from a raster file."""
    with rasterio.open(raster_path) as src:
        return src.bounds, src.crs, src.transform, src.shape


def clip_raster_to_bbox(raster_path, bbox, output_path=None):
    """Clip a raster to the specified bounding box."""
    with rasterio.open(raster_path) as src:
        # Create a polygon from the bounding box
        bbox_geom = box(*bbox)
        
        # Clip the raster
        clipped_data, clipped_transform = mask(src, [bbox_geom], crop=True)
        
        # Update metadata
        clipped_meta = src.meta.copy()
        clipped_meta.update({
            'height': clipped_data.shape[1],
            'width': clipped_data.shape[2],
            'transform': clipped_transform
        })
        
        if output_path:
            with rasterio.open(output_path, 'w', **clipped_meta) as dst:
                dst.write(clipped_data)
            return output_path, clipped_meta
        else:
            return clipped_data, clipped_meta, clipped_transform


def read_and_clip_band(file_path, bbox=None):
    """Read a band file and optionally clip it to bbox."""
    with rasterio.open(file_path) as src:
        if bbox:
            # Create window from bounds
            window = from_bounds(*bbox, src.transform)
            data = src.read(1, window=window)
            # Get the transform for the windowed data
            transform = rasterio.windows.transform(window, src.transform)
            return data, src.meta, transform, window
        else:
            data = src.read(1)
            return data, src.meta, src.transform, None


def assemble_multitemporal_image(input_dir, output_path, bbox=None):
    """Main function to assemble multi-temporal image using rasterio."""
    
    # Check if input directory exists
    if not os.path.exists(input_dir):
        raise ValueError(f"Input directory does not exist: {input_dir}")
    
    # Look for time folders
    time_folders = ['t0', 't1', 't2']
    bands = ['B02', 'B03', 'B04', 'B8A', 'B11', 'B12']
    all_band_files = []
    
    # Collect all band files in order
    for time_folder in time_folders:
        time_path = os.path.join(input_dir, time_folder)
        if not os.path.exists(time_path):
            raise ValueError(f"Time folder does not exist: {time_path}")
        
        print(f"Processing {time_folder}...")
        band_files = find_band_files(time_path)
        
        if len(band_files) != 6:
            print(f"Warning: Expected 6 bands in {time_folder}, found {len(band_files)}")
        
        # Add bands in correct order
        for band in bands:
            if band in band_files:
                all_band_files.append(band_files[band])
            else:
                print(f"Error: Missing {band} in {time_folder}")
                raise ValueError(f"Missing required band {band} in {time_folder}")
    
    if len(all_band_files) != 18:
        raise ValueError(f"Expected 18 bands, found {len(all_band_files)}")
    
    # Get reference metadata from first file
    print(f"Reading reference metadata from: {os.path.basename(all_band_files[0])}")
    with rasterio.open(all_band_files[0]) as ref_src:
        ref_meta = ref_src.meta.copy()
        ref_crs = ref_src.crs
        
        print(f"Reference image CRS: {ref_crs}")
        print(f"Reference image bounds: {ref_src.bounds}")
        print(f"Reference image shape: {ref_src.height} x {ref_src.width}")
        
        # Handle bounding box
        target_bbox = None
        if bbox is None:
            coords_file = os.path.join(input_dir, 'coordinates.txt')
            bbox_wgs84 = parse_coordinates_file(coords_file)
            if bbox_wgs84:
                print(f"Using bounding box from coordinates.txt: {bbox_wgs84}")
                target_bbox = transform_bbox_to_crs(bbox_wgs84, 'EPSG:4326', ref_crs)
            else:
                print("No bounding box provided, using full image extent")
        else:
            print(f"Using provided bounding box: {bbox}")
            target_bbox = transform_bbox_to_crs(bbox, 'EPSG:4326', ref_crs)
        
        # Calculate window and output metadata
        if target_bbox:
            print(f"Target bbox in image CRS: {target_bbox}")
            window = from_bounds(*target_bbox, ref_src.transform)
            print(f"Calculated window: {window}")
            
            # Get dimensions from the window but create exact transform for target bbox
            windowed_height = int(window.height)
            windowed_width = int(window.width)
            
            if windowed_width <= 0 or windowed_height <= 0:
                print(f"ERROR: Invalid window dimensions! Target bbox may be outside image bounds")
                raise ValueError("Bounding box is outside the image extent")
            
            # Create transform that maps exactly to the target bbox bounds
            windowed_transform = transform_from_bounds(*target_bbox, windowed_width, windowed_height)
            
            print(f"Output dimensions: {windowed_width} x {windowed_height}")
            print(f"Output will have exact bounds: {target_bbox}")
        else:
            window = None
            windowed_transform = ref_src.transform
            windowed_height = ref_src.height
            windowed_width = ref_src.width
            print(f"Using full image extent: {windowed_width} x {windowed_height}")
    
    # Update metadata for 18-band output
    output_meta = ref_meta.copy()
    output_meta.update({
        'count': 18,
        'height': windowed_height,
        'width': windowed_width,
        'transform': windowed_transform,
        'dtype': 'uint16',
        'nodata': 0,  # Use 0 as nodata for uint16
        'compress': 'lzw'
    })
    
    # Create output directory if needed
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    print(f"Creating 18-band image: {output_path}")
    print(f"Output dimensions: {windowed_width} x {windowed_height} pixels")
    
    # Write the multi-band image
    with rasterio.open(output_path, 'w', **output_meta) as dst:
        for i, band_file in enumerate(all_band_files, 1):
            print(f"Processing band {i}/18: {os.path.basename(band_file)}")
            
            with rasterio.open(band_file) as src:
                if window:
                    data = src.read(1, window=window)
                else:
                    data = src.read(1)
                
                dst.write(data, i)
                
                # Set band description
                time_idx = (i - 1) // 6
                band_idx = (i - 1) % 6
                band_name = bands[band_idx]
                dst.set_band_description(i, f"t{time_idx}_{band_name}")
    
    print(f"Successfully created 18-band image: {output_path}")
    
    # Print output statistics
    with rasterio.open(output_path) as src:
        print(f"Output CRS: {src.crs}")
        print(f"Output bounds: {src.bounds}")
        print(f"Output shape: {src.height} x {src.width} x {src.count}")
    
    return output_path


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Assemble 18-band multi-temporal satellite images (rasterio version)')
    parser.add_argument('input_dir', help='Input directory containing t0, t1, t2 folders')
    parser.add_argument('--bbox', help='Bounding box as sw_lat,sw_lon,ne_lat,ne_lon')
    parser.add_argument('--output', default='assembled_18band.tif', help='Output file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        # Parse bounding box if provided
        bbox = None
        if args.bbox:
            coords = [float(x) for x in args.bbox.split(',')]
            if len(coords) != 4:
                raise ValueError("Bounding box must have 4 coordinates: sw_lat,sw_lon,ne_lat,ne_lon")
            bbox = (coords[1], coords[0], coords[3], coords[2])  # Convert to standard (minx, miny, maxx, maxy)
            print(f"Using provided bounding box: {bbox}")
        
        # Assemble the image
        result = assemble_multitemporal_image(args.input_dir, args.output, bbox)
        print(f"Assembly complete! Output saved to: {result}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main() 