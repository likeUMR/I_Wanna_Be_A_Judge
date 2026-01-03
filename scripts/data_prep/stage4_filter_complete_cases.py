import os
import pandas as pd
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
    return None

SOURCE_DIR = find_dir("cases_by_adcode")
if SOURCE_DIR is None:
    print("\n[致命错误] 找不到输入目录 'cases_by_adcode'。请先运行 stage3_group_by_adcode.py")
    import sys
    sys.exit(1)

PROJECT_ROOT = Path(r"d:\PROJECT\VSCode\AI+Game\I_Wanna_Be_A_Judge")
TARGET_DIR = PROJECT_ROOT / "public" / "data"
PERFECT_DIR = TARGET_DIR / "perfect"
REPORT_PATH = PROJECT_ROOT / "scripts" / "data_prep" / "filtering_report.csv"

# 仅保留这些列名
REQUIRED_COLUMNS = [
    '案号', 'AdCode', '原始链接', '法院', '案由', '全文', '审理程序', '审判组织形式', '是否公开审理',
    '姓名', '性别', '出生日期', '文化程度', '职业', '刑事前科', '是否未成年', '精神状态', '年龄',
    'SECTION_5_经审理查明的犯罪事实', 'SECTION_6_证据列举', '是否累犯', '是否未遂', '是否自首', '是否立功',
    '是否如实供述', '是否取得谅解', '是否退赃', '特殊身体状况', 'surrender_type', '主从犯身份',
    '罪名', '主刑', '刑期_年', '刑期_月', '罚金', '判决日期', 'SECTION_7_罪名认定理由', 'SECTION_10_判决主文'
]

def process_single_adcode(filename, max_rows):
    """处理单个 AdCode 文件的并行任务"""
    file_path = SOURCE_DIR / filename
    adcode = filename.replace('.csv', '')
    
    try:
        if not file_path.exists():
            return None
            
        # 尝试读取，处理可能的编码问题
        try:
            # 优先尝试 utf-8-sig
            df = pd.read_csv(file_path, encoding='utf-8-sig', low_memory=False)
            if '主字段缺失数量' not in df.columns:
                # 如果没有，可能编码还是不对，尝试 gbk
                df = pd.read_csv(file_path, encoding='gbk', low_memory=False)
        except Exception:
            df = pd.read_csv(file_path, encoding='gbk', low_memory=False)

        if len(df) == 0:
            return None
        
        original_count = len(df)
        
        # 严格检查列名
        if '主字段缺失数量' not in df.columns:
            # 这里的异常会被 ProcessPoolExecutor 捕获
            raise KeyError(f"文件 {filename} 缺失关键列 '主字段缺失数量'。当前列名: {list(df.columns)}")
            
        main_missing_col = '主字段缺失数量'
        sub_missing_col = '子字段缺失数量' if '子字段缺失数量' in df.columns else None

        # 计算展示字段完整度
        display_fields = ['姓名', '性别', '年龄', '职业', '文化程度']
        df['display_missing_count'] = 0
        for f in display_fields:
            if f in df.columns:
                df['display_missing_count'] += df[f].apply(
                    lambda x: 1 if x in [None, "", "不详", "None", "nan", "NaN"] or pd.isna(x) else 0
                )
            else:
                df['display_missing_count'] += 1

        # 筛选主字段必须完整的数据
        df[main_missing_col] = pd.to_numeric(df[main_missing_col], errors='coerce').fillna(1)
        base_mask = (df[main_missing_col] == 0)
        valid_df = df[base_mask].copy()
        
        if valid_df.empty:
            return {'AdCode': adcode, 'OriginalRows': original_count, 'PerfectRows': 0, 'RetainedRows': 0, 'PerfectBlocks': 0, 'FilteredBlocks': 0}

        BLOCK_SIZE = 10
        
        # 1. 提取完美数据 (展示字段 0 缺失)
        perfect_df = valid_df[valid_df['display_missing_count'] == 0].copy()
        perfect_count = len(perfect_df)
        perfect_blocks = 0
        if perfect_count > 0:
            existing_cols = [col for col in REQUIRED_COLUMNS if col in perfect_df.columns]
            # 分 block 保存
            for i in range(0, perfect_count, BLOCK_SIZE):
                block_df = perfect_df.iloc[i:i+BLOCK_SIZE]
                block_num = (i // BLOCK_SIZE) + 1
                block_filename = f"{adcode}_perfect_{block_num:02d}.csv"
                block_df[existing_cols].to_csv(PERFECT_DIR / block_filename, index=False, encoding='utf-8-sig')
                perfect_blocks = block_num

        # 2. 提取尽量完美的数据 (最多允许缺失 2 个展示字段)
        standard_df = valid_df[valid_df['display_missing_count'] <= 2].copy()
        sort_cols = ['display_missing_count']
        if sub_missing_col:
            standard_df[sub_missing_col] = pd.to_numeric(standard_df[sub_missing_col], errors='coerce').fillna(99)
            sort_cols.append(sub_missing_col)
        
        standard_df = standard_df.sort_values(by=sort_cols, ascending=True)
        
        # 计算保留池的平均缺失度
        retained_df = standard_df.head(max_rows) if max_rows else standard_df
        avg_missing = retained_df['display_missing_count'].mean() if not retained_df.empty else 0
        retained_count = len(retained_df)
        filtered_blocks = 0

        if retained_count > 0:
            existing_cols = [col for col in REQUIRED_COLUMNS if col in retained_df.columns]
            # 分 block 保存
            for i in range(0, retained_count, BLOCK_SIZE):
                block_df = retained_df.iloc[i:i+BLOCK_SIZE]
                block_num = (i // BLOCK_SIZE) + 1
                block_filename = f"{adcode}_filtered_{block_num:02d}.csv"
                block_df[existing_cols].to_csv(TARGET_DIR / block_filename, index=False, encoding='utf-8-sig')
                filtered_blocks = block_num

        return {
            'AdCode': adcode,
            'OriginalRows': original_count,
            'PerfectRows': perfect_count,
            'RetainedRows': retained_count,
            'AvgMissingInRetained': round(avg_missing, 2),
            'PerfectBlocks': perfect_blocks,
            'FilteredBlocks': filtered_blocks
        }
    except Exception as e:
        return {'AdCode': adcode, 'Error': str(e)}

def filter_all_cases(max_rows=100, test_mode=False):
    t_start = time.time()
    
    # 清理旧数据，避免 block 数量减少时残留旧文件
    import shutil
    for d in [TARGET_DIR, PERFECT_DIR]:
        if d.exists():
            print(f"清理旧目录: {d}")
            # 只清理 csv 文件，保留目录结构
            for f in d.glob("*.csv"):
                f.unlink()
        else:
            d.mkdir(parents=True, exist_ok=True)

    source_files = [f for f in os.listdir(SOURCE_DIR) if f.endswith('.csv')]
    if test_mode: source_files = source_files[:100]

    print(f"开始执行 Stage4: 完美分流与分片筛选 (Limit={max_rows}, BlockSize=10)...")

    report_data = []
    max_workers = os.cpu_count()
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_single_adcode, f, max_rows): f for f in source_files}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing AdCodes"):
            try:
                res = future.result()
                if res: report_data.append(res)
            except Exception as e:
                print(f"\n[致命错误] 处理文件时发生异常: {e}")
                executor.shutdown(wait=False, cancel_futures=True)
                import sys
                sys.exit(1)

    # 生成统计报告
    report_df = pd.DataFrame(report_data)
    report_df.to_csv(REPORT_PATH, index=False, encoding='utf-8-sig')
    
    # 生成 blocks_manifest.json
    import json
    manifest = {}
    for _, row in report_df.iterrows():
        if 'Error' in row and not pd.isna(row['Error']): continue
        adcode = str(row['AdCode'])
        manifest[adcode] = {
            'p': int(row['PerfectBlocks']) if 'PerfectBlocks' in row else 0,
            'f': int(row['FilteredBlocks']) if 'FilteredBlocks' in row else 0
        }
    
    manifest_path = TARGET_DIR / "blocks_manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False)
    print(f"分片清单已生成: {manifest_path}")
    
    # 打印简要报告
    if 'PerfectRows' in report_df.columns:
        print("\n" + "="*40)
        print("Stage4 筛选统计汇总")
        print("-" * 40)
        print(f"总处理行政区 (AdCode): {len(report_df)}")
        print(f"累计发现完美案例: {int(report_df['PerfectRows'].sum())}")
        print(f"累计保留标准案例: {int(report_df['RetainedRows'].sum())}")
        print(f"标准池平均每案缺失展示字段: {report_df['AvgMissingInRetained'].mean():.2f} 个")
        print(f"报告已保存至: {REPORT_PATH}")
        print("="*40)

    print(f"总耗时: {time.time() - t_start:.2f}s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    filter_all_cases(max_rows=args.limit, test_mode=args.test)
