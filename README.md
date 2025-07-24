# HLS Sentinel-2 Data Downloader

A Python script for downloading HLS Sentinel-2 Multi-spectral Instrument Surface Reflectance data from NASA Earthdata using the [earthaccess library](https://github.com/nsidc/earthaccess).

## Features

- Download HLS Sentinel-2 data (.tif files) from NASA Earthdata
- Configurable parameters: coordinates, date/date range, and bands
- Support for coordinates from files or direct input
- Filter by specific bands (B02, B03, B04, B8A, B11, B12, etc.)
- Command-line interface and programmatic usage
- List available data without downloading

## Prerequisites

1. **NASA Earthdata Account**: You need a free NASA Earthdata account to access the data
   - Sign up at: https://urs.earthdata.nasa.gov/users/new

2. **Python Requirements**: Install the required packages
   ```bash
   pip install -r requirements.txt
   ```

3. **Authentication Setup** (Optional but Recommended): Create a `.env` file for automatic authentication
   ```bash
   # Copy the example file and edit with your credentials
   cp env.example .env
   # Edit .env with your NASA Earthdata username and password
   ```

## Quick Start

### Command Line Usage

1. **Download data using coordinates file:**
   ```bash
   python src/download_hls_data.py \
     --coords-file data/sentinel/region-0/coordinates.txt \
     --date 2024-07-15 \
     --bands B02 B03 B04
   ```

2. **Download data using direct coordinates:**
   ```bash
   python src/download_hls_data.py \
     --sw-lat 45.24301 --sw-lon 78.44504 \
     --ne-lat 45.2912 --ne-lon 78.49116 \
     --date 2024-07-15 \
     --bands B8A B11 B12
   ```

3. **Download data for a date range:**
   ```bash
   python src/download_hls_data.py \
     --coords-file coordinates.txt \
     --date "2024-07-01,2024-07-31" \
     --bands B02 B03 B04
   ```

4. **List available data without downloading:**
   ```bash
   python src/download_hls_data.py \
     --coords-file coordinates.txt \
     --date 2024-07-15 \
     --list-only
   ```

### Programmatic Usage

```python
from src.download_hls_data import HLSDownloader

# Initialize downloader (handles authentication)
downloader = HLSDownloader()

# Download data
downloaded_files = downloader.download_hls_data(
    sw_coords=(45.24301, 78.44504),  # Southwest (lat, lon)
    ne_coords=(45.2912, 78.49116),   # Northeast (lat, lon)
    date="2024-07-15",               # Date or "start,end" range
    bands=["B02", "B03", "B04"],     # Bands to download
    output_dir="./data/downloaded",   # Output directory
    max_results=10                   # Max files to download
)

print(f"Downloaded {len(downloaded_files)} files")
```

## Parameters

### Coordinates

**Option 1: Coordinates File**
Create a text file with southwest and northeast coordinates:
```
HLS Sentinel-2 Multi-spectral Instrument Surface Reflectance Daily Global 30m v2.0

sw 45.24301,78.44504
ne 45.2912,78.49116
```

**Option 2: Direct Input**
Provide coordinates directly via command line arguments:
- `--sw-lat`, `--sw-lon`: Southwest latitude and longitude
- `--ne-lat`, `--ne-lon`: Northeast latitude and longitude

### Date

- **Single date**: `2024-07-15` (YYYY-MM-DD format)
- **Date range**: `"2024-07-01,2024-07-31"` (start,end format)

### Bands

Available HLS Sentinel-2 bands:
- `B02`: Blue (490 nm)
- `B03`: Green (560 nm) 
- `B04`: Red (665 nm)
- `B05`: Red Edge 1 (705 nm)
- `B06`: Red Edge 2 (740 nm)
- `B07`: Red Edge 3 (783 nm)
- `B8A`: NIR Narrow (865 nm)
- `B11`: SWIR 1 (1610 nm)
- `B12`: SWIR 2 (2190 nm)

**Default bands**: `B02 B03 B04 B8A B11 B12`

## Examples

### Example 1: Basic RGB Download
```bash
python src/download_hls_data.py \
  --coords-file coordinates.txt \
  --date 2024-07-15 \
  --bands B02 B03 B04 \
  --output-dir ./rgb_data
```

### Example 2: NIR and SWIR Analysis
```bash
python src/download_hls_data.py \
  --sw-lat 45.24 --sw-lon 78.44 \
  --ne-lat 45.29 --ne-lon 78.49 \
  --date 2024-07-15 \
  --bands B8A B11 B12 \
  --output-dir ./nir_swir_data
```

### Example 3: Time Series Data
```bash
python src/download_hls_data.py \
  --coords-file coordinates.txt \
  --date "2024-06-01,2024-08-31" \
  --bands B03 B04 B8A \
  --max-results 100 \
  --output-dir ./time_series
```

### Example 4: Check Available Data
```bash
python src/download_hls_data.py \
  --coords-file coordinates.txt \
  --date "2024-07-01,2024-07-31" \
  --list-only
```

## Command Line Options

```
usage: download_hls_data.py [-h] (--coords-file COORDS_FILE | --coords-direct SW_LAT SW_LON NE_LAT NE_LON)
                           [--sw-lat SW_LAT] [--sw-lon SW_LON] [--ne-lat NE_LAT] [--ne-lon NE_LON]
                           --date DATE [--bands BANDS [BANDS ...]] [--output-dir OUTPUT_DIR]
                           [--max-results MAX_RESULTS] [--list-only]

Download HLS Sentinel-2 data from NASA Earthdata

options:
  -h, --help            show this help message and exit
  --coords-file COORDS_FILE
                        Path to coordinates file (sw/ne format)
  --coords-direct SW_LAT SW_LON NE_LAT NE_LON
                        Direct coordinates: sw_lat sw_lon ne_lat ne_lon
  --sw-lat SW_LAT       Southwest latitude
  --sw-lon SW_LON       Southwest longitude
  --ne-lat NE_LAT       Northeast latitude
  --ne-lon NE_LON       Northeast longitude
  --date DATE           Date (YYYY-MM-DD) or date range (YYYY-MM-DD,YYYY-MM-DD)
  --bands BANDS [BANDS ...]
                        Bands to download (default: B02 B03 B04 B8A B11 B12)
  --output-dir OUTPUT_DIR
                        Output directory (default: ./data/downloaded)
  --max-results MAX_RESULTS
                        Maximum number of results (default: 50)
  --list-only           Only list available data, do not download
```

## Output

Downloaded files will be saved as GeoTIFF (.tif) files with names like:
```
HLS.S30.T43TGL.2024196T053649.v2.0.B02.tif
HLS.S30.T43TGL.2024196T053649.v2.0.B03.tif
HLS.S30.T43TGL.2024196T053649.v2.0.B04.tif
```

Where:
- `S30`: Sentinel-2 data
- `T43TGL`: MGRS tile identifier
- `2024196`: Year and day of year
- `B02`, `B03`, etc.: Band identifier

## Authentication

The script supports two authentication methods:

### Method 1: Environment Variables (Recommended)
Create a `.env` file in the project root:
```bash
# Copy the template and edit with your credentials
cp env.example .env
```

Edit the `.env` file:
```
EARTHDATA_USERNAME=your_username
EARTHDATA_PASSWORD=your_password

# Optional defaults
DEFAULT_OUTPUT_DIR=./data/downloaded
DEFAULT_MAX_RESULTS=50
```

### Method 2: Interactive Login
If no `.env` file is found, the script will prompt for credentials:
- Username/Email
- Password

Credentials are securely stored by the earthaccess library for future use.

## Troubleshooting

1. **Authentication Issues**: Ensure you have a valid NASA Earthdata account
2. **No Data Found**: Try a different date range or expand your geographic area
3. **Network Issues**: Check your internet connection and NASA Earthdata service status
4. **Dependencies**: Make sure all required packages are installed: `pip install -r requirements.txt`

## Dataset Information

- **Full Name**: HLS Sentinel-2 Multi-spectral Instrument Surface Reflectance Daily Global 30m v2.0
- **Short Name**: HLSS30
- **Spatial Resolution**: 30 meters
- **Temporal Resolution**: Daily (when available)
- **Data Format**: GeoTIFF
- **Coordinate System**: UTM projection

For more information about HLS data, visit: https://lpdaac.usgs.gov/products/hlss30v002/

## References

- [earthaccess library](https://github.com/nsidc/earthaccess)
- [NASA Earthdata](https://earthdata.nasa.gov/)
- [HLS Dataset Documentation](https://lpdaac.usgs.gov/products/hlss30v002/) # skyterra-crop-classification
