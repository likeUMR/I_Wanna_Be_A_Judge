import os
from pathlib import Path
import glob

def find_dir(name):
    paths = [
        fr"F:\素材\游戏制作\裁判文书\裁判文书全量数据\{name}",
        fr"d:\PROJECT\VSCode\AI+Game\I_Wanna_Be_A_Judge\data\{name}"
    ]
    print(f"Checking for {name} in:")
    for p in paths:
        exists = os.path.exists(p)
        print(f"  - {p} (Exists: {exists})")
        if exists: return Path(p)
    
    print(f"Searching via glob for {name} on F:...")
    matches = glob.glob(f'F:/**/*{name}*', recursive=True)
    if matches:
        print(f"  - Found: {matches[0]}")
        return Path(matches[0])
    return None

source = find_dir("cases_by_adcode")
if source:
    files = [f for f in os.listdir(source) if f.endswith('.csv')]
    print(f"Source: {source}")
    print(f"File count: {len(files)}")
else:
    print("Source directory NOT FOUND.")
