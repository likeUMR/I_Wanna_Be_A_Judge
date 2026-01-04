import os
import re
import pandas as pd
from typing import List, Dict
from functools import lru_cache

class LocationMapper:
    def __init__(self, csv_path: str):
        self.districts = []
        self.name_to_districts = {} 
        if not os.path.exists(csv_path):
            print(f"错误: 找不到行政区划文件 {csv_path}")
            return
        try:
            # 必须使用 utf-8-sig 处理 Windows 下的 BOM
            df = pd.read_csv(csv_path, header=None, names=['name', 'adcode', 'p1', 'p2'], dtype={'adcode': str}, encoding='utf-8-sig')
            
            # 预处理：只保留区县级单位 (adcode 末两位通常非 00)
            # 或者像东莞(441900)、中山(442000)这种特殊的不设区地级市
            self.districts = []
            for d in df.to_dict('records'):
                code = str(d['adcode'])
                # 排除省级 (xx0000) 和 大部分地级市 (xxxx00)
                if not code.endswith('00') or code in ['441900', '442000']:
                    self.districts.append(d)
            
            # 建立索引：支持全名、简称、以及带父级的组合名
            for d in self.districts:
                name = str(d['name']).strip()
                if not name: continue
                
                # 1. 全名索引 (如 "永昌县")
                self._add_to_index(name, d)
                
                # 2. 简称索引 (如 "永昌")
                short_name = re.sub(r'(省|市|自治区|特别行政区|区|县|盟|旗)$', '', name)
                if len(short_name) >= 2:
                    self._add_to_index(short_name, d)
                
                # 3. 组合索引 (如 "金昌市永昌县")
                p1 = str(d['p1']) if pd.notna(d['p1']) else ""
                if p1:
                    self._add_to_index(p1 + name, d)
                    short_p1 = re.sub(r'(省|市|区|县)$', '', p1)
                    if len(short_p1) >= 2:
                        self._add_to_index(short_p1 + name, d)

        except Exception as e:
            print(f"加载行政区划失败: {e}")

    def _add_to_index(self, key, dist_obj):
        if key not in self.name_to_districts:
            self.name_to_districts[key] = []
        if dist_obj not in self.name_to_districts[key]:
            self.name_to_districts[key].append(dist_obj)

    @lru_cache(maxsize=8192)
    def map(self, region: str, court: str) -> str:
        region = str(region).strip() if pd.notna(region) and region != 'nan' else ""
        court = str(court).strip() if pd.notna(court) and court != 'nan' else ""
        
        # 提取法院名中的所有中文字符串作为地名候选
        court_clean = re.sub(r'(人民法院|法院|法庭|派出法庭)$', '', court)
        
        # 尝试匹配策略：从长到短
        # 1. 直接匹配清理后的法院名前缀
        for i in range(len(court_clean), 1, -1):
            candidate_key = court_clean[:i]
            if candidate_key in self.name_to_districts:
                res = self._pick_best(self.name_to_districts[candidate_key], region, court)
                if res: return res

        # 2. 如果没匹配到，尝试在 court_clean 中寻找已知的区县名
        best_match = None
        max_len = 0
        for name_key in self.name_to_districts:
            if name_key in court_clean and len(name_key) > max_len:
                res = self._pick_best(self.name_to_districts[name_key], region, court)
                if res:
                    best_match = res
                    max_len = len(name_key)
        
        if best_match: return best_match

        # 3. 最后尝试 region
        if region and region in self.name_to_districts:
            return self._pick_best(self.name_to_districts[region], region, court)

        return ""

    def _pick_best(self, candidates, region, court):
        # 严格过滤：必须是区县级代码
        valid = [d for d in candidates if not str(d['adcode']).endswith('00') or str(d['adcode']) in ['441900', '442000']]
        if not valid: return ""
        
        # 如果有多个，根据 region 校验
        if len(valid) > 1 and region:
            consistent = []
            for d in valid:
                p1 = str(d['p1']) if pd.notna(d['p1']) else ""
                p2 = str(d['p2']) if pd.notna(d['p2']) else ""
                if (p1 and p1 in region) or (p2 and p2 in region) or (region in p1) or (region in p2):
                    consistent.append(d)
            if consistent: valid = consistent

        # 按名称长度排序，越长越精确
        valid.sort(key=lambda x: len(str(x['name'])), reverse=True)
        return str(valid[0]['adcode'])
