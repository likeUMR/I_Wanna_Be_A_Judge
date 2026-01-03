import os
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

structured = find_dir("structured_results")
if structured:
    files = [f for f in os.listdir(structured) if f.endswith('.csv')]
    print(f"Structured: {structured}")
    print(f"File count: {len(files)}")
    if files:
        print(f"Example file: {files[0]}")
else:
    print("Structured directory NOT FOUND.")
