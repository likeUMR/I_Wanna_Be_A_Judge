import os
import pandas as pd
import time
import shutil
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse

# Configuration
def find_dir(name):
    # 获取项目根目录下的 data 目录
    script_dir = Path(__file__).parent
    project_data_dir = script_dir.parent.parent / "data" / name
    
    paths = [
        Path(fr"F:\素材\游戏制作\裁判文书\裁判文书全量数据\{name}"),
        project_data_dir
    ]
    for p in paths:
        if p.exists(): return p
    
    # 如果都不存在，尝试在 F 盘搜索
    import glob
    try:
        matches = glob.glob(f'F:/**/*{name}*', recursive=True)
        if matches: return Path(matches[0])
    except Exception:
        pass
        
    return None

SOURCE_DIR = find_dir("cases_by_adcode")
if SOURCE_DIR is None:
    print("\n[致命错误] 找不到输入目录 'cases_by_adcode'。请先运行 stage3_group_by_adcode.py")
    import sys
    sys.exit(1)

# 使用相对路径获取项目根目录
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
TARGET_DIR = PROJECT_ROOT / "public" / "data"
PERFECT_DIR = TARGET_DIR / "perfect"
REPORT_PATH = SCRIPT_DIR / "filtering_report.csv"

# 仅保留这些列名
REQUIRED_COLUMNS = [
    '案号', 'AdCode', '原始链接', '法院', '案由', '全文', '审理程序', '审判组织形式', '是否公开审理',
    '姓名', '性别', '出生日期', '文化程度', '职业', '刑事前科', '是否未成年', '精神状态', '年龄',
    'SECTION_5_经审理查明的犯罪事实', 'SECTION_6_证据列举', '是否累犯', '是否未遂', '是否自首', '是否立功',
    '是否如实供述', '是否取得谅解', '是否退赃', '特殊身体状况', 'surrender_type', '主从犯身份',
    '罪名', '主刑', '刑期_年', '刑期_月', '罚金', '判决日期', 'SECTION_7_罪名认定理由', 'SECTION_10_判决主文'
]

def process_single_adcode(filename, max_rows, block_size=10):
    """处理单个 AdCode 文件的并行任务"""
    file_path = SOURCE_DIR / filename
    adcode = filename.replace('.csv', '')
    
    try:
        if not file_path.exists():
            return None
            
        # 既然 stage3 是我们生成的，编码固定为 utf-8-sig
        df = pd.read_csv(file_path, encoding='utf-8-sig', low_memory=False)

        if len(df) == 0:
            return None
        
        original_count = len(df)
        
        # 严格检查列名
        if '主字段缺失数量' not in df.columns:
            raise KeyError(f"文件 {filename} 缺失关键列 '主字段缺失数量'")
            
        main_missing_col = '主字段缺失数量'
        sub_missing_col = '子字段缺失数量' if '子字段缺失数量' in df.columns else None

        # 计算展示字段完整度 (向量化优化)
        display_fields = ['姓名', '性别', '年龄', '职业', '文化程度']
        present_display_fields = [f for f in display_fields if f in df.columns]
        
        # 向量化判断缺失值
        bad_values = [None, "", "不详", "None", "nan", "NaN"]
        if present_display_fields:
            # 统计存在的字段中的缺失情况
            missing_matrix = df[present_display_fields].isin(bad_values) | df[present_display_fields].isna()
            df['display_missing_count'] = missing_matrix.sum(axis=1)
            # 加上完全不存在的字段数量
            df['display_missing_count'] += (len(display_fields) - len(present_display_fields))
        else:
            df['display_missing_count'] = len(display_fields)

        # 准备排序和筛选
        df[main_missing_col] = pd.to_numeric(df[main_missing_col], errors='coerce').fillna(99)
        if sub_missing_col:
            df[sub_missing_col] = pd.to_numeric(df[sub_missing_col], errors='coerce').fillna(99)
        
        # 1. 提取完美数据 (主字段和展示字段均为 0 缺失)
        perfect_mask = (df[main_missing_col] == 0) & (df['display_missing_count'] == 0)
        perfect_df = df[perfect_mask]
        perfect_count = len(perfect_df)
        
        perfect_blocks = 0
        if perfect_count > 0:
            existing_cols = [col for col in REQUIRED_COLUMNS if col in df.columns]
            for i in range(0, perfect_count, block_size):
                block_df = perfect_df.iloc[i:i+block_size]
                block_num = (i // block_size) + 1
                block_filename = f"{adcode}_perfect_{block_num:02d}.csv"
                block_df[existing_cols].to_csv(PERFECT_DIR / block_filename, index=False, encoding='utf-8-sig')
                perfect_blocks = block_num

        # 2. 提取筛选数据 (保留最完整的前 100)
        sort_cols = [main_missing_col, 'display_missing_count']
        if sub_missing_col:
            sort_cols.append(sub_missing_col)
        
        # 仅对需要的数据进行排序，减少开销
        retained_df = df.sort_values(by=sort_cols, ascending=True)
        if max_rows:
            retained_df = retained_df.head(max_rows)
            
        avg_missing = retained_df['display_missing_count'].mean() if not retained_df.empty else 0
        retained_count = len(retained_df)
        filtered_blocks = 0

        if retained_count > 0:
            existing_cols = [col for col in REQUIRED_COLUMNS if col in df.columns]
            for i in range(0, retained_count, block_size):
                block_df = retained_df.iloc[i:i+block_size]
                block_num = (i // block_size) + 1
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

def filter_all_cases(max_rows=100, block_size=10, test_mode=False):
    t_start = time.time()
    
    # 清理旧数据：直接删除目录再重建，速度提升巨大
    for d in [TARGET_DIR, PERFECT_DIR]:
        if d.exists():
            print(f"快速清理目录: {d}")
            try:
                shutil.rmtree(d)
            except PermissionError:
                # 如果文件夹被占用，回退到循环删除
                for f in d.glob("*.csv"):
                    try: f.unlink()
                    except: pass
        d.mkdir(parents=True, exist_ok=True)

    source_files = [f for f in os.listdir(SOURCE_DIR) if f.endswith('.csv')]
    if not source_files:
        print(f"\n[致命错误] 输入目录 '{SOURCE_DIR}' 为空。没有 AdCode 分组数据可供筛选。")
        import sys
        sys.exit(1)

    if test_mode: source_files = source_files[:100]

    print(f"开始执行 Stage4: 完美分流与分片筛选 (Limit={max_rows}, BlockSize={block_size})...")

    report_data = []
    max_workers = os.cpu_count()
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_single_adcode, f, max_rows, block_size): f for f in source_files}
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
        
        # 检查缺失的地区
        admin_divisions_path = PROJECT_ROOT / "public" / "processed_admin_divisions.csv"
        if admin_divisions_path.exists():
            try:
                admin_df = pd.read_csv(admin_divisions_path, header=None, names=['name', 'adcode', 'p1', 'p2'], dtype={'adcode': str})
                # 只检查区县级 (adcode 最后两位非00)
                all_districts = set(admin_df[admin_df['adcode'].str.strip().str.endswith('00') == False]['adcode'].tolist())
                processed_districts = set(report_df[report_df['RetainedRows'] > 0]['AdCode'].astype(str).tolist())
                
                missing_districts = all_districts - processed_districts
                if missing_districts:
                    print(f"\n[提示] 发现 {len(missing_districts)} 个地区没有任何有效案件数据！")
                    print(f"部分缺失代码: {list(missing_districts)[:10]}")
                    print("这可能是由于原始数据中缺失这些地区，或者是映射逻辑未能识别。")
                    
                    # 写入缺失报告
                    missing_report_path = PROJECT_ROOT / "scripts" / "data_prep" / "missing_districts.csv"
                    missing_info = admin_df[admin_df['adcode'].isin(missing_districts)]
                    missing_info.to_csv(missing_report_path, index=False, encoding='utf-8-sig')
                    print(f"详细缺失列表已保存至: {missing_report_path}")
                else:
                    print("\n[成功] 所有目标地区均已包含案件数据！")
            except Exception as e:
                print(f"\n[警告] 检查地区完整性时出错: {e}")

        print(f"\n报告已保存至: {REPORT_PATH}")
        print("="*40)

    print(f"总耗时: {time.time() - t_start:.2f}s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--block_size", type=int, default=10)
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    filter_all_cases(max_rows=args.limit, block_size=args.block_size, test_mode=args.test)
