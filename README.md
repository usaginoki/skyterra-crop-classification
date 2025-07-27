# HLS Sentinel-2 Data Downloader

A Python script for downloading HLS Sentinel-2 Multi-spectral Instrument Surface Reflectance data from NASA Earthdata using the [earthaccess library](https://github.com/nsidc/earthaccess).

## Features

- Download HLS Sentinel-2 data (.tif files) from NASA Earthdata
- **Granule organization**: Each granule downloaded to separate folders
- **Interactive granule selection**: Choose specific granules or download all
- **Smart limits**: Automatic abort if more than 3 granules detected
- Configurable parameters: coordinates, date/date range, and bands
- Support for coordinates from files or direct input
- Filter by specific bands (B02, B03, B04, B8A, B11, B12, etc.)
- Command-line interface and programmatic usage
- List available data without downloading
- Auto-download mode for batch processing

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

1. **Download data using coordinates file (interactive granule selection):**
   ```bash
   python src/download_hls_data.py \
     --coords-file data/sentinel/region-0/coordinates.txt \
     --date 2024-07-15 \
     --bands B02 B03 B04
   ```
   *The script will show available granules and let you select which ones to download.*

2. **Download data using direct coordinates (auto-download all granules):**
   ```bash
   python src/download_hls_data.py \
     --sw-lat 45.24301 --sw-lon 78.44504 \
     --ne-lat 45.2912 --ne-lon 78.49116 \
     --date 2024-07-15 \
     --bands B8A B11 B12 \
     --auto-download
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

# Download data with interactive granule selection (default)
downloaded_files = downloader.download_hls_data(
    sw_coords=(45.24301, 78.44504),  # Southwest (lat, lon)
    ne_coords=(45.2912, 78.49116),   # Northeast (lat, lon)
    date="2024-07-15",               # Date or "start,end" range
    bands=["B02", "B03", "B04"],     # Bands to download
    output_dir="./data/downloaded",   # Output directory
    max_results=10,                  # Max files to download
    auto_download=False              # Interactive mode (default)
)

# Or download all granules automatically
downloaded_files = downloader.download_hls_data(
    sw_coords=(45.24301, 78.44504),
    ne_coords=(45.2912, 78.49116),
    date="2024-07-15",
    bands=["B02", "B03", "B04"],
    output_dir="./data/downloaded",
    max_results=10,
    auto_download=True               # Auto-download all granules
)

print(f"Downloaded {len(downloaded_files)} files")
# Files are organized in granule-specific folders under output_dir
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

## Granule Organization & Selection

### Granule Folders
Each HLS granule is downloaded to its own folder, organized by granule identifier:
```
./data/downloaded/
├── HLS.S30.T43TGL.2024196T053649.v2.0/
│   ├── HLS.S30.T43TGL.2024196T053649.v2.0.B02.tif
│   ├── HLS.S30.T43TGL.2024196T053649.v2.0.B03.tif
│   └── HLS.S30.T43TGL.2024196T053649.v2.0.B04.tif
└── HLS.S30.T43TGM.2024196T053649.v2.0/
    ├── HLS.S30.T43TGM.2024196T053649.v2.0.B02.tif
    ├── HLS.S30.T43TGM.2024196T053649.v2.0.B03.tif
    └── HLS.S30.T43TGM.2024196T053649.v2.0.B04.tif
```

### Interactive Selection
By default, the script provides an interactive interface to select granules:
```
🔍 Found 2 granules:
   1. HLS.S30.T43TGL.2024196T053649.v2.0 (6 bands)
   2. HLS.S30.T43TGM.2024196T053649.v2.0 (6 bands)

Options:
   - Enter granule numbers (1-2) separated by commas to select specific granules
   - Press Enter to download all granules
   - Type 'abort' to cancel

Your choice: 1,2
```

### Selection Options
- **Select specific granules**: Enter numbers like `1` or `1,3`
- **Download all**: Press Enter
- **Cancel**: Type `abort`

### Automatic Download Mode
Use `--auto-download` to skip interactive selection and download all granules automatically.

### Maximum Limit
The script automatically aborts if more than **3 granules** are detected to prevent excessive downloads. Narrow your search criteria (smaller area or date range) if this occurs.

## Examples

### Example 1: Interactive Granule Selection
```bash
python src/download_hls_data.py \
  --coords-file coordinates.txt \
  --date 2024-07-15 \
  --bands B02 B03 B04 \
  --output-dir ./rgb_data
```
*Script will display available granules and prompt for selection.*

### Example 2: Auto-Download All Granules
```bash
python src/download_hls_data.py \
  --sw-lat 45.24 --sw-lon 78.44 \
  --ne-lat 45.29 --ne-lon 78.49 \
  --date 2024-07-15 \
  --bands B8A B11 B12 \
  --output-dir ./nir_swir_data \
  --auto-download
```
*Downloads all detected granules automatically without user interaction.*

### Example 3: Time Series with Granule Organization
```bash
python src/download_hls_data.py \
  --coords-file coordinates.txt \
  --date "2024-06-01,2024-08-31" \
  --bands B03 B04 B8A \
  --max-results 100 \
  --output-dir ./time_series
```
*Each granule will be saved in separate folders for easy time series analysis.*

### Example 4: Check Available Data
```bash
python src/download_hls_data.py \
  --coords-file coordinates.txt \
  --date "2024-07-01,2024-07-31" \
  --list-only
```

### Example 5: Selecting Specific Granules
When prompted with granule selection:
```
🔍 Found 3 granules:
   1. HLS.S30.T43TGL.2024196T053649.v2.0 (6 bands)
   2. HLS.S30.T43TGM.2024196T053649.v2.0 (6 bands)
   3. HLS.S30.T43TGN.2024196T053649.v2.0 (6 bands)

Your choice: 1,3
```
*This would download only granules 1 and 3, skipping granule 2.*

## Command Line Options

```
usage: download_hls_data.py [-h] (--coords-file COORDS_FILE | --coords-direct SW_LAT SW_LON NE_LAT NE_LON)
                           [--sw-lat SW_LAT] [--sw-lon SW_LON] [--ne-lat NE_LAT] [--ne-lon NE_LON]
                           --date DATE [--bands BANDS [BANDS ...]] [--output-dir OUTPUT_DIR]
                           [--max-results MAX_RESULTS] [--list-only] [--auto-download]

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
  --auto-download       Automatically download all granules without user interaction
```

## Output

Downloaded files are organized in granule-specific folders with GeoTIFF (.tif) files:

```
./data/downloaded/
├── HLS.S30.T43TGL.2024196T053649.v2.0/
│   ├── HLS.S30.T43TGL.2024196T053649.v2.0.B02.tif
│   ├── HLS.S30.T43TGL.2024196T053649.v2.0.B03.tif
│   └── HLS.S30.T43TGL.2024196T053649.v2.0.B04.tif
└── HLS.S30.T43TGM.2024196T053649.v2.0/
    ├── HLS.S30.T43TGM.2024196T053649.v2.0.B02.tif
    ├── HLS.S30.T43TGM.2024196T053649.v2.0.B03.tif
    └── HLS.S30.T43TGM.2024196T053649.v2.0.B04.tif
```

### File Naming Convention:
- `S30`: Sentinel-2 data
- `T43TGL`: MGRS tile identifier
- `2024196`: Year and day of year (Julian day)
- `T053649`: Time of acquisition
- `v2.0`: Version
- `B02`, `B03`, etc.: Band identifier

### Folder Structure Benefits:
- **Easy granule identification**: Each folder represents one satellite acquisition
- **Simplified processing**: Process all bands from a single granule together
- **Time series analysis**: Compare the same location across different acquisition dates
- **Reduced file clutter**: Organized structure instead of hundreds of files in one directory

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

## Multi-Temporal Image Assembly

The project includes `assemble_rasterio.py`, a lightweight script for assembling multi-temporal satellite images into single 18-band GeoTIFF files using rasterio (no QGIS required).

### Features

- **Multi-temporal assembly**: Combines 3 time periods (t0, t1, t2) with 6 bands each into one 18-band image
- **Precise coordinate clipping**: Output bounds exactly match coordinates from `coordinates.txt`
- **Automatic CRS transformation**: Handles conversion from WGS84 coordinates to image projection
- **Lightweight dependencies**: Uses only rasterio and numpy
- **Band organization**: Maintains logical band order (t0_B02, t0_B03, ..., t2_B12)
- **Compression**: Outputs LZW-compressed GeoTIFF files

### Usage

#### Command Line

```bash
# Assemble with automatic clipping from coordinates.txt
python assemble_rasterio.py data/sentinel/region-0/ --output output/my_18band.tif

# Assemble with custom bounding box
python assemble_rasterio.py data/sentinel/region-0/ \
  --bbox 45.24301,78.44504,45.2912,78.49116 \
  --output output/custom_18band.tif

# Use full image extent (no clipping)
python assemble_rasterio.py data/sentinel/region-0/ \
  --output output/full_18band.tif
```

#### Input Directory Structure

The script expects this folder structure:
```
data/sentinel/region-0/
├── coordinates.txt          # Optional: defines clipping bounds
├── t0/                     # Time period 0
│   ├── *.B02.tiff
│   ├── *.B03.tiff
│   ├── *.B04.tiff
│   ├── *.B8A.tiff
│   ├── *.B11.tiff
│   └── *.B12.tiff
├── t1/                     # Time period 1
│   ├── *.B02.tiff
│   ├── *.B03.tiff
│   ├── *.B04.tiff
│   ├── *.B8A.tiff
│   ├── *.B11.tiff
│   └── *.B12.tiff
└── t2/                     # Time period 2
    ├── *.B02.tiff
    ├── *.B03.tiff
    ├── *.B04.tiff
    ├── *.B8A.tiff
    ├── *.B11.tiff
    └── *.B12.tiff
```

#### Coordinates File Format

Create a `coordinates.txt` file in your input directory:
```
HLS Sentinel-2 Multi-spectral Instrument Surface Reflectance Daily Global 30m v2.0

sw 45.24301,78.44504
ne 45.2912,78.49116
```

### Output

The script produces a single 18-band GeoTIFF with:
- **Band 1-6**: t0 bands (B02, B03, B04, B8A, B11, B12)
- **Band 7-12**: t1 bands (B02, B03, B04, B8A, B11, B12)  
- **Band 13-18**: t2 bands (B02, B03, B04, B8A, B11, B12)

#### Band Descriptions
Each band includes descriptive metadata:
- `t0_B02`, `t0_B03`, `t0_B04`, `t0_B8A`, `t0_B11`, `t0_B12`
- `t1_B02`, `t1_B03`, `t1_B04`, `t1_B8A`, `t1_B11`, `t1_B12`
- `t2_B02`, `t2_B03`, `t2_B04`, `t2_B8A`, `t2_B11`, `t2_B12`

### Coordinate System Handling

The script automatically handles coordinate system transformations:

1. **Reads coordinates** from `coordinates.txt` (in WGS84 lat/lon)
2. **Detects image CRS** from input files (typically UTM)
3. **Transforms coordinates** to match image projection
4. **Clips precisely** to specified bounds

#### Example Transformation
```
Input (WGS84):  lat=45.28826, lon=78.43218
Output (UTM 43N): x=769,515.23m, y=5,020,156.78m
```

### Command Line Options

```
usage: assemble_rasterio.py [-h] [--bbox BBOX] [--output OUTPUT] [--verbose] input_dir

Assemble 18-band multi-temporal satellite images

positional arguments:
  input_dir            Input directory containing t0, t1, t2 folders

optional arguments:
  -h, --help           show this help message and exit
  --bbox BBOX          Bounding box as sw_lat,sw_lon,ne_lat,ne_lon
  --output OUTPUT      Output file path (default: assembled_18band.tif)
  --verbose, -v        Verbose output
```

### Integration with HLS Downloader

Perfect workflow integration:

1. **Download multi-temporal data** using the HLS downloader
2. **Organize by time periods** (t0, t1, t2)
3. **Assemble into training data** using `assemble_rasterio.py`

```bash
# Step 1: Download data for 3 time periods
python src/download_hls_data.py --coords-file coordinates.txt --date 2024-05-15 --bands B02 B03 B04 B8A B11 B12
python src/download_hls_data.py --coords-file coordinates.txt --date 2024-06-30 --bands B02 B03 B04 B8A B11 B12  
python src/download_hls_data.py --coords-file coordinates.txt --date 2024-07-15 --bands B02 B03 B04 B8A B11 B12

# Step 2: Organize into time folders (manually or with scripts)
# Move downloaded granules to t0/, t1/, t2/ folders

# Step 3: Assemble into 18-band training image
python assemble_rasterio.py data/sentinel/region-0/ --output training_data.tif
```

### Dependencies

The assembly script requires:
```bash
pip install rasterio numpy shapely
```

### Use Cases

- **Machine learning training data**: Create multi-temporal input features
- **Change detection**: Analyze temporal patterns across acquisitions  
- **Crop classification**: Capture seasonal vegetation dynamics
- **Time series analysis**: Prepare data for temporal modeling

## References

- [earthaccess library](https://github.com/nsidc/earthaccess)
- [NASA Earthdata](https://earthdata.nasa.gov/)
- [HLS Dataset Documentation](https://lpdaac.usgs.gov/products/hlss30v002/)
- [Rasterio Documentation](https://rasterio.readthedocs.io/) # skyterra-crop-classification
