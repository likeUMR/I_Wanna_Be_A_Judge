import os
import re
import pandas as pd
from typing import List, Dict
from functools import lru_cache

class LocationMapper:
    def __init__(self, csv_path: str):
        self.districts = []
        self.name_map = {} # 建立名称到行政区划对象的快速索引
        if not os.path.exists(csv_path):
            return
        try:
            # name, adcode, p1, p2
            # 强制指定 adcode 为字符串，防止出现 .0
            df = pd.read_csv(csv_path, header=None, names=['name', 'adcode', 'p1', 'p2'], dtype={'adcode': str})
            # 只保留区县级 (adcode 最后两位非00，且不为空)
            df_districts = df[df['adcode'].str.strip().str.endswith('00') == False]
            self.districts = df_districts.to_dict('records')
            
            # 建立索引：支持全名匹配
            for d in self.districts:
                name = str(d['name'])
                if name not in self.name_map:
                    self.name_map[name] = []
                self.name_map[name].append(d)
                
        except Exception as e:
            print(f"加载行政区划失败: {e}")

    @lru_cache(maxsize=4096)
    def map(self, region: str, court: str) -> str:
        region = str(region) if pd.notna(region) and region != 'nan' else ""
        court = str(court) if pd.notna(court) and court != 'nan' else ""
        
        # 1. 提取法院所在区域名 (例如: "山东省昌邑市人民法院" -> "昌邑市")
        court_area = ""
        m = re.search(r'([\u4e00-\u9fa5]+?)(?:法院|人民法院)', court)
        if m:
            court_area = m.group(1)

        # 2. 确定候选范围：不再遍历全量 self.districts
        candidates = []
        
        # 策略：如果 region 或 court_area 命中索引，直接使用候选者
        # 注意：原代码逻辑是 (name == court_area or court_area.endswith(name)) or (name == region or region.endswith(name))
        # 为了保持一致，我们需要处理后缀匹配
        
        # 先尝试精准匹配和后缀匹配
        search_terms = []
        if court_area: search_terms.append(court_area)
        if region: search_terms.append(region)
        
        # 为了性能，我们仍然需要一个列表来处理后缀匹配，但只在必要时遍历
        # 实际上，绝大多数情况下是名称相等。如果一定要保持 endswith 逻辑：
        for d in self.districts:
            name = str(d['name'])
            if len(name) < 2: continue
            
            is_court_match = court_area and (name == court_area or court_area.endswith(name))
            is_region_match = region and (name == region or region.endswith(name))
            
            if is_court_match or is_region_match:
                p1 = str(d['p1']) if pd.notna(d['p1']) else ""
                p2 = str(d['p2']) if pd.notna(d['p2']) else ""
                
                parent_consistent = True
                if region:
                    has_parent_info = False
                    for p in [p1, p2]:
                        if p and p in region:
                            has_parent_info = True
                            break
                    
                    if not has_parent_info and len(region) > len(name):
                        parent_consistent = False
                
                if parent_consistent:
                    candidates.append(d)

        if not candidates: return ""
        
        unique_codes = list(set([str(m['adcode']) for m in candidates if m['adcode']]))
        if len(unique_codes) == 1:
            return unique_codes[0]
            
        if court_area:
            exact = [str(m['adcode']) for m in candidates if str(m['name']) == court_area]
            if len(exact) == 1:
                return exact[0]

        return ""
