import React, { useState, useEffect, useMemo } from 'react';
import { fetchAdminDivisions } from '../../services/locationService';
import './LocationSelector.css';

const LocationSelector = ({ onLocationChange }) => {
  const [allDivisions, setAllDivisions] = useState([]);
  const [isManual, setIsManual] = useState(false);
  const [loading, setLoading] = useState(false);

  const [selectedProvince, setSelectedProvince] = useState('');
  const [selectedCity, setSelectedCity] = useState('');
  const [selectedDistrict, setSelectedDistrict] = useState('');

  // 1. 加载所有行政区划数据 (仅在切换到手动模式时加载)
  useEffect(() => {
    if (isManual && allDivisions.length === 0) {
      setLoading(true);
      fetchAdminDivisions().then(data => {
        setAllDivisions(data);
        setLoading(false);
        
        // 初始设置第一个省份 (北京)
        if (data.length > 0) {
          const firstProv = data.find(d => d.parent === '' && d.grandparent === '');
          if (firstProv) {
            handleProvinceChange(firstProv.name, data);
          }
        }
      });
    }
  }, [isManual, allDivisions.length]);

  // 2. 过滤各级菜单
  const provinces = useMemo(() => 
    allDivisions.filter(d => d.parent === '' && d.grandparent === ''), 
    [allDivisions]
  );

  const cities = useMemo(() => 
    allDivisions.filter(d => d.parent === selectedProvince && d.grandparent === ''),
    [allDivisions, selectedProvince]
  );

  const districts = useMemo(() => 
    allDivisions.filter(d => d.parent === selectedCity && d.grandparent === selectedProvince),
    [allDivisions, selectedCity, selectedProvince]
  );

  // 3. 处理变更逻辑
  const handleProvinceChange = (provinceName, data = allDivisions) => {
    setSelectedProvince(provinceName);
    
    // 自动选择第一个城市
    const cityList = data.filter(d => d.parent === provinceName && d.grandparent === '');
    if (cityList.length > 0) {
      handleCityChange(cityList[0].name, provinceName, data);
    } else {
      setSelectedCity('');
      setSelectedDistrict('');
    }
  };

  const handleCityChange = (cityName, provinceName, data = allDivisions) => {
    setSelectedCity(cityName);
    
    // 自动选择第一个区县
    const distList = data.filter(d => d.parent === cityName && d.grandparent === provinceName);
    if (distList.length > 0) {
      const firstDist = distList[0];
      setSelectedDistrict(firstDist.name);
      onLocationChange({
        province: provinceName,
        city: cityName,
        district: firstDist.name,
        adcode: firstDist.adcode,
        method: '手动选择'
      });
    } else {
      setSelectedDistrict('');
      // 如果没有区县，就用城市的 adcode
      const cityInfo = data.find(d => d.name === cityName && d.parent === provinceName);
      onLocationChange({
        province: provinceName,
        city: cityName,
        district: '',
        adcode: cityInfo?.adcode || '',
        method: '手动选择'
      });
    }
  };

  const handleDistrictChange = (districtName) => {
    setSelectedDistrict(districtName);
    const districtInfo = allDivisions.find(d => d.name === districtName && d.parent === selectedCity && d.grandparent === selectedProvince);
    if (districtInfo) {
      onLocationChange({
        province: selectedProvince,
        city: selectedCity,
        district: districtName,
        adcode: districtInfo.adcode,
        method: '手动选择'
      });
    }
  };

  const toggleManual = () => {
    const nextManual = !isManual;
    setIsManual(nextManual);
    if (!nextManual) {
      // 切换回自动定位
      onLocationChange(null);
    } else if (allDivisions.length > 0) {
      // 切换到手动时，恢复上次或默认选择
      const firstProv = allDivisions.find(d => d.parent === '' && d.grandparent === '');
      if (firstProv) handleProvinceChange(firstProv.name);
    }
  };

  return (
    <div className="location-selector-container">
      <div className="manual-toggle">
        <label className="switch-label">
          <input type="checkbox" checked={isManual} onChange={toggleManual} />
          <span className="slider"></span>
          <span className="text">{isManual ? '手动定位' : '自动定位'}</span>
        </label>
      </div>

      {isManual && (
        <div className="selectors">
          {loading ? (
            <span className="loading-text">行政数据读取中...</span>
          ) : (
            <>
              <select value={selectedProvince} onChange={(e) => handleProvinceChange(e.target.value)}>
                {provinces.map(p => <option key={p.adcode} value={p.name}>{p.name}</option>)}
              </select>
              <select value={selectedCity} onChange={(e) => handleCityChange(e.target.value, selectedProvince)}>
                {cities.map(c => <option key={c.adcode} value={c.name}>{c.name}</option>)}
              </select>
              <select value={selectedDistrict} onChange={(e) => handleDistrictChange(e.target.value)}>
                {districts.map(d => <option key={d.adcode} value={d.name}>{d.name}</option>)}
              </select>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default LocationSelector;
