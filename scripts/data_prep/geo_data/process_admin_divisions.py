import csv
import os
import requests
import json

def get_amap_key(config_path):
    """从 App.jsx 或 config.js 中提取高德 Key"""
    # 优先从 config.js 读取，因为它是被 App.jsx 引入的源
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 简单的正则匹配或查找
            import re
            match = re.search(r"AMAP_KEY:\s*['\"]([^'\"]+)['\"]", content)
            if match:
                return match.group(1)
    return None

def fetch_admin_divisions(api_key):
    """使用高德 API 获取行政区划数据"""
    print("Fetching data from Amap API...")
    url = "https://restapi.amap.com/v3/config/district"
    params = {
        "key": api_key,
        "keywords": "中国",
        "subdistrict": 3,
        "extensions": "base"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "1" and data.get("districts"):
            # 返回的是“中国”下的子级（即各省）
            return data["districts"][0].get("districts", [])
        else:
            print(f"API Error: {data.get('info')}")
            return []
    except Exception as e:
        print(f"Request failed: {e}")
        return []

def process_admin_divisions(output_file, api_key):
    provinces = fetch_admin_divisions(api_key)
    if not provinces:
        print("No data fetched. Aborting.")
        return

    results = []
    
    # 直辖市编码
    municipalities = {'110000', '120000', '310000', '500000'}

    for province in provinces:
        p_name = province["name"]
        p_code = province["adcode"]
        # 省级：[名, 码, 上级, 上上级]
        results.append([p_name, p_code, "", ""])
        
        is_municipality = p_code in municipalities
        
        cities = province.get("districts", [])
        for city in cities:
            c_name = city["name"]
            c_code = city["adcode"]
            c_level = city.get("level")
            
            # 只保留地级市/区县级别以上，过滤掉街道/乡镇 (street)
            if c_level not in ['province', 'city', 'district']:
                continue
            
            if is_municipality:
                # 直辖市：跳过中间的“北京城区/市辖区”层，直接将区县挂在直辖市下
                # 这样符合 [区县名, 区县码, 直辖市名, ""] 的格式
                districts = city.get("districts", [])
                for district in districts:
                    d_name = district["name"]
                    d_code = district["adcode"]
                    d_level = district.get("level")
                    # 过滤掉街道级别和代码重复的项
                    if d_level not in ['province', 'city', 'district'] or d_code == c_code:
                        continue
                    results.append([d_name, d_code, p_name, ""])
            else:
                # 普通省份
                results.append([c_name, c_code, p_name, ""])
                
                districts = city.get("districts", [])
                for district in districts:
                    d_name = district["name"]
                    d_code = district["adcode"]
                    d_level = district.get("level")
                    
                    # 过滤掉街道级别和代码重复的项 (防止出现 文昌市 -> 文教镇 且码相同的情况)
                    if d_level not in ['province', 'city', 'district'] or d_code == c_code:
                        continue
                    
                    # 区县级：[名, 码, 市名, 省名]
                    results.append([d_name, d_code, c_name, p_name])

    # Write to CSV
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(results)
    
    print(f"Successfully processed {len(results)} divisions (County level and above).")

if __name__ == "__main__":
    # 当前脚本在 scripts/data_prep/geo_data/，向上退三级到根目录
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    CONFIG_PATH = os.path.join(BASE_DIR, 'src', 'config.js')
    OUTPUT_PATH = os.path.join(BASE_DIR, 'data', 'processed_admin_divisions.csv')
    
    api_key = get_amap_key(CONFIG_PATH)
    if not api_key:
        print(f"Could not find AMAP_KEY in {CONFIG_PATH}")
        # 备选：如果 config.js 没找到，可以尝试直接搜索 App.jsx，但通常 config.js 是正确的
    else:
        process_admin_divisions(OUTPUT_PATH, api_key)
        print(f"Processing complete. Output saved to {OUTPUT_PATH}")

