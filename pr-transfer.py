import os
import shutil
import logging
import zipfile
from datetime import datetime

# Log dosyasını ayarla
log_file = "file_transfer.log"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def read_config_files():
    """Mevcut dizindeki tüm source*.txt dosyalarını oku"""
    configs = []
    for file in os.listdir():
        if file.startswith("source") and file.endswith(".txt"):
            config = {}
            with open(file, 'r', encoding='utf-8') as f:
                for line in f:
                    key, value = line.strip().split('=')
                    config[key.strip()] = value.strip()
            configs.append(config)
    return configs

def filter_files(source, extensions=None, min_size=None, max_size=None, use_size_filter=True, start_date=None, end_date=None, use_date_filter=True):
    """Belirtilen kriterlere göre dosyaları filtrele"""
    files_to_process = []
    for root, _, files in os.walk(source):
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            if extensions and not file.lower().endswith(tuple(extensions)):
                continue
            if use_size_filter:
                if min_size and file_size < min_size:
                    continue
                if max_size and file_size > max_size:
                    continue
            if use_date_filter:
                if start_date and file_mtime < start_date:
                    continue
                if end_date and file_mtime > end_date:
                    continue
            
            files_to_process.append(file_path)
    return files_to_process

def transfer_files(files, target, move=False, zip_files=False):
    """Dosyaları belirtilen hedefe taşı veya kopyala. Opsiyonel olarak zipleyebilir."""
    if not os.path.exists(target):
        os.makedirs(target)
    
    if zip_files:
        zip_path = os.path.join(target, "transferred_files.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files:
                file_name = os.path.basename(file_path)
                try:
                    zipf.write(file_path, file_name)
                    logging.info(f"Zipped: {file_name} | Source: {file_path}")
                    print(f"Zipped: {file_name}")
                except Exception as e:
                    logging.error(f"Error zipping {file_path}: {str(e)}")
                    print(f"Error: {file_path} -> {str(e)}")
    else:
        for file_path in files:
            file_name = os.path.basename(file_path)
            target_path = os.path.join(target, file_name)
            
            try:
                if move:
                    shutil.move(file_path, target_path)
                    action = "Moved"
                else:
                    shutil.copy2(file_path, target_path)
                    action = "Copied"
                
                file_size = os.path.getsize(target_path)
                logging.info(f"{action}: {file_name} | Size: {file_size} bytes | Target: {target_path}")
                print(f"{action}: {file_name} -> {target_path}")
            except Exception as e:
                logging.error(f"Error processing {file_path}: {str(e)}")
                print(f"Error: {file_path} -> {str(e)}")

if __name__ == "__main__":
    configs = read_config_files()
    
    if not configs:
        print("ERROR: Hiçbir source.txt dosyası bulunamadı!")
    else:
        for config in configs:
            source = config.get("SOURCE")
            target = config.get("TARGET")
            
            if not source or not target:
                print(f"ERROR: {config} dosyasında SOURCE veya TARGET eksik!")
                continue
            
            # Opsiyonel filtreleme parametreleri
            extensions = config.get("EXTENSIONS", "").split(',') if "EXTENSIONS" in config else None
            min_size = int(config.get("MIN_SIZE", 0)) if "MIN_SIZE" in config else None
            max_size = int(config.get("MAX_SIZE", 0)) if "MAX_SIZE" in config else None
            move = config.get("MOVE", "False").lower() == "true"
            zip_files = config.get("ZIP", "False").lower() == "true"
            use_size_filter = config.get("USE_SIZE_FILTER", "True").lower() == "true"
            use_date_filter = config.get("USE_DATE_FILTER", "True").lower() == "true"
            
            start_date = datetime.strptime(config.get("START_DATE", ""), "%Y-%m-%d") if "START_DATE" in config and config["START_DATE"] else None
            end_date = datetime.strptime(config.get("END_DATE", ""), "%Y-%m-%d") if "END_DATE" in config and config["END_DATE"] else None
            
            files = filter_files(source, extensions, min_size, max_size, use_size_filter, start_date, end_date, use_date_filter)
            transfer_files(files, target, move, zip_files)
