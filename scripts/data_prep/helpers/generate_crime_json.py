import os
import pandas as pd
import json

def generate_crime_json(input_file: str, output_file: str, top_n: int = 300):
    """
    将统计好的案由数据转换为前端可用的 JSON 格式，并按权重采样。
    """
    if not os.path.exists(input_file):
        print(f"错误: 输入文件不存在: {input_file}")
        return

    print(f"正在读取: {input_file}")
    df = pd.read_csv(input_file)
    
    # 案由列名可能在不同版本中有差异，优先取'案由'
    col_name = '案由' if '案由' in df.columns else '罪名'
    count_col = '案由出现次数' if '案由出现次数' in df.columns else '出现次数'
    
    # 清洗数据
    df = df.dropna(subset=[col_name, count_col])
    
    # 获取前 N 个最频繁的罪名
    # 我们按次数排序并取前 N 个
    top_crimes = df.sort_values(by=count_col, ascending=False).head(top_n)
    
    # 构造字典列表
    result = []
    for _, row in top_crimes.iterrows():
        result.append({
            "name": str(row[col_name]).strip(),
            "count": int(row[count_col])
        })
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"生成成功: {output_file} (包含 {len(result)} 个罪名)")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
    
    INPUT_FILE = os.path.join(current_dir, 'cause_of_action_statistics.csv')
    OUTPUT_FILE = os.path.join(project_root, 'public', 'crimes.json')
    
    generate_crime_json(INPUT_FILE, OUTPUT_FILE)
