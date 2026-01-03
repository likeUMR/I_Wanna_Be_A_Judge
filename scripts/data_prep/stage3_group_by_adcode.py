import os
import pandas as pd
import re
import shutil
import time
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse

# Configuration
def find_dir(name):
    paths = [
        fr"F:\素材\游戏制作\裁判文书\裁判文书全量数据\{name}",
        fr"d:\PROJECT\VSCode\AI+Game\I_Wanna_Be_A_Judge\data\{name}"
    ]
    for p in paths:
        if os.path.exists(p): return Path(p)
    import glob
    matches = glob.glob(f'F:/**/*{name}*', recursive=True)
    if matches: return Path(matches[0])
    return Path(paths[0])

SOURCE_DIR = find_dir("structured_results")
OUTPUT_DIR = find_dir("cases_by_adcode")
TEMP_DIR = OUTPUT_DIR / "temp_parts"

def get_year_from_filename(filename):
    match = re.search(r'(\d{4})', filename)
    return int(match.group(1)) if match else 0

def clean_adcode_vectorized(s):
    return s.astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

def process_file_worker(filename):
    """Worker process to read one source file and split it into AdCode parts in a temp dir."""
    file_path = SOURCE_DIR / filename
    year = get_year_from_filename(filename)
    year_temp_dir = TEMP_DIR / str(year)
    year_temp_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        chunk_size = 200000 
        # 尝试不同编码
        try:
            # 先试 utf-8-sig
            reader = pd.read_csv(file_path, chunksize=chunk_size, low_memory=False, encoding='utf-8-sig')
            first_chunk = next(reader)
            if 'AdCode' not in first_chunk.columns:
                raise ValueError("Encoding check failed")
            # 重新创建 reader
            reader = pd.read_csv(file_path, chunksize=chunk_size, low_memory=False, encoding='utf-8-sig')
        except Exception:
            # 失败则试 gbk
            reader = pd.read_csv(file_path, chunksize=chunk_size, low_memory=False, encoding='gbk')

        adcode_counts = {}
        for chunk in reader:
            if 'AdCode' not in chunk.columns:
                # 再次检查是否有 AdCode，如果没有则可能文件真的有问题
                continue
            
            valid_rows = chunk.dropna(subset=['AdCode']).copy()
            valid_rows['AdCode'] = clean_adcode_vectorized(valid_rows['AdCode'])
            valid_rows = valid_rows[~valid_rows['AdCode'].str.lower().isin(['nan', '', 'none'])]
            
            if valid_rows.empty: continue

            for adcode, group_df in valid_rows.groupby('AdCode'):
                out_part = year_temp_dir / f"{adcode}.csv"
                write_header = not out_part.exists()
                group_df.to_csv(out_part, mode='a', index=False, header=write_header, encoding='utf-8-sig')
                adcode_counts[adcode] = adcode_counts.get(adcode, 0) + len(group_df)
                
        return True, filename, adcode_counts
    except Exception as e:
        return False, filename, str(e)

def merge_adcode_worker(adcode, part_paths):
    """Worker to merge all year parts for a specific AdCode."""
    try:
        dfs = []
        for p in part_paths:
            dfs.append(pd.read_csv(p, low_memory=False, encoding='utf-8-sig'))
        
        if not dfs: return False, adcode
        
        final_df = pd.concat(dfs)
        output_file = OUTPUT_DIR / f"{adcode}.csv"
        final_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        return True, adcode
    except Exception as e:
        return False, f"{adcode}: {str(e)}"

def merge_batch_worker(adcode_list, adcode_to_parts):
    """Top-level batch worker for merging."""
    for adcode in adcode_list:
        merge_adcode_worker(adcode, adcode_to_parts[adcode])
    return True

def safe_rmtree(path, retries=3, delay=2):
    """Safely remove a directory with retries for Windows permission issues."""
    if not path.exists():
        return
    for i in range(retries):
        try:
            shutil.rmtree(path)
            return
        except PermissionError:
            if i < retries - 1:
                print(f"Warning: Permission denied for {path}. Retrying in {delay}s... ({i+1}/{retries})")
                time.sleep(delay)
            else:
                print(f"Error: Could not delete {path}. Please close any open files in this directory.")
                # Instead of crashing, we can try to continue but might have mixed data
                pass

def process_all_files(test_mode=False):
    t_start = time.time()
    
    print(f"Cleaning existing output directory: {OUTPUT_DIR}")
    safe_rmtree(OUTPUT_DIR)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    files = [f for f in os.listdir(SOURCE_DIR) if f.endswith('.csv') and 'structured_' in f]
    files.sort(key=get_year_from_filename, reverse=True)
    files_to_process = [f for f in files if get_year_from_filename(f) <= 2018]
    
    if test_mode:
        files_to_process = files_to_process[:2]
        print(f"TEST MODE: {len(files_to_process)} files.")

    print(f"Step 1: Parallel Splitting {len(files_to_process)} source files...")
    
    all_adcodes = set()
    with ProcessPoolExecutor(max_workers=max(1, os.cpu_count() - 1)) as executor:
        futures = {executor.submit(process_file_worker, f): f for f in files_to_process}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Splitting"):
            success, fname, res = future.result()
            if success:
                all_adcodes.update(res.keys())
            else:
                print(f"Error in {fname}: {res}")

    t_split = time.time()
    print(f"Splitting finished in {t_split - t_start:.2f}s. Found {len(all_adcodes)} unique AdCodes.")

    print(f"Step 2: Parallel Merging {len(all_adcodes)} AdCode files...")
    
    # Map each adcode to its temporary part files
    adcode_to_parts = {}
    for year_dir in TEMP_DIR.iterdir():
        if year_dir.is_dir():
            for part_file in year_dir.glob("*.csv"):
                adcode = part_file.stem
                if adcode not in adcode_to_parts:
                    adcode_to_parts[adcode] = []
                adcode_to_parts[adcode].append(part_file)

    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        adcode_list = list(adcode_to_parts.keys())
        batch_size = 50
        batches = [adcode_list[i:i + batch_size] for i in range(0, len(adcode_list), batch_size)]
        
        # Pass top-level function and picklable arguments
        futures = [executor.submit(merge_batch_worker, b, adcode_to_parts) for b in batches]
        for _ in tqdm(as_completed(futures), total=len(futures), desc="Merging"):
            pass

    # Clean up temp files
    shutil.rmtree(TEMP_DIR)
    
    t_end = time.time()
    print(f"\nAll processing finished in {t_end - t_start:.2f}s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Process only 2 files for testing.")
    args = parser.parse_args()
    process_all_files(test_mode=args.test)
