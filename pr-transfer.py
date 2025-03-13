import os
import shutil
import logging
import zipfile
import yaml
from datetime import datetime, timedelta

def setup_logging(log_file):
    """Her source için ayrı log dosyası oluştur"""
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def read_config_files():
    """Mevcut dizindeki tüm source*.yml dosyalarını oku"""
    configs = []
    for file in os.listdir():
        if file.startswith("source") and file.endswith(".yml"):
            with open(file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                config["CONFIG_FILE"] = file  # Dosya adını sakla
                configs.append(config)
    return configs

def get_relative_date_range(date_filter):
    """Belirtilen sabit tarih aralıklarını hesaplar"""
    today = datetime.now()
    if date_filter == "last_15_days":
        return today - timedelta(days=15), today
    elif date_filter == "last_1_month":
        return today - timedelta(days=30), today
    elif date_filter == "last_3_months":
        return today - timedelta(days=90), today
    elif date_filter == "last_6_months":
        return today - timedelta(days=180), today
    elif date_filter == "last_1_year":
        return today - timedelta(days=365), today
    return None, None

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

def zip_directory(target, zip_path):
    """Hedef dizindeki tüm dosya ve klasörleri ZIP içerisine ekle, hiyerarşiyi koru"""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(target):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, target))

def transfer_files(files, source, target, move=False, zip_files=False, log_file="file_transfer.log"):
    """Dosyaları belirtilen hedefe taşı veya kopyala. Opsiyonel olarak zipleyebilir."""
    setup_logging(log_file)
    
    if not os.path.exists(target):
        os.makedirs(target)
    
    for file_path in files:
        relative_path = os.path.relpath(file_path, source)
        target_path = os.path.join(target, relative_path)
        target_dir = os.path.dirname(target_path)
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        
        try:
            if move:
                shutil.move(file_path, target_path)
                action = "Moved"
            else:
                shutil.copy2(file_path, target_path)
                action = "Copied"
            
            file_size = os.path.getsize(target_path)
            logging.info(f"{action}: {file_path} -> {target_path} | Size: {file_size} bytes")
            print(f"{action}: {file_path} -> {target_path}")
        except Exception as e:
            logging.error(f"Error processing {file_path}: {str(e)}")
            print(f"Error: {file_path} -> {str(e)}")
    
    if zip_files:
        zip_path = os.path.join(target, "transferred_files.zip")
        zip_directory(target, zip_path)
        logging.info(f"Zipped directory: {target} -> {zip_path}")
        print(f"Zipped directory: {zip_path}")

if __name__ == "__main__":
    configs = read_config_files()
    
    if not configs:
        print("ERROR: Hiçbir source.yml dosyası bulunamadı!")
    else:
        for config in configs:
            source = config.get("SOURCE")
            target = config.get("TARGET")
            config_file = config.get("CONFIG_FILE", "source_unknown.yml")
            log_file = f"{config_file}.log"
            
            if not source or not target:
                print(f"ERROR: {config_file} dosyasında SOURCE veya TARGET eksik!")
                continue
            
            # Opsiyonel filtreleme parametreleri
            extensions = config.get("EXTENSIONS", [])
            min_size = config.get("MIN_SIZE")
            max_size = config.get("MAX_SIZE")
            move = config.get("MOVE", False)
            zip_files = config.get("ZIP", False)
            use_size_filter = config.get("USE_SIZE_FILTER", True)
            use_date_filter = config.get("USE_DATE_FILTER", True)
            
            start_date = datetime.strptime(config.get("START_DATE", ""), "%Y-%m-%d") if config.get("START_DATE") else None
            end_date = datetime.strptime(config.get("END_DATE", ""), "%Y-%m-%d") if config.get("END_DATE") else None
            
            # Sabit tarih aralıkları
            if "DATE_FILTER" in config:
                start_date, end_date = get_relative_date_range(config["DATE_FILTER"])
            
            print(f"Processing: {config_file}")
            files = filter_files(source, extensions, min_size, max_size, use_size_filter, start_date, end_date, use_date_filter)
            transfer_files(files, source, target, move, zip_files, log_file)
