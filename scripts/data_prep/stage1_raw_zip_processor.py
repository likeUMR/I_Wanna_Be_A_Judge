import os
import zipfile
import pandas as pd
import shutil
import re

# ================= 配置区 =================
# 源数据根目录
SOURCE_DIR = r'F:\素材\游戏制作\裁判文书\裁判文书全量数据'
# 处理后的数据保存路径
OUTPUT_DIR = os.path.join(SOURCE_DIR, 'processed_results')
# 临时解压目录
TEMP_EXTRACT_DIR = os.path.join(SOURCE_DIR, 'temp_processing')

# CSV 列名（根据描述定义，如果实际列名不同请修改）
COL_CASE_TYPE = '案件类型'
COL_PROCEDURE = '审理程序'
COL_CAUSE = '案由'
COL_PARTIES = '当事人'

# 过滤条件配置
TARGET_CASE_TYPE = '刑事案件'
TARGET_PROCEDURES = ['一审']
MAX_PARTIES_LEN = 4
# ==========================================

def process_csv(file_path, output_file):
    """
    分块读取 CSV 并过滤数据
    """
    count = 0
    # 注意：中国裁判文书数据常见编码为 utf-8-sig 或 gbk
    # 这里先尝试 utf-8-sig (处理带 BOM 的 UTF8)
    try:
        # 使用 chunksize 分块读取，每块 5000 行
        chunks = pd.read_csv(file_path, chunksize=5000, encoding='utf-8-sig', on_bad_lines='skip')
        
        for i, chunk in enumerate(chunks):
            # 1. 案件类型为 刑事案件
            # 2. 审理程序为 一审或二审
            # 3. 案由不为空
            # 4. 当事人字数 <= 4
            
            mask = (
                (chunk[COL_CASE_TYPE] == TARGET_CASE_TYPE) &
                (chunk[COL_PROCEDURE].isin(TARGET_PROCEDURES)) &
                (chunk[COL_CAUSE].notna()) &
                (chunk[COL_CAUSE] != '') &
                (chunk[COL_PARTIES].astype(str).str.len() <= MAX_PARTIES_LEN)
            )
            
            filtered_chunk = chunk[mask]
            
            if not filtered_chunk.empty:
                # 写入文件，如果是第一次写入则带表头，否则追加
                is_first = not os.path.exists(output_file)
                filtered_chunk.to_csv(output_file, mode='a', index=False, header=is_first, encoding='utf-8-sig')
                count += len(filtered_chunk)
                
    except Exception as e:
        print(f"  读取文件 {os.path.basename(file_path)} 出错: {e}")
        
    return count

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # 报告记录
    report = {}
    total_valid_rows = 0

    # 1. 获取所有 zip 文件
    zip_files = [f for f in os.listdir(SOURCE_DIR) if f.endswith('.zip')]
    # 按年份排序（简单从文件名提取数字）
    zip_files.sort(key=lambda x: re.findall(r'\d+', x)[0] if re.findall(r'\d+', x) else x)

    for zip_name in zip_files:
        year_match = re.search(r'(\d{4})年', zip_name)
        year_label = year_match.group(1) if year_match else zip_name
        
        print(f"正在处理: {zip_name} ...")
        zip_path = os.path.join(SOURCE_DIR, zip_name)
        
        # 2. 解压 zip
        if os.path.exists(TEMP_EXTRACT_DIR):
            shutil.rmtree(TEMP_EXTRACT_DIR)
        os.makedirs(TEMP_EXTRACT_DIR)
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(TEMP_EXTRACT_DIR)
        except Exception as e:
            print(f"  解压失败: {e}")
            continue

        # 3. 遍历解压出来的 CSV 文件
        year_count = 0
        output_year_file = os.path.join(OUTPUT_DIR, f'filtered_{year_label}.csv')
        
        # 递归查找所有 csv（处理可能存在的嵌套文件夹）
        for root, dirs, files in os.walk(TEMP_EXTRACT_DIR):
            for file in files:
                if file.lower().endswith('.csv'):
                    csv_path = os.path.join(root, file)
                    print(f"  分析中: {file}")
                    rows = process_csv(csv_path, output_year_file)
                    year_count += rows
                    
                    # 立即删除源 CSV 以节省空间
                    os.remove(csv_path)

        # 记录年份报告
        report[year_label] = year_count
        total_valid_rows += year_count
        print(f"--- {year_label} 处理完成，有效行数: {year_count} ---")

        # 清理临时目录
        shutil.rmtree(TEMP_EXTRACT_DIR)

    # 4. 生成报告
    print("\n" + "="*30)
    print("处理报告")
    print("="*30)
    for yr, cnt in report.items():
        print(f"{yr}年: {cnt} 行")
    print("-" * 30)
    print(f"总有效行数: {total_valid_rows}")
    print(f"结果已保存至: {OUTPUT_DIR}")

if __name__ == '__main__':
    main()