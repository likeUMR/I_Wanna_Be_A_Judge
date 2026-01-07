import os
import pandas as pd
from collections import Counter
from typing import Dict

def process_cause_of_action(input_dir: str, output_file: str):
    """
    统计判决中案由和罪名的出现频率，并生成并列对比表格
    """
    if not os.path.exists(input_dir):
        print(f"错误: 目录不存在: {input_dir}")
        return
    
    cause_counter = Counter()  # 案由计数器
    crime_counter = Counter()  # 罪名计数器
    csv_files = []
    
    # 遍历目录获取所有CSV文件
    for root, _, files in os.walk(input_dir):
        for f in files:
            if f.lower().endswith('.csv'):
                csv_files.append(os.path.join(root, f))
    
    if not csv_files:
        print(f"警告: 在 {input_dir} 中未找到CSV文件")
        return

    print(f"找到 {len(csv_files)} 个CSV文件，开始处理...")
    
    total_processed = 0
    for csv_file in csv_files:
        try:
            # 同时读取'案由'和'罪名'列
            df = pd.read_csv(csv_file, usecols=lambda x: x in ['案由', '罪名'], on_bad_lines='skip')
            
            # 统计案由
            if '案由' in df.columns:
                counts = df['案由'].value_counts()
                for val, count in counts.items():
                    if pd.isna(val): continue
                    cause_counter[str(val).strip()] += count
            
            # 统计罪名
            if '罪名' in df.columns:
                counts = df['罪名'].value_counts()
                for val, count in counts.items():
                    if pd.isna(val): continue
                    crime_counter[str(val).strip()] += count
            
            total_processed += 1
            if total_processed % 5000 == 0:
                print(f"已处理 {total_processed}/{len(csv_files)} 个文件...")
                
        except Exception as e:
            # print(f"  处理文件 {os.path.basename(csv_file)} 时出错: {e}")
            continue
    
    # 准备排序后的数据
    sorted_cause = sorted(cause_counter.items(), key=lambda x: x[1], reverse=True)
    sorted_crime = sorted(crime_counter.items(), key=lambda x: x[1], reverse=True)
    
    # 确定最大行数，用于并列合并
    max_len = max(len(sorted_cause), len(sorted_crime))
    
    # 构建 4 列结果数据
    final_data = []
    for i in range(max_len):
        row = []
        # 案由部分
        if i < len(sorted_cause):
            row.extend([sorted_cause[i][0], sorted_cause[i][1]])
        else:
            row.extend(["", ""])
        
        # 罪名部分
        if i < len(sorted_crime):
            row.extend([sorted_crime[i][0], sorted_crime[i][1]])
        else:
            row.extend(["", ""])
        
        final_data.append(row)
    
    # 创建 DataFrame
    result_df = pd.DataFrame(final_data, columns=['案由', '案由出现次数', '罪名', '罪名出现次数'])
    
    # 保存结果
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n统计完成！处理文件总数: {total_processed}")
    print(f"案由种类: {len(cause_counter)}, 罪名种类: {len(crime_counter)}")
    print(f"结果已保存到: {output_file}")

if __name__ == "__main__":
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 默认项目根目录下的 public/data
    project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
    
    INPUT_DIR = os.path.join(project_root, 'public', 'data')
    OUTPUT_FILE = os.path.join(current_dir, 'cause_of_action_statistics.csv')
    
    # 如果 public/data 不存在，尝试使用 citation_utils.py 中提到的路径（如果适用）
    if not os.path.exists(INPUT_DIR):
        print(f"警告: 默认路径 {INPUT_DIR} 不存在，请检查数据存放位置。")
    else:
        process_cause_of_action(INPUT_DIR, OUTPUT_FILE)
