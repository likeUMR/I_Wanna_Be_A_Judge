import pandas as pd
import os

def clean_court_data(input_file, output_file):
    """
    清洗抓取到的法院数据
    1. 过滤名字中不包含“法院”的记录
    2. 过滤行政区划信息缺失的记录
    """
    if not os.path.exists(input_file):
        print(f"错误: 找不到输入文件 {input_file}")
        return

    print(f"正在读取数据: {input_file} ...")
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    initial_count = len(df)
    
    # 1. 过滤名字中不包含“法院”的记录
    # 确保 name 列是字符串并过滤
    df = df[df['name'].fillna('').str.contains('法院')]
    after_name_filter = len(df)
    
    # 2. 过滤行政区划信息缺失的记录
    # 检查 province, city, district 是否全为空
    # 这里根据需求，如果位置信息完全缺失（即这三个字段都为空）则删除
    # 或者根据 user 的描述 (,,,)，理解为这三个关键字段只要有一个缺失就可能不符合要求
    # 按照严格逻辑：省、市、区 必须都存在才保留
    mask = (
        df['province'].fillna('') != ''
    ) & (
        df['city'].fillna('') != ''
    ) & (
        df['district'].fillna('') != ''
    )
    
    df = df[mask]
    final_count = len(df)
    
    # 保存结果
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print("\n" + "="*30)
    print("清洗报告")
    print("="*30)
    print(f"原始记录数: {initial_count}")
    print(f"过滤非法院名后: {after_name_filter} (删除了 {initial_count - after_name_filter} 条)")
    print(f"过滤缺失位置信息后: {final_count} (删除了 {after_name_filter - final_count} 条)")
    print(f"最终保留记录数: {final_count}")
    print(f"清洗后的数据已保存至: {output_file}")

if __name__ == "__main__":
    # 使用相对路径，指向项目根目录下的 data 文件夹
    # 当前脚本在 scripts/data_prep/geo_data/，所以需要向上退三级
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    INPUT_PATH = os.path.join(BASE_DIR, 'data', 'china_courts_osm.csv')
    OUTPUT_PATH = os.path.join(BASE_DIR, 'data', 'china_courts_cleaned.csv')
    
    clean_court_data(INPUT_PATH, OUTPUT_PATH)

