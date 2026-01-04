import axios from 'axios';
import Papa from 'papaparse';
import config from '../config';

/**
 * 加载行政区划数据
 */
export const fetchAdminDivisions = async () => {
  try {
    const response = await axios.get('/processed_admin_divisions.csv', { responseType: 'text' });
    let csvData = response.data;
    if (csvData.startsWith('\ufeff')) {
      csvData = csvData.slice(1);
    }
    
    return new Promise((resolve) => {
      Papa.parse(csvData, {
        header: false,
        skipEmptyLines: true,
        complete: (results) => {
          // 格式化为: { name, adcode, parent, grandparent }
          const formatted = results.data.map(row => ({
            name: row[0],
            adcode: row[1],
            parent: row[2] || '',
            grandparent: row[3] || ''
          }));
          resolve(formatted);
        }
      });
    });
  } catch (error) {
    console.error('加载行政区划数据失败:', error);
    return [];
  }
};

/**
 * 尝试从多个源获取经纬度或位置信息
 */
const getCoordsByIP = async () => {
  // 方案 1: www.mapchaxun.cn (第一优先级)
  try {
    console.log('[定位] 尝试方案 1: www.mapchaxun.cn');
    const res = await axios.post(
      '/api-mapchaxun/api/mapApi/getIpMes',
      { ip: null },
      {
        headers: {
          'accept': 'application/json',
          'content-type': 'application/json'
        },
        timeout: 8000
      }
    );
    
    console.log('[定位] 方案 1 返回:', res.data);
    
    if (res.data.status === 0 && res.data.result) {
      const { location: loc, ad_info } = res.data.result;
      return {
        lat: loc.lat,
        lon: loc.lng, // 注意该接口返回的是 lng
        province: ad_info.province,
        city: ad_info.city,
        district: ad_info.district,
        adcode: ad_info.adcode,
        source: 'mapchaxun.cn'
      };
    }
  } catch (e) {
    console.warn('[定位] 方案 1 失败:', e.message);
  }

  // 方案 2: AMap IP 定位 (第二优先级)
  try {
    console.log('[定位] 尝试方案 2: AMap IP');
    const res = await axios.get(`https://restapi.amap.com/v3/ip?key=${config.AMAP_KEY}`, { timeout: 5000 });
    if (res.data.status === '1') {
      return {
        province: res.data.province,
        city: res.data.city,
        adcode: res.data.adcode,
        district: res.data.district, // 通常为空
        source: 'AMap IP'
      };
    }
  } catch (e) {
    console.warn('[定位] 方案 2 失败:', e.message);
  }

  // 方案 3: ipapi.co (第三优先级)
  try {
    console.log('[定位] 尝试方案 3: ipapi.co');
    const res = await axios.get('https://ipapi.co/json/', { timeout: 5000 });
    if (res.data?.latitude) {
      return {
        lat: res.data.latitude,
        lon: res.data.longitude,
        source: 'ipapi.co'
      };
    }
  } catch (e) {
    console.warn('[定位] 方案 3 失败:', e.message);
  }

  throw new Error('所有定位接口均不可达');
};

/**
 * 获取完整的地理位置信息，包括精度补强
 */
export const fetchFullLocation = async (onStatusUpdate) => {
  const currentKey = config.AMAP_KEY;

  try {
    console.log('[流程] 开始获取地理位置...');
    
    // 执行优先级策略
    const rawData = await getCoordsByIP();
    console.log('[流程] 原始定位结果:', rawData);

    // 构造初步结果
    let location = {
      province: rawData.province || '',
      city: rawData.city || '',
      district: (typeof rawData.district === 'string') ? rawData.district : '',
      adcode: rawData.adcode || '',
      method: `静默定位 (${rawData.source})`,
      status: ''
    };

    // 判断是否需要通过高德逆地理编码补精（如果没有区县信息，或者 adcode 是市级的）
    const adcodeStr = String(location.adcode);
    const isNotPrecise = !location.district || adcodeStr.endsWith('00');

    if (isNotPrecise && rawData.lat && rawData.lon) {
      console.log('[流程] 精度不足，启动高德逆地理编码补精...');
      if (onStatusUpdate) onStatusUpdate('正在深度解析区县...');
      
      const regeoRes = await axios.get(
        `https://restapi.amap.com/v3/geocode/regeo?key=${currentKey}&location=${rawData.lon},${rawData.lat}`
      );

      if (regeoRes.data.status === '1') {
        const component = regeoRes.data.regeocode.addressComponent;
        let newCity = component.city;
        if (Array.isArray(newCity) && newCity.length === 0) {
          newCity = component.province;
        }

        location = {
          province: component.province,
          city: newCity,
          district: component.district,
          adcode: component.adcode,
          method: `深度解析 (${rawData.source} + AMap)`,
          status: ''
        };
      }
    } else {
      console.log('[流程] 定位精度已达标。');
    }

    return location;
  } catch (err) {
    console.error('[流程] 严重错误:', err);
    throw new Error(err.message || '定位解析失败');
  }
};
