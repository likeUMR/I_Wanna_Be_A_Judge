import os
import re
import pandas as pd
from collections import Counter
from typing import List, Tuple, Dict

# 中文数字转阿拉伯数字映射
CN_NUM = {
    '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '壹': 1, '贰': 2, '叁': 3, '肆': 4, '伍': 5, '陆': 6, '柒': 7, '捌': 8, '玖': 9, '拾': 10,
    '佰': 100, '仟': 1000, '万': 10000, '百': 100, '千': 1000, '两': 2
}

def cn_to_an(cn_str: str) -> int:
    """全面支持中文数字转整数，优化用于法条编号和金额转换"""
    if not cn_str: return 0
    if isinstance(cn_str, (int, float)): return int(cn_str)
    
    cn_str = str(cn_str).strip().replace('元', '').replace('整', '').replace(',', '')
    if cn_str.isdigit(): return int(cn_str)
    
    # 处理纯阿拉伯数字+单位的情况，如 "1.5万"
    if re.match(r'^[\d.]+[万]$', cn_str):
        num = float(cn_str[:-1])
        return int(num * 10000)

    units = {'万': 10000, '仟': 1000, '千': 1000, '佰': 100, '百': 100, '拾': 10, '十': 10}
    curr_unit = 1
    res = 0
    
    # 从右往左处理
    for char in reversed(cn_str):
        if char in units:
            u = units[char]
            if u > curr_unit: curr_unit = u
            else: curr_unit *= u
        elif char in CN_NUM:
            val = CN_NUM[char]
            res += val * curr_unit
        elif char.isdigit():
            res += int(char) * curr_unit
            
    # 特殊处理 "十" 开头的数字，如 "十一"
    if cn_str.startswith('十') or cn_str.startswith('拾'):
        if len(cn_str) == 1: res = 10
        elif len(cn_str) > 1 and cn_str[1] in CN_NUM and CN_NUM[cn_str[1]] < 10:
            res = 10 + CN_NUM[cn_str[1]]

    return res if res > 0 else (int(cn_str) if cn_str.isdigit() else 0)

def normalize_law_name(law_name: str) -> str:
    """标准化法律名称"""
    if not law_name: return ""
    law_name = law_name.strip().replace('（', '(').replace('）', ')')
    # 移除常见的引导词
    law_name = re.sub(r'^(?:依照|根据|根据|遵照)', '', law_name)
    return law_name

def parse_article_number(article_str: str) -> Tuple[int, int]:
    """解析法条编号字符串，返回(条号, 款号)"""
    if not article_str: return (0, 0)
    article_str = article_str.strip()
    
    article_match = re.search(r'第([^条]+)条', article_str)
    if not article_match: return (0, 0)
    
    article_num = cn_to_an(article_match.group(1))
    paragraph_match = re.search(r'第([^款]+)款', article_str)
    paragraph_num = cn_to_an(paragraph_match.group(1)) if paragraph_match else 0
    
    return (article_num, paragraph_num)

def parse_citations(citation_text: str) -> List[str]:
    """解析法律依据字符串，返回标准化后的引用列表"""
    if not citation_text or pd.isna(citation_text): return []
    citation_text = str(citation_text).strip()
    
    citations = []
    # 改进的正则：支持“依照《...》第...条”这种格式，且更兼容分隔符
    law_pattern = r'《([^》]+)》[:：\s]*([^；;《]+?)(?=；|;|《|$|之规定)'
    matches = re.finditer(law_pattern, citation_text)
    
    for match in matches:
        law_name = normalize_law_name(match.group(1))
        article_string = match.group(2).strip()
        
        # 分割法条，处理多种分隔符
        article_parts = re.split(r'[，,、；\s]', article_string)
        for part in article_parts:
            part = part.strip()
            if not part: continue
            
            # 如果部分中不包含“条”，可能是之前的条的后续款，这里简单处理
            if '条' not in part: continue
            
            article_num, paragraph_num = parse_article_number(part)
            if article_num == 0: continue
            
            if paragraph_num > 0:
                citations.append(f"《{law_name}》第{article_num}条第{paragraph_num}款")
            else:
                citations.append(f"《{law_name}》第{article_num}条")
    
    return citations

def process_csv_files(input_dir: str, output_file: str):
    """统计法律依据出现次数"""
    if not os.path.exists(input_dir):
        print(f"错误: 目录不存在: {input_dir}"); return
    
    citation_counter = Counter()
    csv_files = [os.path.join(root, f) for root, _, files in os.walk(input_dir) for f in files if f.lower().endswith('.csv')]
    
    total_rows = 0
    for csv_file in csv_files:
        print(f"正在处理: {os.path.basename(csv_file)}...")
        try:
            df = pd.read_csv(csv_file, usecols=lambda x: x == '法律依据', on_bad_lines='skip')
            if '法律依据' not in df.columns: continue
            
            for text in df['法律依据'].dropna():
                citations = parse_citations(str(text))
                citation_counter.update(citations)
                total_rows += 1
        except Exception as e:
            print(f"  错误: {e}"); continue
    
    result_df = pd.DataFrame(sorted(citation_counter.items(), key=lambda x: x[1], reverse=True), columns=['法律依据', '出现次数'])
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"结果已保存到: {output_file}")

if __name__ == "__main__":
    INPUT_DIR = r'F:\素材\游戏制作\裁判文书\裁判文书全量数据\structured_results'
    OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'citation_statistics.csv')
    process_csv_files(INPUT_DIR, OUTPUT_FILE)
