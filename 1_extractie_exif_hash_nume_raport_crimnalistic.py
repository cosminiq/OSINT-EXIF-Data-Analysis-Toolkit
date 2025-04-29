import os
import subprocess
import csv
import hashlib
import json
from datetime import datetime
import platform
import logging
from tqdm import tqdm

def setup_logging(log_file='forensic_metadata.log', log_level=logging.INFO):
    """
    Configure logging for the script.
    
    :param log_file: Path to the log file
    :param log_level: Logging level
    """
    # Get log directory - if log_file has no directory, use current directory
    log_dir = os.path.dirname(log_file)
    if log_dir:  # If log_dir is not empty
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # Also log to console
        ]
    )
    logging.info("Logging initialized")

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

def extract_metadata(folder_path, exiftool_path, output_options=None):
    """
    Extract and process metadata from files in a folder with progress tracking.
    
    :param folder_path: Path to the folder containing files
    :param exiftool_path: Path to ExifTool executable
    :param output_options: Dictionary with output configuration
    :return: List of consolidated metadata entries
    """
    # Validate ExifTool path
    if not os.path.exists(exiftool_path):
        logging.error(f"ExifTool executable not found at {exiftool_path}")
        return []

    # Default output options
    default_options = {
        'output_folder': os.path.join(folder_path, 'Forensic_metadata_output'),
        'output_formats': ['json', 'csv', 'txt'],
        'device_source': platform.node()
    }
    
    # Merge default and user-provided options
    options = {**default_options, **(output_options or {})}

    # Ensure output folder exists
    prepare_output_folder(options['output_folder'])

    # Get list of files and filter for files only
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    logging.info(f"Starting metadata extraction for {len(files)} files")

    # Process files and collect metadata with progress bar
    consolidated_data = []
    with tqdm(total=len(files), desc="Extracting Metadata", unit="file", 
              bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
        for filename in files:
            filepath = os.path.join(folder_path, filename)
            
            try:
                # Calculate file hashes
                file_hashes = calculate_file_hashes(filepath)
                
                # Extract metadata using ExifTool
                metadata_json = subprocess.check_output(
                    [exiftool_path, '-j', filepath], 
                    universal_newlines=True
                )
                metadata = json.loads(metadata_json)[0]
                
                # Consolidate metadata
                consolidated_entry = {
                    'Nume fișier': filename,
                    'Cale completă': filepath,
                    'Dimensiune fișier': os.path.getsize(filepath),
                    'Hash MD5': file_hashes.get('MD5_Hash', ''),
                    'Hash SHA1': file_hashes.get('SHA1_Hash', ''),
                    'Hash SHA256': file_hashes.get('SHA256_Hash', ''),
                    'Timestamp înregistrare': datetime.now().isoformat(),
                    'Sursă/dispozitiv origine': options['device_source'],
                    'Metadate suplimentare': metadata
                }
                
                consolidated_data.append(consolidated_entry)
                logging.info(f"Procesat: {filename}")
                pbar.update(1)
            
            except Exception as e:
                logging.error(f"Eroare la procesarea {filename}: {e}")
                pbar.update(1)

    # Output data in specified formats
    base_path = os.path.join(options['output_folder'], 'forensic_metadata_consolidated')
    
    if 'json' in options['output_formats'] and consolidated_data:
        try:
            with open(f"{base_path}.json", 'w', encoding='utf-8') as json_file:
                json.dump(consolidated_data, json_file, indent=4, ensure_ascii=False)
            logging.info(f"JSON output saved to {base_path}.json")
        except Exception as e:
            logging.error(f"Error saving JSON output: {e}")
    
    if 'csv' in options['output_formats'] and consolidated_data:
        try:
            with open(f"{base_path}.csv", 'w', newline='', encoding='utf-8') as csv_file:
                fieldnames = list(consolidated_data[0].keys())
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(consolidated_data)
            logging.info(f"CSV output saved to {base_path}.csv")
        except Exception as e:
            logging.error(f"Error saving CSV output: {e}")
    
    if 'txt' in options['output_formats'] and consolidated_data:
        try:
            with open(f"{base_path}.txt", 'w', encoding='utf-8') as txt_file:
                for entry in consolidated_data:
                    txt_file.write("=" * 50 + "\n")
                    for key, value in entry.items():
                        txt_file.write(f"{key}: {value}\n")
                    txt_file.write("=" * 50 + "\n\n")
            logging.info(f"TXT output saved to {base_path}.txt")
        except Exception as e:
            logging.error(f"Error saving TXT output: {e}")

        # Adaugă acest cod imediat după crearea celorlalte fișiere output
    if consolidated_data:
        create_hash_database(consolidated_data, options['output_folder'])

    logging.info(f"Metadata extraction completed. Total files processed: {len(consolidated_data)}")
    return consolidated_data

def create_hash_database(consolidated_data, output_folder):
    """
    Create a separate database file containing only filenames and their hash values.
    
    :param consolidated_data: List of metadata entries
    :param output_folder: Folder where to save the hash database
    :return: Path to the created database file
    """
    logging.info("Creating hash database file")
    
    # Extract only the relevant fields
    hash_data = []
    for entry in consolidated_data:
        hash_entry = {
            'Nume fișier': entry['Nume fișier'],
            'MD5': entry['Hash MD5'],
            'SHA1': entry['Hash SHA1'],
            'SHA256': entry['Hash SHA256']
        }
        hash_data.append(hash_entry)
    
    # Create the hash database files
    hash_db_path = os.path.join(output_folder, 'hash_database')
    
    # Create JSON version
    try:
        with open(f"{hash_db_path}.json", 'w', encoding='utf-8') as json_file:
            json.dump(hash_data, json_file, indent=4, ensure_ascii=False)
        logging.info(f"Hash database JSON saved to {hash_db_path}.json")
    except Exception as e:
        logging.error(f"Error saving hash database JSON: {e}")
    
    # Create CSV version
    try:
        with open(f"{hash_db_path}.csv", 'w', newline='', encoding='utf-8') as csv_file:
            fieldnames = list(hash_data[0].keys())
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(hash_data)
        logging.info(f"Hash database CSV saved to {hash_db_path}.csv")
    except Exception as e:
        logging.error(f"Error saving hash database CSV: {e}")
    
    # Create SQLite database version
    try:
        import sqlite3
        db_path = f"{hash_db_path}.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_hashes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                md5 TEXT NOT NULL,
                sha1 TEXT NOT NULL,
                sha256 TEXT NOT NULL
            )
        ''')
        
        # Insert data
        for entry in hash_data:
            cursor.execute('''
                INSERT INTO file_hashes (filename, md5, sha1, sha256)
                VALUES (?, ?, ?, ?)
            ''', (
                entry['Nume fișier'],
                entry['MD5'],
                entry['SHA1'],
                entry['SHA256']
            ))
        
        conn.commit()
        conn.close()
        logging.info(f"Hash database SQLite saved to {db_path}")
    except Exception as e:
        logging.error(f"Error creating SQLite database: {e}")
    
    return hash_db_path







def main():
    """
    Example usage of the enhanced metadata extraction script.
    """
    # Configure logging - use current directory for log file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join('Jpg_folder\Forensic_metadata_output', 'forensic_metadata.log')
    setup_logging(log_file=log_file)

    try:
        # Example configuration
        folder_path = r"Jpg_folder"
        exiftool_path = r"exiftool.exe"
        
        # Extract metadata with default options
        extract_metadata(folder_path, exiftool_path)
        

    except Exception as e:
        logging.error(f"Script execution failed: {e}")

if __name__ == "__main__":
    main()
    print("Script gata de utilizare. Modifică path-urile înainte de rulare.")