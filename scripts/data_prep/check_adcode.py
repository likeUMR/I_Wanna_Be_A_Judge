import os
import pandas as pd
from pathlib import Path
import glob

def find_dir(name):
    paths = [
        fr"F:\素材\游戏制作\裁判文书\裁判文书全量数据\{name}",
        fr"d:\PROJECT\VSCode\AI+Game\I_Wanna_Be_A_Judge\data\{name}"
    ]
    for p in paths:
        if os.path.exists(p): return Path(p)
    matches = glob.glob(f'F:/**/*{name}*', recursive=True)
    if matches: return Path(matches[0])
    return None

processed = find_dir("processed_results")
if processed:
    print(f"Scanning directory: {processed}")
    all_beijing_count = 0
    for f in processed.glob("*.csv"):
        try:
            df = pd.read_csv(f, encoding='utf-8-sig', low_memory=False, nrows=10000)
        except:
            try:
                df = pd.read_csv(f, encoding='gbk', low_memory=False, nrows=10000)
            except:
                continue
        
        court_col = next((c for c in df.columns if '法院' in str(c)), None)
        if court_col:
            beijing = df[df[court_col].astype(str).str.contains('北京')]
            if not beijing.empty:
                print(f"FOUND Beijing in {f.name}: {len(beijing)} rows (in first 10000)")
                all_beijing_count += len(beijing)
    print(f"Total Beijing rows found in samples: {all_beijing_count}")
else:
    print("Processed directory NOT FOUND.")
