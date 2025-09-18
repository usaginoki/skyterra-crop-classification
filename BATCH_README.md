# Batch Crop Classification Pipeline Processor

This script processes multiple field coordinates from a CSV file using the automated crop classification pipeline. It provides comprehensive error handling, progress tracking, and detailed reporting.

## 🚀 Quick Start

```bash
# Basic usage - process all fields in your CSV
python3 batch_crop_pipeline.py 2024-03-01 2024-06-30 data.csv ./batch_output

# Test with limited fields in random order
python3 batch_crop_pipeline.py 2024-03-01 2024-06-30 data.csv ./test_output --order random --limit 5

# Production run with custom settings
python3 batch_crop_pipeline.py 2024-01-01 2024-12-31 data.csv ./production_output --bbox-size 0.02
```

## 📋 Input Requirements

### CSV Data File Format
Your CSV file must contain these columns:
- `Polygon Number`: Unique identifier for each field
- `Y Coordinate`: Latitude in decimal degrees
- `X Coordinate`: Longitude in decimal degrees
- `Class`: (Optional) Crop type or land use class

Example CSV structure:
```csv
Polygon Number,Class,Y Coordinate,X Coordinate
1,Sorghum,51.024681,71.841594
2,Other,51.015214,71.839089
3,Winter Wheat,50.951843,71.909225
```

## 🔧 Command Line Usage

```bash
python3 batch_crop_pipeline.py <start_date> <end_date> <data_file> <output_folder> [options]
```

### Required Arguments
- `start_date`: Start date in YYYY-MM-DD format
- `end_date`: End date in YYYY-MM-DD format  
- `data_file`: Path to CSV file with field coordinates
- `output_folder`: Base directory for all processed fields

### Optional Arguments
- `--order {forward,backward,random}`: Processing order (default: forward)
- `--limit NUMBER`: Maximum fields to process (default: unlimited)
- `--bbox-size FLOAT`: Bounding box size in degrees (default: 0.01)
- `--verbose, -v`: Enable detailed logging

## 📁 Output Structure

For each field, the script creates a directory named: `{polygon_number}_{start_date}_{end_date}`

```
batch_output/
├── 1_2024-03-01_2024-06-30/
│   ├── assembled_18band.tif        # Final 18-band image
│   ├── coordinates.txt             # Generated bounding box
│   ├── downloads/                  # Raw downloaded data
│   │   ├── t0/
│   │   ├── t1/
│   │   └── t2/
│   └── organized/                  # Organized for assembly
│       ├── t0/
│       ├── t1/
│       └── t2/
├── 2_2024-03-01_2024-06-30/
│   └── ... (same structure)
└── batch_pipeline.log              # Detailed processing log
```

## 🔄 Processing Orders

### Forward (default)
Processes fields in the order they appear in the CSV file.
```bash
python3 batch_crop_pipeline.py 2024-03-01 2024-06-30 data.csv ./output
```

### Backward
Processes fields in reverse order (last to first).
```bash
python3 batch_crop_pipeline.py 2024-03-01 2024-06-30 data.csv ./output --order backward
```

### Random
Processes fields in random order (useful for testing and sampling).
```bash
python3 batch_crop_pipeline.py 2024-03-01 2024-06-30 data.csv ./output --order random --limit 10
```

## 📊 Progress Tracking

The script provides real-time progress updates with:
- **Progress bar**: Visual representation of completion
- **ETA calculation**: Estimated time of completion
- **Success/failure counts**: Running statistics
- **Performance metrics**: Processing rate and timing

Example output:
```
================================================================================
✅ Field 15 | 15/100 (15.0%)
Progress: [███████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 15/100
Status: Success
Success: 12 | Failed: 2 | Skipped: 1
Elapsed: 45.2m | ETA: 4.5h (ETA: 18:30:45)
================================================================================
```

## 🛡️ Error Handling

### Automatic Recovery
- **Skip already processed**: Detects existing output and skips completed fields
- **Timeout handling**: 30-minute timeout per field to prevent hanging
- **Continue on failure**: Failed fields don't stop the entire batch
- **Detailed error logging**: All errors logged with context

### Common Issues and Solutions

**Authentication errors**: Ensure NASA Earthdata credentials are configured
```bash
# Check if you have a .env file in skyterra-crop-classification/
cp skyterra-crop-classification/env.example skyterra-crop-classification/.env
# Edit with your NASA Earthdata credentials
```

**No satellite data found**: Try historical dates (2022-2024) instead of future dates
```bash
# Good: Historical dates
python3 batch_crop_pipeline.py 2023-06-01 2023-08-31 data.csv ./output

# Avoid: Future dates
python3 batch_crop_pipeline.py 2025-06-01 2025-08-31 data.csv ./output
```

**Network timeouts**: Use smaller limits for testing, then scale up
```bash
# Test with small batch first
python3 batch_crop_pipeline.py 2023-06-01 2023-08-31 data.csv ./test --limit 3
```

## 📈 Completion Report

After processing, you'll get a comprehensive report:

```
================================================================================
📊 BATCH PROCESSING COMPLETION REPORT
================================================================================
📅 Date Range: 2024-03-01 to 2024-06-30
📁 Output Folder: ./batch_output
⏱️  Total Processing Time: 125.4 minutes
📊 Processing Statistics:
   • Total Fields: 100
   • Processed: 100
   • Successful: 85
   • Skipped (already done): 10
   • Failed: 5
   • Success Rate: 95.0%

✅ Successfully Processed Fields:
   1, 3, 4, 5, 7, 8, 9, 11, 12, 14...

❌ Failed Fields:
   Field 23: No satellite data found
     Coordinates: (45.123, 78.456)
   Field 67: Authentication failed
     Coordinates: (51.234, 72.345)

📈 Performance Metrics:
   • Average time per field: 1.25 minutes
   • Processing rate: 48.0 fields/hour
================================================================================
```

## 🧪 Testing and Development

### Start Small
Always test with a small subset first:
```bash
# Test with 3 random fields
python3 batch_crop_pipeline.py 2023-06-01 2023-08-31 data.csv ./test --order random --limit 3 --verbose
```

### Validate Your Data
Check your CSV file structure:
```bash
# View first few lines
head -10 data.csv

# Check for required columns
python3 -c "import pandas as pd; df = pd.read_csv('data.csv'); print(df.columns.tolist()); print(f'Rows: {len(df)}')"
```

### Monitor Progress
- Watch the console output for real-time updates
- Check `batch_pipeline.log` for detailed information
- Use `--verbose` flag for maximum detail during testing

## 🔧 Advanced Configuration

### Custom Bounding Box Size
Adjust the area around each coordinate:
```bash
# Larger area (2km radius)
python3 batch_crop_pipeline.py 2023-06-01 2023-08-31 data.csv ./output --bbox-size 0.02

# Smaller area (500m radius)  
python3 batch_crop_pipeline.py 2023-06-01 2023-08-31 data.csv ./output --bbox-size 0.005
```

### Resume Interrupted Processing
The script automatically skips already completed fields, so you can safely restart:
```bash
# If interrupted, just run the same command again
python3 batch_crop_pipeline.py 2023-06-01 2023-08-31 data.csv ./output
```

### Parallel Processing (Manual)
For very large datasets, you can split processing:
```bash
# Process first half
python3 batch_crop_pipeline.py 2023-06-01 2023-08-31 data.csv ./output_part1 --limit 500

# Process second half  
python3 batch_crop_pipeline.py 2023-06-01 2023-08-31 data.csv ./output_part2 --order backward --limit 500
```

## 🛠️ Dependencies

Ensure you have all required packages:
```bash
# Install from requirements
pip install -r skyterra-crop-classification/requirements.txt

# Key dependencies
pip install pandas earthaccess rasterio numpy
```

## 📞 Troubleshooting

### Check Logs
```bash
# View recent log entries
tail -50 batch_pipeline.log

# Search for errors
grep -i error batch_pipeline.log
```

### Validate Setup
```bash
# Test the underlying pipeline manually
cd skyterra-crop-classification
python3 src/automated_crop_data_pipeline.py --center-lat 51.024681 --center-lon 71.841594 --start-date 2023-06-01 --end-date 2023-08-31 --output-dir ./test_single
```

### Performance Tips
- Start with historical dates (2022-2024) for better data availability
- Use `--limit` for testing and development
- Consider processing during off-peak hours for better download speeds
- Monitor disk space - each field generates ~100-500MB of data

## 📋 Example Workflows

### Development/Testing
```bash
# 1. Test with 3 random fields
python3 batch_crop_pipeline.py 2023-06-01 2023-08-31 data.csv ./test --order random --limit 3 --verbose

# 2. If successful, try 10 fields
python3 batch_crop_pipeline.py 2023-06-01 2023-08-31 data.csv ./test10 --limit 10

# 3. Process full dataset
python3 batch_crop_pipeline.py 2023-06-01 2023-08-31 data.csv ./production
```

### Production Processing
```bash
# 1. Run overnight batch
nohup python3 batch_crop_pipeline.py 2023-06-01 2023-08-31 data.csv ./production > batch_output.log 2>&1 &

# 2. Monitor progress
tail -f batch_output.log

# 3. Check completion
grep "COMPLETION REPORT" batch_output.log
```

This batch processor makes it easy to scale from single field testing to processing hundreds of fields automatically while providing comprehensive monitoring and error handling. 