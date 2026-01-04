import json
import re
import os

def chinese_to_arabic(cn):
    units = {'十': 10, '百': 100, '千': 1000}
    digits = {'零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
    
    if not cn:
        return "0"
    
    suffix = ""
    if '之' in cn:
        parts = cn.split('之')
        cn = parts[0]
        suffix = "-" + str(digits.get(parts[1], parts[1]))
        
    res = 0
    tmp = 0
    for char in cn:
        if char in digits:
            tmp = digits[char]
        elif char in units:
            unit = units[char]
            if tmp == 0:
                tmp = 1
            res += tmp * unit
            tmp = 0
    res += tmp
    return str(res) + suffix

def structure_law(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    law_data = {
        "title": "中华人民共和国刑法",
        "parts": []
    }

    current_part = None
    current_chapter = None
    current_section = None
    current_article = None

    # Using [ \t　] to be explicit about spaces including ideographic space
    part_re = re.compile(r'^[ \t　]*第([一二三四五六七八九十百]+)编[ \t　]+(.*)')
    chapter_re = re.compile(r'^[ \t　]*第([一二三四五六七八九十百]+)章[ \t　]+(.*)')
    section_re = re.compile(r'^[ \t　]*第([一二三四五六七八九十百]+)节[ \t　]+(.*)')
    # Updated article regex to match the pattern: 第[数]条　【[标题]】[内容]
    article_re = re.compile(r'^[ \t　]*第([一二三四五六七八九十百]+条(?:之[一二三四五六七八九十]+)?)　【(.*?)】(.*)')

    found_content = False
    line_count = 0

    for line in lines:
        line_count += 1
        # Skip TOC (approx first 60 lines)
        if line_count < 60 and not found_content:
            if "第一编" in line and "总则" in line and not line.strip().startswith("目录"):
                # Potential start of content
                pass
            else:
                continue

        line_content = line.rstrip()
        if not line_content.strip():
            continue
            
        part_match = part_re.match(line_content)
        if part_match:
            found_content = True
            part_num_cn = part_match.group(1)
            part_title = part_match.group(2)
            current_part = {
                "id": chinese_to_arabic(part_num_cn),
                "title": part_title,
                "chapters": []
            }
            law_data["parts"].append(current_part)
            current_chapter = None
            current_section = None
            current_article = None
            continue

        chapter_match = chapter_re.match(line_content)
        if chapter_match:
            found_content = True
            chapter_num_cn = chapter_match.group(1)
            chapter_title = chapter_match.group(2)
            current_chapter = {
                "id": chinese_to_arabic(chapter_num_cn),
                "title": chapter_title,
                "sections": [],
                "articles": []
            }
            if current_part:
                current_part["chapters"].append(current_chapter)
            current_section = None
            current_article = None
            continue

        section_match = section_re.match(line_content)
        if section_match:
            found_content = True
            section_num_cn = section_match.group(1)
            section_title = section_match.group(2)
            current_section = {
                "id": chinese_to_arabic(section_num_cn),
                "title": section_title,
                "articles": []
            }
            if current_chapter:
                current_chapter["sections"].append(current_section)
            current_article = None
            continue

        article_match = article_re.match(line_content)
        if article_match:
            found_content = True
            art_num_full = article_match.group(1)
            article_num_cn = art_num_full.replace('条', '')
            article_id = chinese_to_arabic(article_num_cn)
            article_title = article_match.group(2)
            article_text = article_match.group(3)
            
            current_article = {
                "id": article_id,
                "num_cn": "第" + art_num_full,
                "title": article_title,
                "content": article_text
            }
            
            if current_section:
                current_section["articles"].append(current_article)
            elif current_chapter:
                current_chapter["articles"].append(current_article)
            continue

        if current_article and found_content:
            # Check if it's a new article but without title (unlikely in this file)
            # or just continuation
            current_article["content"] += "\n" + line_content.strip()

    return law_data

if __name__ == "__main__":
    input_file = "data/中华人民共和国刑法.txt"
    output_file = "data/criminal_law_structured.json"
    
    law_json = structure_law(input_file)
    
    # Filter empty parts from TOC artifacts
    law_json["parts"] = [p for p in law_json["parts"] if p["chapters"]]
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(law_json, f, ensure_ascii=False, indent=2)
    
    print(f"Structured law saved to {output_file}")
