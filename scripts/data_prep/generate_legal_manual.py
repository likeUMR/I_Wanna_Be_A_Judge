import json
import csv
import re
import os

# 配置参数
MAX_ARTICLES = 20  # 控制包含多少个高频法条

def generate_manual():
    stats_file = "scripts/data_prep/helpers/citation_statistics.csv"
    structured_law_file = "data/criminal_law_structured.json"
    output_file = "public/legal_manual.json"

    with open(structured_law_file, 'r', encoding='utf-8') as f:
        law_data = json.load(f)

    article_map = {}
    def process_node(node):
        if isinstance(node, list):
            for item in node:
                process_node(item)
            return
            
        if "articles" in node:
            for art in node["articles"]:
                article_map[art["id"]] = art
        
        # Recursively process hierarchy
        if "parts" in node:
            process_node(node["parts"])
        if "chapters" in node:
            process_node(node["chapters"])
        if "sections" in node:
            process_node(node["sections"])

    process_node(law_data)

    top_citations = []
    
    # Using utf-8-sig as we verified it works for the content
    with open(stats_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        
        for row in reader:
            if not row or len(row) < 2: continue
            citation = row[0]
            count_str = row[1]
            
            # Match Criminal Law but skip 1997 version
            if "刑法" in citation and "(1997年)" not in citation:
                nums = re.findall(r'(\d+)', citation)
                if nums:
                    base_id = nums[0]
                    suffix = ""
                    if "之一" in citation: suffix = "-1"
                    elif "之二" in citation: suffix = "-2"
                    elif "之三" in citation: suffix = "-3"
                    elif "之四" in citation: suffix = "-4"
                    elif "之五" in citation: suffix = "-5"
                    
                    art_id = base_id + suffix
                    if art_id in article_map:
                        top_citations.append({
                            "id": art_id,
                            "citation": citation,
                            "count": int(count_str)
                        })
            
            if len(top_citations) >= MAX_ARTICLES:
                break
        
    manual_articles = []
    for cite in top_citations:
        art = article_map[cite["id"]]
        manual_articles.append({
            "id": art["id"],
            "num_cn": art["num_cn"],
            "title": art["title"],
            "content": art["content"],
            "citation_count": cite["count"]
        })

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(manual_articles, f, ensure_ascii=False, indent=2)

    print(f"Legal manual (top {len(manual_articles)} articles, max limit: {MAX_ARTICLES}) saved to {output_file}")

if __name__ == "__main__":
    generate_manual()
