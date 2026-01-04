import os
import re
import pandas as pd
import argparse
import time
import sys
import random
from typing import Dict, Any, List, Optional
from concurrent.futures import ProcessPoolExecutor
import numpy as np

# 导入自定义模块
from extractor import JudgmentExtractor, LocationMapper

# 全局变量，用于多进程初始化
extractor = None
loc_mapper = None

def init_worker(admin_csv):
    """初始化子进程的提取器和映射器"""
    global extractor, loc_mapper
    extractor = JudgmentExtractor()
    loc_mapper = LocationMapper(admin_csv)

def process_batch(batch_tuple):
    """处理一批数据，显式统计缺失情况并返回"""
    rows_list, content_col, region_col, court_col, main_fields, sub_fields = batch_tuple
    batch_results = []
    
    # 局部统计
    batch_stats = {
        'total': 0,
        'perfect': 0,
        'main_missing_total': 0,
        'sub_missing_total': 0,
        'main_missing_rows': 0,
        'main_field_missing_counts': {f: 0 for f in main_fields},
        'sub_field_missing_counts': {f: 0 for f in sub_fields},
        'sample_main_missing_row': None
    }
    
    for row_dict in rows_list:
        batch_stats['total'] += 1
        try:
            ext = extractor.extract_all(row_dict.get(content_col, ''))
            region = row_dict.get(region_col, '') if region_col else ''
            court = row_dict.get(court_col, '') if court_col else ''
            ext['AdCode'] = loc_mapper.map(region, court)
        except Exception as e:
            ext = {}
        
        # 字段缺失统计 - 优化：排除布尔值和数值为 0 的情况
        missing_main = [f for f in main_fields if ext.get(f) in [None, ""]]
        missing_sub = [f for f in sub_fields if ext.get(f) in [None, ""]]
        
        for f in missing_main: batch_stats['main_field_missing_counts'][f] += 1
        for f in missing_sub: batch_stats['sub_field_missing_counts'][f] += 1
        
        ext['主字段缺失数量'] = len(missing_main)
        ext['主字段缺失'] = ",".join(missing_main)
        ext['子字段缺失数量'] = len(missing_sub)
        ext['子字段缺失'] = ",".join(missing_sub)
        
        if not missing_main and not missing_sub:
            batch_stats['perfect'] += 1
        
        if missing_main:
            batch_stats['main_missing_rows'] += 1
            batch_stats['main_missing_total'] += len(missing_main)
            if batch_stats['sample_main_missing_row'] is None:
                batch_stats['sample_main_missing_row'] = {**row_dict, **ext}
        
        batch_stats['sub_missing_total'] += len(missing_sub)
        batch_results.append({**row_dict, **ext})
    
    return batch_results, batch_stats

def safe_to_csv(df, path):
    """尝试写入CSV，如果文件被占用则重试"""
    for i in range(5):
        try:
            df.to_csv(path, index=False, encoding='utf-8-sig')
            return True
        except PermissionError:
            print(f"警告: 文件 {path} 被占用，请关闭它。5秒后重试 ({i+1}/5)...")
            time.sleep(5)
    print(f"错误: 无法写入文件 {path}，请手动关闭后重新运行。")
    return False

def process_directory(input_dir: str, output_dir: str, start_year: int = None, end_year: int = None, test_mode: bool = False):
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    
    # 初始化位置映射器路径
    # 尝试多种方式定位 public 目录
    possible_admin_paths = [
        # 1. 项目根目录 (从 scripts/data_prep/ 向上三级)
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "public", "processed_admin_divisions.csv"),
        # 2. 从当前工作目录找
        os.path.join(os.getcwd(), "public", "processed_admin_divisions.csv"),
        # 3. 如果在 scripts/data_prep 运行
        os.path.join(os.getcwd(), "..", "..", "public", "processed_admin_divisions.csv"),
    ]
    
    admin_csv = None
    for p in possible_admin_paths:
        if os.path.exists(p):
            admin_csv = p
            break
            
    if not admin_csv:
        print(f"[致命错误] 无法定位行政区划文件 processed_admin_divisions.csv")
        print(f"已尝试路径: {possible_admin_paths}")
        sys.exit(1)
        
    print(f"使用行政区划文件: {admin_csv}")
    
    # 定义字段
    main_fields = [
        "SECTION_1_被告人基本信息及前科劣迹", "SECTION_2_本案强制措施及羁押情况", 
        "SECTION_3_公诉机关及起诉信息", "SECTION_4_审理程序与诉讼参与情况", 
        "SECTION_5_经审理查明的犯罪事实", "SECTION_6_证据列举", 
        "SECTION_7_罪名认定理由", "SECTION_8_量刑情节分析", 
        "SECTION_9_判决法律依据", "SECTION_10_判决主文", 
        "SECTION_11_审判人员及日期"
    ]
    sub_fields = [
        '姓名', '性别', '年龄', '文化程度', '职业', 
        '是否未成年', '是否累犯', '是否初犯', '是否自首', '是否立功', 
        '是否取得谅解', '是否如实供述', '是否退赃', '是否未遂',
        'surrender_type', '案由', '主从犯身份', '特殊身体状况', '精神状态', 
        '涉案金额', '罚金', '罪名', '主刑', '出生日期', 'AdCode'
    ]

    files_to_process = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
    if not files_to_process:
        print(f"[致命错误] 输入目录 {input_dir} 中没有找到 CSV 文件！")
        sys.exit(1)
    if test_mode:
        # 测试模式：专门挑选 2013 年的数据
        files_to_process = [f for f in files_to_process if "2013" in f][:1]
        if not files_to_process:
            files_to_process = [f for f in os.listdir(input_dir) if f.endswith('.csv')][:1]
        print(f"测试模式: 仅处理 {len(files_to_process)} 个文件 (优先匹配 2013 年)")

    for filename in files_to_process:
        t_start = time.time()
        year_m = re.search(r'(\d{4})', filename)
        if year_m:
            year = int(year_m.group(1))
            if not test_mode and start_year and end_year and not (start_year <= year <= end_year): continue
            
        input_path = os.path.join(input_dir, filename)
        try:
            # 尝试不同编码读取
            try:
                if test_mode:
                    df = pd.read_csv(input_path, encoding='utf-8-sig', nrows=100)
                else:
                    df = pd.read_csv(input_path, encoding='utf-8-sig')
                # 检查是否成功读取到中文列名，如果全是乱码则尝试 gbk
                if not any('案' in str(c) or '法' in str(c) for c in df.columns):
                    raise ValueError("Encoding check failed")
            except Exception:
                if test_mode:
                    df = pd.read_csv(input_path, encoding='gbk', nrows=100)
                else:
                    df = pd.read_csv(input_path, encoding='gbk')
            
            # 统一列名映射
            col_map = {c: c for c in df.columns}
            content_col = next((c for c in df.columns if '全文' in str(c)), df.columns[0])
            region_col = next((c for c in df.columns if '所属地区' in str(c)), None)
            court_col = next((c for c in df.columns if '法院' in str(c)), None)
            
            if not region_col or not court_col:
                # 尝试通过索引定位：通常 3 是法院，4 是地区
                court_col = df.columns[3] if len(df.columns) > 3 else None
                region_col = df.columns[4] if len(df.columns) > 4 else None

        except Exception as e:
            print(f"无法读取 {filename}: {e}"); continue

        t_load = time.time()
        print(f"\n[{filename}] 正在加载: {len(df)} 行 (耗时: {t_load - t_start:.2f}s)")
        
        # 优化：批量任务切分
        max_workers = max(1, os.cpu_count() - 1)
        batch_size = 500
        # 将列名也传递进去
        rows_dicts = df.to_dict('records')
        batches = [
            (rows_dicts[i:i + batch_size], content_col, region_col, court_col, main_fields, sub_fields)
            for i in range(0, len(rows_dicts), batch_size)
        ]
        
        t_prep = time.time()
        print(f"任务准备完毕: {len(batches)} 个批次 (耗时: {t_prep - t_load:.2f}s)")
        
        final_rows = []
        global_stats = {
            'total': 0, 
            'perfect': 0, 
            'main_missing_total': 0,
            'sub_missing_total': 0,
            'main_missing_rows': 0,
            'main_field_missing_counts': {f: 0 for f in main_fields},
            'sub_field_missing_counts': {f: 0 for f in sub_fields},
            'sample_main_missing_row': None
        }

        # 使用多进程池执行批处理
        print(f"并行计算中 (使用 {max_workers} 个核心)...")
        with ProcessPoolExecutor(max_workers=max_workers, initializer=init_worker, initargs=(admin_csv,)) as pool:
            # map 现在返回 (batch_results, batch_stats)
            for batch_res, batch_s in pool.map(process_batch, batches):
                final_rows.extend(batch_res)
                
                # 快速合并统计信息
                global_stats['total'] += batch_s['total']
                global_stats['perfect'] += batch_s['perfect']
                global_stats['main_missing_total'] += batch_s['main_missing_total']
                global_stats['sub_missing_total'] += batch_s['sub_missing_total']
                global_stats['main_missing_rows'] += batch_s['main_missing_rows']
                
                for f in main_fields:
                    global_stats['main_field_missing_counts'][f] += batch_s['main_field_missing_counts'][f]
                for f in sub_fields:
                    global_stats['sub_field_missing_counts'][f] += batch_s['sub_field_missing_counts'][f]
                
                if global_stats['sample_main_missing_row'] is None and batch_s['sample_main_missing_row']:
                    global_stats['sample_main_missing_row'] = batch_s['sample_main_missing_row']

        t_calc = time.time()
        print(f"提取任务完成 (耗时: {t_calc - t_prep:.2f}s, 速率: {len(df)/(t_calc - t_prep):.1f}行/秒)")

        res_df = pd.DataFrame(final_rows)
        
        # 数据清洗与格式转换 (向量化操作提升效率)
        bool_fields = ['是否自首', '是否立功', '是否取得谅解', '是否如实供述', '是否未遂', '是否累犯', '是否初犯', '是否退赃', '是否未成年']
        for bf in bool_fields:
            if bf in res_df.columns:
                res_df[bf] = res_df[bf].fillna(0).astype(int)
        
        num_fields = ['罚金', '涉案金额', 'surrender_type']
        for nf in num_fields:
            if nf in res_df.columns:
                res_df[nf] = res_df[nf].fillna(0).astype(int)

        if 'AdCode' in res_df.columns:
            res_df['AdCode'] = res_df['AdCode'].fillna('').astype(str).apply(lambda x: x.split('.')[0] if '.' in x else x)
            res_df['AdCode'] = res_df['AdCode'].replace('nan', '')
            
        out_path = os.path.join(output_dir, f"structured_{filename}")
        safe_to_csv(res_df, out_path)

        summary_path = os.path.join(output_dir, f"summary_{filename.replace('.csv', '.txt')}")
        with open(summary_path, 'w', encoding='utf-8-sig') as f:
            f.write(f"总处理:{global_stats['total']}, 完美(无主子字段缺失):{global_stats['perfect']}, 有主字段缺失的行数:{global_stats['main_missing_rows']}\n")
            f.write(f"主字段缺失总数:{global_stats['main_missing_total']}, 子字段缺失总数:{global_stats['sub_missing_total']}\n")
            f.write("\n--- 主字段缺失统计 ---\n")
            f.write(", ".join([f"{k}:{v}" for k, v in global_stats['main_field_missing_counts'].items()]))
            f.write("\n\n--- 子字段缺失统计 ---\n")
            f.write(", ".join([f"{k}:{v}" for k, v in global_stats['sub_field_missing_counts'].items()]))
            
            if global_stats['sample_main_missing_row']:
                f.write("\n\n--- 主字段缺失样例 ---\n")
                f.write(f"主字段缺失内容: {global_stats['sample_main_missing_row'].get('主字段缺失')}\n")
                f.write(f"原文片段: {str(global_stats['sample_main_missing_row'].get(content_col, ''))[:500]}...\n")
        
        t_end = time.time()
        print(f"保存完毕 (总计耗时: {t_end - t_start:.2f}s)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start_year", type=int)
    parser.add_argument("--end_year", type=int)
    parser.add_argument("--input", type=str)
    parser.add_argument("--output", type=str)
    parser.add_argument("--test", action="store_true", help="测试模式：处理少量数据")
    args = parser.parse_args()

    INPUT = args.input if args.input else r'F:\素材\游戏制作\裁判文书\裁判文书全量数据\processed_results'
    OUTPUT = args.output if args.output else r'F:\素材\游戏制作\裁判文书\裁判文书全量数据\structured_results'
    
    if not os.path.exists(INPUT):
        INPUT = os.path.join(os.getcwd(), 'data', 'processed_results')
        OUTPUT = os.path.join(os.getcwd(), 'data', 'structured_results')

    if os.path.exists(INPUT):
        process_directory(INPUT, OUTPUT, args.start_year, args.end_year, test_mode=args.test)
        
        # 抽样检查逻辑：检查刚刚生成的文件
        print(f"\n{'='*50}\n【数据随机抽检】")
        
        # 查找刚刚生成的文件
        output_files = [f for f in os.listdir(OUTPUT) if f.startswith("structured_") and f.endswith(".csv")]
        if not output_files:
            print("没有找到生成的结果文件，无法抽检。")
        else:
            # 优先检查最新的文件
            output_files.sort(key=lambda x: os.path.getmtime(os.path.join(OUTPUT, x)), reverse=True)
            output_file = os.path.join(OUTPUT, output_files[0])
            
            print(f"正在抽检文件: {output_file}")
            try:
                # 显式指定 AdCode 为字符串
                df_sample = pd.read_csv(output_file, dtype={'AdCode': str}, encoding='utf-8-sig', nrows=1000)
                if not df_sample.empty:
                    # 检查 AdCode 填充情况
                    valid_adcodes = df_sample[df_sample['AdCode'].notna() & (df_sample['AdCode'] != '')]
                    print(f"抽检样本数: {len(df_sample)}, 有效 AdCode 数量: {len(valid_adcodes)}")
                    
                    if len(valid_adcodes) > 0:
                        samples = valid_adcodes.sample(min(2, len(valid_adcodes)))
                        for i, (idx, row) in enumerate(samples.iterrows()):
                            try:
                                print(f"\n--- 样例 {i+1} ---")
                                print(f"姓名: {row.get('姓名')} | 法院: {row.get('法院')} | AdCode: {row.get('AdCode')}")
                                print(f"案由: {row.get('案由')} | 刑期: {row.get('主刑')}")
                                print("-" * 30)
                            except Exception: pass
                    else:
                        print("警告: 抽检样本中没有任何有效的 AdCode！")
                        # 打印前几行看看 AdCode 列到底是什么
                        print("前 5 行 AdCode 列内容:")
                        print(df_sample['AdCode'].head().tolist())
                else:
                    print("结果文件为空，无法抽检。")
            except Exception as e:
                print(f"抽检过程出错: {e}")
        print(f"{'='*50}\n")
    else:
        print(f"路径不存在: {INPUT}")

# python D:\PROJECT\VSCode\AI+Game\I_Wanna_Be_A_Judge\scripts\data_prep\stage2_legal_info_extractor.py --start_year 2013 --end_year 2013