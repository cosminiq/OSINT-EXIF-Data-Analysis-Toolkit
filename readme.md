# OSINT & EXIF Data Analysis Toolkit

A collection of powerful Python scripts for OSINT (Open Source Intelligence) investigations and forensic EXIF data extraction. This toolkit helps investigators, security professionals, and researchers extract, analyze, and visualize metadata from images and files.

## 🔍 Key Features

### 1. Comprehensive Metadata Extraction (`1_extractie_exif_hash_nume_raport_crimnalistic.py`)
- **File Hash Calculation**: Generates MD5, SHA1, and SHA256 hashes for file authentication and verification
- **EXIF Data Extraction**: Extracts all available EXIF metadata from files using ExifTool
- **Multiple Output Formats**: Generates results in JSON, CSV, and TXT formats for flexible analysis
- **Hash Database Creation**: Automatically creates separate hash databases (JSON, CSV, SQLite) for reference
- **Advanced Logging**: Comprehensive logging system with both file and console outputs
- **Progress Tracking**: Visual progress bars for monitoring extraction processes

### 2. Geolocation Intelligence (`2_extractie_geolocatii_coordonate_si_localitati.py`)
- **Geolocation Data Extraction**: Extracts GPS coordinates, city names, and location details
- **Specialized API Usage**: Utilizes ExifTool's geolocation API for enhanced location data
- **Comprehensive Database Creation**: Generates SQLite databases with all location attributes
- **Detailed Geolocation Reports**: Creates extensive reports mapping images to locations
- **Multi-Format Output**: Provides JSON, CSV and SQLite outputs for integration with other tools

### 3. Visual Geospatial Analysis (`3_vers3_clustere_thumbnail.py`)
- **Interactive Mapping**: Creates interactive maps with all geotagged images positioned
- **Cluster Visualization**: Implements marker clustering for handling large datasets
- **Route Visualization**: Draws connecting lines between points to show potential movement patterns
- **Image Thumbnails**: Automatically generates and displays thumbnails on the map
- **HTML Output**: Creates standalone HTML map files that can be viewed in any browser

## 🔧 Technical Capabilities

### OSINT Functionality
- Extract hidden metadata from files that might reveal sensitive information
- Identify location patterns and movement histories from geotagged media
- Create visual representations of data for intelligence analysis
- Build searchable databases of file signatures and metadata
- Generate standardized reports for investigations or evidence presentation

### EXIF & Metadata Analysis
- Extract complete EXIF data including camera information, timestamps, and geolocation
- Process device-specific metadata that can identify equipment used
- Analyze editing history and software used to modify files
- Extract embedded thumbnails and preview images
- Identify original creation data even after modifications

### Forensic Applications
- Create legally defensible hash values for evidence verification
- Generate comprehensive forensic reports suitable for legal proceedings
- Track chain of custody through detailed timestamp logging
- Identify patterns across multiple files through clustered analysis
- Visual representation of evidence with proper documentation

## 📋 Requirements
- Python 3.6+
- ExifTool (must be installed separately)
- Required Python packages:
  ```
  tqdm
  folium
  pandas
  pillow
  ```

## 🚀 Getting Started

1. Clone this repository
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Download and install [ExifTool](https://exiftool.org/)
4. Modify the file paths in the scripts to point to your data folder and ExifTool location
5. Run the scripts in sequence to extract, analyze and visualize the data

## 📊 Output Examples

### Metadata Extraction
- Comprehensive JSON, CSV, and TXT reports containing all extracted metadata
- Dedicated hash databases for file verification
- Structured SQLite databases for complex queries

### Geolocation Analysis
- Interactive HTML maps showing all geotagged images
- Cluster visualizations for identifying hotspots
- Path analysis showing movement patterns
- Visual thumbnails of images at their respective locations

## 🔐 Privacy & Ethical Usage

This toolkit is designed for legitimate forensic analysis, security research, and authorized investigations. Users must ensure they:

- Have proper authorization to analyze files
- Follow applicable laws and regulations regarding data privacy
- Use extracted information responsibly and legally
- Do not use these tools for unauthorized surveillance or privacy violations

## 📄 License

[MIT License](LICENSE)

---

⚠️ **Disclaimer**: This toolkit is provided for educational and legitimate investigative purposes only. The authors are not responsible for any misuse of this software.