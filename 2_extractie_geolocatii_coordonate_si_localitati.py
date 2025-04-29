import os
import subprocess
import csv
import hashlib
import json
import sqlite3
from datetime import datetime
import platform
import logging
from tqdm import tqdm



def calculate_file_hashes(filepath):
    """
    Calculate file hashes (MD5, SHA1, SHA256).
    
    :param filepath: Path to the file
    :return: Dictionary with file hashes
    """
    hash_algorithms = {
        'MD5': hashlib.md5(),
        'SHA1': hashlib.sha1(),
        'SHA256': hashlib.sha256()
    }
    
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                for hash_obj in hash_algorithms.values():
                    hash_obj.update(chunk)
        
        return {
            f"{alg}_Hash": hash_obj.hexdigest() 
            for alg, hash_obj in hash_algorithms.items()
        }
    except IOError as e:
        logging.error(f"Error calculating hashes for {filepath}: {e}")
        return {}

def prepare_output_folder(output_path):
    """
    Prepare and return the output folder path.
    
    :param output_path: Desired output folder path
    :return: Path to the output folder
    """
    try:
        os.makedirs(output_path, exist_ok=True)
        logging.info(f"Output folder prepared: {output_path}")
        return output_path
    except Exception as e:
        logging.error(f"Error creating output folder {output_path}: {e}")
        raise

def extract_geolocation_data(folder_path, exiftool_path, output_options=None):
    """
    Extract geolocation metadata from files in a folder with progress tracking.
    
    :param folder_path: Path to the folder containing files
    :param exiftool_path: Path to ExifTool executable
    :param output_options: Dictionary with output configuration
    :return: List of geolocation metadata entries
    """
    # Validate ExifTool path
    if not os.path.exists(exiftool_path):
        logging.error(f"ExifTool executable not found at {exiftool_path}")
        return []

    # Default output options
    default_options = {
        'output_folder': os.path.join(folder_path, 'Geolocation_data_output'),
        'output_formats': ['json', 'csv', 'sql'],
        'device_source': platform.node()
    }
    
    # Merge default and user-provided options
    options = {**default_options, **(output_options or {})}

    # Ensure output folder exists
    prepare_output_folder(options['output_folder'])

    # Get list of files and filter for files only
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    logging.info(f"Starting geolocation data extraction for {len(files)} files")

    # Process files and collect geolocation data with progress bar
    geolocation_data = []
    with tqdm(total=len(files), desc="Extracting Geolocation Data", unit="file", 
              bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
        for filename in files:
            filepath = os.path.join(folder_path, filename)
            
            try:
                # Calculate file hashes for identification
                file_hashes = calculate_file_hashes(filepath)
                
                # Extract geolocation data using ExifTool with the geolocation API
                geolocation_output = subprocess.check_output(
                    [exiftool_path, '-api', 'geolocation', '-geolocation*', '-j', filepath], 
                    universal_newlines=True
                )
                
                try:
                    geo_data = json.loads(geolocation_output)
                    if geo_data and isinstance(geo_data, list) and len(geo_data) > 0:
                        geo_info = geo_data[0]
                        
                        # Create a consolidated entry with filename and geolocation data
                        consolidated_entry = {
                            'Filename': filename,
                            'Full Path': filepath,
                            'MD5_Hash': file_hashes.get('MD5_Hash', ''),
                            'Extraction Timestamp': datetime.now().isoformat(),
                            'Source Device': options['device_source']
                        }
                        
                        # Add all geolocation fields from ExifTool output
                        for key, value in geo_info.items():
                            if key.startswith('Geolocation'):
                                consolidated_entry[key] = value
                        
                        geolocation_data.append(consolidated_entry)
                        logging.info(f"Processed: {filename}")
                    else:
                        logging.warning(f"No geolocation data found for: {filename}")
                except json.JSONDecodeError:
                    logging.warning(f"Failed to parse geolocation data for: {filename}")
                
                pbar.update(1)
            
            except Exception as e:
                logging.error(f"Error processing {filename}: {e}")
                pbar.update(1)

    # Output data in specified formats
    base_path = os.path.join(options['output_folder'], 'geo_location')
    
    if 'json' in options['output_formats'] and geolocation_data:
        try:
            with open(f"{base_path}.json", 'w', encoding='utf-8') as json_file:
                json.dump(geolocation_data, json_file, indent=4, ensure_ascii=False)
            logging.info(f"JSON output saved to {base_path}.json")
        except Exception as e:
            logging.error(f"Error saving JSON output: {e}")
    
    if 'csv' in options['output_formats'] and geolocation_data:
        try:
            # Get all unique fields from all entries
            fieldnames = set()
            for entry in geolocation_data:
                fieldnames.update(entry.keys())
            fieldnames = sorted(list(fieldnames))
            
            with open(f"{base_path}.csv", 'w', newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(geolocation_data)
            logging.info(f"CSV output saved to {base_path}.csv")
        except Exception as e:
            logging.error(f"Error saving CSV output: {e}")
    
    if 'sql' in options['output_formats'] and geolocation_data:
        try:
            # Create SQLite database
            db_path = f"{base_path}.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all unique geolocation fields from all entries
            geo_fields = set()
            for entry in geolocation_data:
                geo_fields.update([k for k in entry.keys() if k.startswith('Geolocation')])
            
            # Create table with dynamic columns based on available geolocation fields
            create_table_sql = '''
                CREATE TABLE IF NOT EXISTS geolocation_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    full_path TEXT NOT NULL,
                    md5_hash TEXT,
                    extraction_timestamp TEXT,
                    source_device TEXT
            '''
            
            # Add geolocation fields to table schema
            for field in sorted(geo_fields):
                field_name = field.replace(' ', '_').lower()
                create_table_sql += f',\n    {field_name} TEXT'
            
            create_table_sql += '\n)'
            cursor.execute(create_table_sql)
            
            # Insert data
            for entry in geolocation_data:
                # Prepare column names and placeholders
                columns = ['filename', 'full_path', 'md5_hash', 'extraction_timestamp', 'source_device']
                values = [
                    entry.get('Filename', ''),
                    entry.get('Full Path', ''),
                    entry.get('MD5_Hash', ''),
                    entry.get('Extraction Timestamp', ''),
                    entry.get('Source Device', '')
                ]
                
                # Add geolocation fields
                for field in sorted(geo_fields):
                    field_name = field.replace(' ', '_').lower()
                    columns.append(field_name)
                    values.append(entry.get(field, ''))
                
                # Construct and execute SQL
                placeholders = ', '.join(['?' for _ in columns])
                insert_sql = f"INSERT INTO geolocation_data ({', '.join(columns)}) VALUES ({placeholders})"
                cursor.execute(insert_sql, values)
            
            conn.commit()
            conn.close()
            logging.info(f"SQLite database saved to {db_path}")
        except Exception as e:
            logging.error(f"Error creating SQLite database: {e}")
    
    # Create a text report with detailed information
    try:
        with open(f"{base_path}_report.txt", 'w', encoding='utf-8') as txt_file:
            for entry in geolocation_data:
                txt_file.write("=" * 50 + "\n")
                txt_file.write(f"FILE: {entry.get('Filename', '')}\n")
                txt_file.write("=" * 50 + "\n")
                
                for key, value in entry.items():
                    if key != 'Filename':  # Skip filename as it's already in the header
                        txt_file.write(f"{key}: {value}\n")
                txt_file.write("\n\n")
        logging.info(f"Text report saved to {base_path}_report.txt")
    except Exception as e:
        logging.error(f"Error saving text report: {e}")

    logging.info(f"Geolocation data extraction completed. Files with geolocation data: {len(geolocation_data)}")
    return geolocation_data

def main():
    """
    Main function to run the geolocation data extraction.
    """

    try:
        # Paths - update these before running
        folder_path = r"Jpg_folder"
        exiftool_path = r"exiftool.exe"
        
        # Extract geolocation data
        extract_geolocation_data(folder_path, exiftool_path)
        
    except Exception as e:
        logging.error(f"Script execution failed: {e}")

if __name__ == "__main__":
    main()
    print("Script finalizat. Modifică path-urile înainte de rulare.")