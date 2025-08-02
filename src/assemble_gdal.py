#!/usr/bin/env python3
"""
Assemble 18-band multi-temporal satellite images using GDAL.

This script takes a directory containing 3 time folders (t0, t1, t2), each with 6 band files
(B02, B03, B04, B8A, B11, B12), and assembles them into a single 18-band GeoTIFF image.

Usage:
    python assemble_gdal.py <input_directory> [--bbox sw_lat,sw_lon,ne_lat,ne_lon] [--output output.tif]

Author: Generated for crop-classification project
Requires: gdal, osr, numpy
"""

import os
import sys
import argparse
import glob
from pathlib import Path
import numpy as np
import tempfile
import shutil

try:
    from osgeo import gdal, osr
    gdal.UseExceptions()
except ImportError:
    import gdal
    import osr
    gdal.UseExceptions()


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
        # Create standard bbox format (minx, miny, maxx, maxy) for transformation
        # sw_coords = (lat, lon), ne_coords = (lat, lon)
        bbox = (sw_coords[1], sw_coords[0], ne_coords[1], ne_coords[0])  # (minx, miny, maxx, maxy)
        print(f"Converted to WGS84 bbox (minx, miny, maxx, maxy): {bbox}")
        return bbox
    
    print("Could not parse valid coordinates")
    return None


def transform_bbox_to_crs(bbox, src_crs_text, dst_crs_text):
    """Transform bounding box from one CRS to another using GDAL/OSR."""
    print(f"Transforming bbox from {src_crs_text} to {dst_crs_text}")
    print(f"Input bbox: {bbox}")
    
    try:
        # Create coordinate transformation
        src_crs = osr.SpatialReference()
        dst_crs = osr.SpatialReference()
        
        if src_crs_text.startswith('EPSG:'):
            src_crs.ImportFromEPSG(int(src_crs_text.split(':')[1]))
        else:
            src_crs.ImportFromWkt(src_crs_text)
            
        if dst_crs_text.startswith('EPSG:'):
            dst_crs.ImportFromEPSG(int(dst_crs_text.split(':')[1]))
        else:
            dst_crs.ImportFromWkt(dst_crs_text)
        
        transform = osr.CoordinateTransformation(src_crs, dst_crs)
        
        # Transform corner points
        minx, miny, maxx, maxy = bbox
        
        # Transform corners
        min_corner = transform.TransformPoint(minx, miny)
        max_corner = transform.TransformPoint(maxx, maxy)
        
        transformed_bbox = (min_corner[0], min_corner[1], max_corner[0], max_corner[1])
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


def get_raster_info(raster_path):
    """Get information from a raster file using GDAL."""
    dataset = gdal.Open(raster_path, gdal.GA_ReadOnly)
    if dataset is None:
        raise ValueError(f"Could not open raster: {raster_path}")
    
    # Get geotransform and projection
    geotransform = dataset.GetGeoTransform()
    projection = dataset.GetProjection()
    width = dataset.RasterXSize
    height = dataset.RasterYSize
    
    # Calculate bounds
    minx = geotransform[0]
    maxy = geotransform[3]
    maxx = minx + width * geotransform[1]
    miny = maxy + height * geotransform[5]
    bounds = (minx, miny, maxx, maxy)
    
    dataset = None  # Close dataset
    return bounds, projection, geotransform, (height, width)


def clip_raster_gdal(input_path, output_path, bbox):
    """Clip a raster using GDAL Warp with bounding box."""
    print(f"Clipping {os.path.basename(input_path)} to bbox: {bbox}")
    
    # Use gdal.Warp to clip
    warp_options = gdal.WarpOptions(
        outputBounds=bbox,
        cropToCutline=True,
        dstNodata=0
    )
    
    result = gdal.Warp(output_path, input_path, options=warp_options)
    if result is None:
        raise RuntimeError(f"Failed to clip raster: {input_path}")
    
    result = None  # Close dataset
    return output_path


def assemble_multitemporal_image(input_dir, output_path, bbox=None):
    """Main function to assemble multi-temporal image using GDAL."""
    
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
    ref_bounds, ref_projection, ref_geotransform, ref_shape = get_raster_info(all_band_files[0])
    
    print(f"Reference image projection: {ref_projection[:100]}...")
    print(f"Reference image bounds: {ref_bounds}")
    print(f"Reference image shape: {ref_shape[0]} x {ref_shape[1]}")
    
    # Handle bounding box
    target_bbox = None
    if bbox is None:
        coords_file = os.path.join(input_dir, 'coordinates.txt')
        bbox_wgs84 = parse_coordinates_file(coords_file)
        if bbox_wgs84:
            print(f"Using bounding box from coordinates.txt: {bbox_wgs84}")
            target_bbox = transform_bbox_to_crs(bbox_wgs84, 'EPSG:4326', ref_projection)
        else:
            print("No bounding box provided, using full image extent")
    else:
        print(f"Using provided bounding box: {bbox}")
        target_bbox = transform_bbox_to_crs(bbox, 'EPSG:4326', ref_projection)
    
    # Create temporary directory for processing
    temp_dir = tempfile.mkdtemp(prefix='gdal_assemble_')
    try:
        clipped_files = []
        
        # Process each band file
        if target_bbox:
            print(f"Target bbox in image CRS: {target_bbox}")
            print("Clipping individual bands...")
            
            for i, band_file in enumerate(all_band_files):
                temp_clipped = os.path.join(temp_dir, f"clipped_band_{i+1:02d}.tif")
                clip_raster_gdal(band_file, temp_clipped, target_bbox)
                clipped_files.append(temp_clipped)
        else:
            clipped_files = all_band_files
        
        print(f"Creating 18-band image: {output_path}")
        
        # Get dimensions from the first (possibly clipped) file
        first_bounds, first_projection, first_geotransform, first_shape = get_raster_info(clipped_files[0])
        output_width = first_shape[1]
        output_height = first_shape[0]
        
        print(f"Output dimensions: {output_width} x {output_height} pixels")
        
        # Create output directory if needed
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Create the multi-band output file
        driver = gdal.GetDriverByName('GTiff')
        output_dataset = driver.Create(
            output_path,
            output_width,
            output_height,
            18,  # 18 bands
            gdal.GDT_UInt16,
            options=['COMPRESS=LZW', 'TILED=YES']
        )
        
        if output_dataset is None:
            raise RuntimeError(f"Could not create output file: {output_path}")
        
        # Set geotransform and projection
        output_dataset.SetGeoTransform(first_geotransform)
        output_dataset.SetProjection(first_projection)
        
        # Copy each band
        for i, band_file in enumerate(clipped_files):
            print(f"Processing band {i+1}/18: {os.path.basename(all_band_files[i])}")
            
            # Open source band
            src_dataset = gdal.Open(band_file, gdal.GA_ReadOnly)
            if src_dataset is None:
                raise RuntimeError(f"Could not open band file: {band_file}")
            
            src_band = src_dataset.GetRasterBand(1)
            data = src_band.ReadAsArray()
            
            # Write to output band
            output_band = output_dataset.GetRasterBand(i + 1)
            output_band.WriteArray(data)
            output_band.SetNoDataValue(0)
            
            # Set band description
            time_idx = i // 6
            band_idx = i % 6
            band_name = bands[band_idx]
            output_band.SetDescription(f"t{time_idx}_{band_name}")
            
            # Clean up
            src_dataset = None
        
        # Close output dataset
        output_dataset = None
        
    finally:
        # Clean up temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    print(f"Successfully created 18-band image: {output_path}")
    
    # Print output statistics
    final_bounds, final_projection, final_geotransform, final_shape = get_raster_info(output_path)
    final_dataset = gdal.Open(output_path, gdal.GA_ReadOnly)
    print(f"Output projection: {final_projection[:100]}...")
    print(f"Output bounds: {final_bounds}")
    print(f"Output shape: {final_shape[0]} x {final_shape[1]} x {final_dataset.RasterCount}")
    final_dataset = None
    
    return output_path


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Assemble 18-band multi-temporal satellite images (GDAL version)')
    parser.add_argument('input_dir', help='Input directory containing t0, t1, t2 folders')
    parser.add_argument('--bbox', help='Bounding box as sw_lat,sw_lon,ne_lat,ne_lon')
    parser.add_argument('--output', default='assembled_18band_gdal.tif', help='Output file path')
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
