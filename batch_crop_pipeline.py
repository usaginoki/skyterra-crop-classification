#!/usr/bin/env python3
"""
Batch Crop Classification Pipeline Processor

This script processes multiple field coordinates from a CSV file using the automated
crop classification pipeline. It supports different processing orders, limits, 
error handling, and provides detailed progress tracking with ETA.
"""

import os
import sys
import csv
import argparse
import subprocess
import time
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BatchCropPipeline:
    """Batch processor for automated crop classification pipeline."""
    
    def __init__(self, start_date: str, end_date: str, data_file: str, output_folder: str,
                 order: str = "forward", limit: Optional[int] = None, bbox_size: float = 0.01):
        """
        Initialize the batch processor.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            data_file: Path to CSV file with field coordinates
            output_folder: Base output directory for all processed fields
            order: Processing order ('forward', 'backward', 'random')
            limit: Maximum number of fields to process (None for unlimited)
            bbox_size: Bounding box size for each field (default: 0.01)
        """
        self.start_date = start_date
        self.end_date = end_date
        self.data_file = data_file
        self.output_folder = output_folder
        self.order = order.lower()
        self.limit = limit
        self.bbox_size = bbox_size
        
        # Validate inputs
        self._validate_inputs()
        
        # Load and prepare data
        self.fields_data = self._load_fields_data()
        self.total_fields = len(self.fields_data)
        
        # Processing statistics
        self.processed_count = 0
        self.success_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.start_time = None
        self.failed_fields = []
        self.successful_fields = []
        
        # Create output directory
        os.makedirs(self.output_folder, exist_ok=True)
        
        logger.info(f"🚀 Batch Crop Pipeline Processor initialized")
        logger.info(f"   Data file: {self.data_file}")
        logger.info(f"   Date range: {self.start_date} to {self.end_date}")
        logger.info(f"   Output folder: {self.output_folder}")
        logger.info(f"   Processing order: {self.order}")
        logger.info(f"   Fields to process: {self.total_fields}")
        logger.info(f"   Limit: {self.limit if self.limit else 'unlimited'}")
        logger.info(f"   Bounding box size: ±{self.bbox_size}°")
    
    def _validate_inputs(self):
        """Validate input parameters."""
        # Validate dates
        try:
            start_dt = datetime.strptime(self.start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(self.end_date, '%Y-%m-%d')
            if start_dt >= end_dt:
                raise ValueError("Start date must be before end date")
        except ValueError as e:
            if "time data" in str(e):
                raise ValueError("Dates must be in YYYY-MM-DD format")
            raise
        
        # Validate data file
        if not os.path.exists(self.data_file):
            raise FileNotFoundError(f"Data file not found: {self.data_file}")
        
        # Validate order
        if self.order not in ['forward', 'backward', 'random']:
            raise ValueError("Order must be 'forward', 'backward', or 'random'")
        
        # Validate limit
        if self.limit is not None and self.limit <= 0:
            raise ValueError("Limit must be a positive integer")
        
        # Validate bbox size
        if self.bbox_size <= 0 or self.bbox_size > 1:
            raise ValueError("Bounding box size must be between 0 and 1 degrees")
    
    def _load_fields_data(self) -> List[Dict]:
        """Load and validate fields data from CSV file."""
        logger.info(f"📊 Loading fields data from {self.data_file}")
        
        try:
            # Read CSV file
            df = pd.read_csv(self.data_file)
            
            # Validate required columns
            required_cols = ['Polygon Number', 'Y Coordinate', 'X Coordinate']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Convert to list of dictionaries
            fields_data = []
            for _, row in df.iterrows():
                try:
                    field_data = {
                        'polygon_number': int(row['Polygon Number']),
                        'lat': float(row['Y Coordinate']),
                        'lon': float(row['X Coordinate']),
                        'class': str(row.get('Class', 'Unknown'))
                    }
                    
                    # Validate coordinates
                    if not (-90 <= field_data['lat'] <= 90):
                        logger.warning(f"Invalid latitude for polygon {field_data['polygon_number']}: {field_data['lat']}")
                        continue
                    if not (-180 <= field_data['lon'] <= 180):
                        logger.warning(f"Invalid longitude for polygon {field_data['polygon_number']}: {field_data['lon']}")
                        continue
                    
                    fields_data.append(field_data)
                
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid row: {row.to_dict()} - Error: {e}")
                    continue
            
            logger.info(f"   ✓ Loaded {len(fields_data)} valid fields")
            
            # Apply order and limit
            fields_data = self._apply_order_and_limit(fields_data)
            
            return fields_data
            
        except Exception as e:
            logger.error(f"Failed to load fields data: {e}")
            raise
    
    def _apply_order_and_limit(self, fields_data: List[Dict]) -> List[Dict]:
        """Apply processing order and limit to fields data."""
        # Apply order
        if self.order == 'backward':
            fields_data = list(reversed(fields_data))
        elif self.order == 'random':
            random.shuffle(fields_data)
        # 'forward' is default order, no change needed
        
        # Apply limit
        if self.limit is not None:
            fields_data = fields_data[:self.limit]
            logger.info(f"   ✓ Limited to {len(fields_data)} fields ({self.order} order)")
        else:
            logger.info(f"   ✓ Processing all {len(fields_data)} fields ({self.order} order)")
        
        return fields_data
    
    def _calculate_eta(self, processed: int, total: int, elapsed_time: float) -> str:
        """Calculate estimated time of arrival."""
        if processed == 0:
            return "calculating..."
        
        avg_time_per_field = elapsed_time / processed
        remaining_fields = total - processed
        remaining_time = avg_time_per_field * remaining_fields
        
        eta_datetime = datetime.now() + timedelta(seconds=remaining_time)
        
        # Format remaining time
        if remaining_time < 60:
            time_str = f"{remaining_time:.0f}s"
        elif remaining_time < 3600:
            time_str = f"{remaining_time/60:.1f}m"
        else:
            time_str = f"{remaining_time/3600:.1f}h"
        
        return f"{time_str} (ETA: {eta_datetime.strftime('%H:%M:%S')})"
    
    def _generate_output_path(self, polygon_number: int) -> str:
        """Generate output path for a field."""
        output_name = f"{polygon_number}_{self.start_date}_{self.end_date}"
        return os.path.join(self.output_folder, output_name)
    
    def _process_single_field(self, field_data: Dict) -> Tuple[bool, str]:
        """
        Process a single field through the crop pipeline.
        
        Returns:
            Tuple of (success, message)
        """
        polygon_number = field_data['polygon_number']
        lat = field_data['lat']
        lon = field_data['lon']
        class_name = field_data['class']
        
        output_path = self._generate_output_path(polygon_number)
        
        logger.info(f"🌾 Processing field {polygon_number} ({class_name})")
        logger.info(f"   Coordinates: ({lat}, {lon})")
        logger.info(f"   Output: {output_path}")
        
        # Check if already processed
        if os.path.exists(output_path):
            assembled_file = os.path.join(output_path, 'assembled_18band.tif')
            if os.path.exists(assembled_file):
                logger.info(f"   ⏭️  Field {polygon_number} already processed, skipping")
                return True, "Already processed"
        
        # Find the automated pipeline script
        script_paths = [
            
            os.path.join('skyterra-crop-classification', 'src', 'automated_crop_data_pipeline.py'),
            os.path.join('src', 'automated_crop_data_pipeline.py'),
            'automated_crop_data_pipeline.py',
            os.path.join('./')
        ]
        
        script_path = None
        for path in script_paths:
            if os.path.exists(path):
                script_path = path
                break
        
        if not script_path:
            error_msg = "automated_crop_data_pipeline.py not found"
            logger.error(f"   ❌ {error_msg}")
            return False, error_msg
        
        # Construct command
        cmd = [
            sys.executable, script_path,
            '--center-lat', str(lat),
            '--center-lon', str(lon),
            '--start-date', self.start_date,
            '--end-date', self.end_date,
            '--bbox-size', str(self.bbox_size),
            '--output-dir', output_path
        ]
        
        logger.debug(f"   Running: {' '.join(cmd)}")
        
        try:
            # Run the pipeline with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=1800  # 30 minute timeout
            )
            
            logger.info(f"   ✅ Field {polygon_number} processed successfully")
            
            # Log relevant output
            if result.stdout and '✅ PIPELINE COMPLETED SUCCESSFULLY!' in result.stdout:
                logger.debug(f"   Pipeline output: Success")
            
            return True, "Success"
            
        except subprocess.TimeoutExpired:
            error_msg = "Pipeline timed out (30 minutes)"
            logger.error(f"   ⏰ Field {polygon_number}: {error_msg}")
            return False, error_msg
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Pipeline failed with exit code {e.returncode}"
            logger.error(f"   ❌ Field {polygon_number}: {error_msg}")
            
            # Log error details
            if e.stderr:
                logger.debug(f"   Error: {e.stderr.strip()}")
            if e.stdout:
                logger.debug(f"   Output: {e.stdout.strip()}")
            
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"   💥 Field {polygon_number}: {error_msg}")
            return False, error_msg
    
    def _print_progress(self, current: int, total: int, field_data: Dict, success: bool, message: str):
        """Print progress information with ETA."""
        polygon_number = field_data['polygon_number']
        elapsed_time = time.time() - self.start_time
        eta = self._calculate_eta(current, total, elapsed_time)
        
        status_icon = "✅" if success else "❌"
        progress_bar = self._create_progress_bar(current, total)
        
        print(f"\n{'='*80}")
        print(f"{status_icon} Field {polygon_number} | {current}/{total} ({current/total*100:.1f}%)")
        print(f"Progress: {progress_bar}")
        print(f"Status: {message}")
        print(f"Success: {self.success_count} | Failed: {self.failed_count} | Skipped: {self.skipped_count}")
        print(f"Elapsed: {elapsed_time/60:.1f}m | ETA: {eta}")
        print(f"{'='*80}")
    
    def _create_progress_bar(self, current: int, total: int, width: int = 50) -> str:
        """Create a visual progress bar."""
        filled = int(width * current / total)
        bar = '█' * filled + '░' * (width - filled)
        return f"[{bar}] {current}/{total}"
    
    def run_batch_processing(self):
        """Run the batch processing pipeline."""
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 STARTING BATCH CROP PIPELINE PROCESSING")
        logger.info(f"{'='*80}")
        
        self.start_time = time.time()
        
        try:
            for i, field_data in enumerate(self.fields_data, 1):
                polygon_number = field_data['polygon_number']
                
                try:
                    # Process the field
                    success, message = self._process_single_field(field_data)
                    
                    # Update statistics
                    self.processed_count += 1
                    if success:
                        if "Already processed" in message:
                            self.skipped_count += 1
                        else:
                            self.success_count += 1
                        self.successful_fields.append(polygon_number)
                    else:
                        self.failed_count += 1
                        self.failed_fields.append({
                            'polygon_number': polygon_number,
                            'error': message,
                            'coordinates': (field_data['lat'], field_data['lon'])
                        })
                    
                    # Print progress
                    self._print_progress(i, self.total_fields, field_data, success, message)
                    
                except KeyboardInterrupt:
                    logger.warning(f"\n⚠️  Processing interrupted by user")
                    break
                    
                except Exception as e:
                    logger.error(f"Unexpected error processing field {polygon_number}: {e}")
                    self.failed_count += 1
                    self.failed_fields.append({
                        'polygon_number': polygon_number,
                        'error': str(e),
                        'coordinates': (field_data['lat'], field_data['lon'])
                    })
                    continue
            
            # Generate completion report
            self._generate_completion_report()
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            raise
    
    def _generate_completion_report(self):
        """Generate and display completion report."""
        total_time = time.time() - self.start_time
        
        print(f"\n{'='*80}")
        print(f"📊 BATCH PROCESSING COMPLETION REPORT")
        print(f"{'='*80}")
        print(f"📅 Date Range: {self.start_date} to {self.end_date}")
        print(f"📁 Output Folder: {self.output_folder}")
        print(f"⏱️  Total Processing Time: {total_time/60:.1f} minutes")
        print(f"📊 Processing Statistics:")
        print(f"   • Total Fields: {self.total_fields}")
        print(f"   • Processed: {self.processed_count}")
        print(f"   • Successful: {self.success_count}")
        print(f"   • Skipped (already done): {self.skipped_count}")
        print(f"   • Failed: {self.failed_count}")
        print(f"   • Success Rate: {(self.success_count + self.skipped_count)/self.processed_count*100:.1f}%")
        
        if self.successful_fields:
            print(f"\n✅ Successfully Processed Fields:")
            for i, polygon_num in enumerate(self.successful_fields[:10]):  # Show first 10
                print(f"   {polygon_num}")
            if len(self.successful_fields) > 10:
                print(f"   ... and {len(self.successful_fields) - 10} more")
        
        if self.failed_fields:
            print(f"\n❌ Failed Fields:")
            for failure in self.failed_fields[:10]:  # Show first 10 failures
                print(f"   Field {failure['polygon_number']}: {failure['error']}")
                print(f"     Coordinates: {failure['coordinates']}")
            if len(self.failed_fields) > 10:
                print(f"   ... and {len(self.failed_fields) - 10} more failures")
        
        # Performance metrics
        if self.processed_count > 0:
            avg_time = total_time / self.processed_count
            print(f"\n📈 Performance Metrics:")
            print(f"   • Average time per field: {avg_time/60:.2f} minutes")
            print(f"   • Processing rate: {self.processed_count/(total_time/3600):.1f} fields/hour")
        
        print(f"\n📋 Detailed logs saved to: batch_pipeline.log")
        print(f"{'='*80}")
        
        # Log summary
        logger.info(f"Batch processing completed:")
        logger.info(f"  Total: {self.total_fields}, Processed: {self.processed_count}")
        logger.info(f"  Success: {self.success_count}, Skipped: {self.skipped_count}, Failed: {self.failed_count}")
        logger.info(f"  Total time: {total_time/60:.1f} minutes")


def main():
    """Main entry point with command line interface."""
    parser = argparse.ArgumentParser(
        description="Batch Crop Classification Pipeline Processor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python batch_crop_pipeline.py 2024-03-01 2024-06-30 data.csv ./batch_output

  # With custom order and limit
  python batch_crop_pipeline.py 2024-03-01 2024-06-30 data.csv ./batch_output --order random --limit 50

  # Backward processing with custom bounding box
  python batch_crop_pipeline.py 2024-01-01 2024-12-31 fields.csv ./results --order backward --bbox-size 0.02

  # Random order for testing
  python batch_crop_pipeline.py 2024-05-01 2024-07-31 test_fields.csv ./test_output --order random --limit 10
        """
    )
    
    # Required arguments
    parser.add_argument('start_date', 
                       help='Start date in YYYY-MM-DD format')
    parser.add_argument('end_date',
                       help='End date in YYYY-MM-DD format')
    parser.add_argument('data_file',
                       help='Path to CSV file with field coordinates')
    parser.add_argument('output_folder',
                       help='Base output directory for all processed fields')
    
    # Optional arguments
    parser.add_argument('--order', choices=['forward', 'backward', 'random'], 
                       default='forward',
                       help='Processing order (default: forward)')
    parser.add_argument('--limit', type=int,
                       help='Number of fields to process (default: unlimited)')
    parser.add_argument('--bbox-size', type=float, default=0.01,
                       help='Bounding box size in decimal degrees (default: 0.01)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize and run batch processor
        processor = BatchCropPipeline(
            start_date=args.start_date,
            end_date=args.end_date,
            data_file=args.data_file,
            output_folder=args.output_folder,
            order=args.order,
            limit=args.limit,
            bbox_size=args.bbox_size
        )
        
        processor.run_batch_processing()
        return 0
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Processing interrupted by user")
        return 1
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit(main()) 