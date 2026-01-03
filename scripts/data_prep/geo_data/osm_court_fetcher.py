import requests
import pandas as pd
import time
import os

try:
    import zhconv
except ImportError:
    print("警告: 未发现 zhconv 库，繁简转换功能将不可用。请运行 'pip install zhconv' 安装。")
    zhconv = None

class OSMCourtFetcher:
    """
    使用 OpenStreetMap Overpass API 获取中国地区法院信息的类
    """
    
    # 多个备用服务器地址
    OVERPASS_SERVERS = [
        "https://overpass-api.de/api/interpreter",
        "https://lz4.overpass-api.de/api/interpreter",
        "https://z.overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"
    ]
    
    # 使用相对路径，指向项目根目录下的 data 文件夹
    # 当前脚本在 scripts/data_prep/geo_data/，所以需要向上退三级
    ADMIN_DIV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'data', 'processed_admin_divisions.csv')
    
    def __init__(self, timeout=300):
        self.timeout = timeout
        self.admin_divisions = self._load_admin_divisions()

    def _load_admin_divisions(self):
        """
        加载本地行政区划数据，用于补全信息
        """
        if not os.path.exists(self.ADMIN_DIV_FILE):
            print(f"警告: 未找到 {self.ADMIN_DIV_FILE}，行政区划自动补全将受限。")
            return []
        
        try:
            # 读取 CSV
            df = pd.read_csv(self.ADMIN_DIV_FILE, header=None, names=['name', 'code', 'parent_city', 'parent_province'])
            df = df.fillna('')
            return df.to_dict('records')
        except Exception as e:
            print(f"加载行政区划数据失败: {e}")
            return []

    def get_overpass_query(self):
        """
        优化后的 Overpass QL 查询语句
        - 使用 out tags center 极大减小响应数据量，避免 504
        - 精简正则匹配，去掉 i 标志提升性能
        """
        query = f"""
        [out:json][timeout:{self.timeout}];
        area["name:zh"="中国"][admin_level=2]->.china;
        (
          // 标准标签筛选
          node["amenity"~"courthouse|court"](area.china);
          way["amenity"~"courthouse|court"](area.china);
          relation["amenity"~"courthouse|court"](area.china);
          node["office"="court"](area.china);
          way["office"="court"](area.china);
          relation["office"="court"](area.china);
          
          // 名称模糊匹配（去掉 i 提升速度，中文不需要忽略大小写）
          node["name"~"法院"](area.china);
          way["name"~"法院"](area.china);
          relation["name"~"法院"](area.china);
        );
        out tags center;
        """
        return query

    def fetch_data(self):
        """
        发送请求并获取原始 JSON 数据，支持多服务器重试
        """
        query = self.get_overpass_query()
        
        for i, url in enumerate(self.OVERPASS_SERVERS):
            print(f"尝试从服务器 {i+1} 获取数据: {url}")
            try:
                # 稍微增加 requests 层的超时时间，确保 Overpass 内部 timeout 优先起作用
                response = requests.post(url, data={'data': query}, timeout=self.timeout + 20)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"服务器 {url} 请求失败: {e}")
                if i < len(self.OVERPASS_SERVERS) - 1:
                    print("尝试下一个备用服务器...")
                    time.sleep(2)  # 稍微等待
                else:
                    print("所有服务器均尝试失败。")
        return None

    def _infer_admin_info(self, court_name):
        """
        根据法院名称从本地行政区划库中推断省、市、区
        """
        province, city, district = '', '', ''
        if not court_name or not self.admin_divisions:
            return province, city, district

        matched_district = None
        for div in self.admin_divisions:
            name = div['name']
            if len(name) > 1 and name in court_name:
                if div['parent_city'] and div['parent_province']:
                    if not matched_district or len(name) > len(matched_district['name']):
                        matched_district = div
                elif div['parent_city'] and not div['parent_province']:
                    if not city: city = div['name']
                    if not province: province = div['parent_city']
                elif not div['parent_city']:
                    if not province: province = div['name']

        if matched_district:
            district = matched_district['name']
            city = matched_district['parent_city']
            province = matched_district['parent_province']
            
        return province, city, district

    def parse_results(self, data):
        """
        解析 JSON 结果并提取法院信息
        """
        if not data or 'elements' not in data:
            return []
        
        courts = []
        for element in data['elements']:
            tags = element.get('tags', {})
            if not tags: continue
            
            raw_name = tags.get('name:zh') or tags.get('name') or ''
            if not raw_name: continue
            
            name = zhconv.convert(raw_name, 'zh-cn') if zhconv else raw_name
            
            # center 模式下的坐标提取
            lat = element.get('lat') or element.get('center', {}).get('lat')
            lon = element.get('lon') or element.get('center', {}).get('lon')
            if not lat or not lon: continue
            
            province = tags.get('addr:province') or ''
            city = tags.get('addr:city') or ''
            district = tags.get('addr:district') or ''
            
            if not (province and city and district):
                inf_prov, inf_city, inf_dist = self._infer_admin_info(name)
                province = province or inf_prov
                city = city or inf_city
                district = district or inf_dist
            
            courts.append({
                'name': name,
                'province': province,
                'city': city,
                'district': district,
                'latitude': lat,
                'longitude': lon,
                'full_address': tags.get('addr:full') or tags.get('address') or '',
                'website': tags.get('website') or '',
                'phone': tags.get('phone') or tags.get('contact:phone') or '',
                'osm_id': element.get('id')
            })
                
        # 去重
        unique_courts = []
        seen = set()
        for c in courts:
            key = (c['name'], round(float(c['latitude']), 4), round(float(c['longitude']), 4))
            if key not in seen:
                unique_courts.append(c)
                seen.add(key)
        return unique_courts

    def save_to_csv(self, courts, filename=None):
        if filename is None:
            # 默认保存在 data 目录下
            # 当前脚本在 scripts/data_prep/，向上退两级到根目录
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            filename = os.path.join(base_dir, 'data', 'china_courts_osm.csv')
            
        if not courts:
            print("没有找到任何法院信息。")
            return
            
        df = pd.DataFrame(courts)
        cols = ['name', 'province', 'city', 'district', 'latitude', 'longitude', 'full_address', 'website', 'phone']
        df[cols].to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"成功抓取 {len(courts)} 条法院信息，已保存至: {filename}")

def main():
    fetcher = OSMCourtFetcher()
    data = fetcher.fetch_data()
    if data:
        courts = fetcher.parse_results(data)
        fetcher.save_to_csv(courts)

if __name__ == "__main__":
    main()
