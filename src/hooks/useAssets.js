import { useState, useEffect, useCallback } from 'react';
import { fetchFullLocation } from '../services/locationService';
import { loadManifest } from '../services/dataService';

/**
 * 资产与初始化加载 Hook
 */
export const useAssets = () => {
  const [isReady, setIsReady] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState('正在布置法庭...');
  const [location, setLocation] = useState(null);
  const [error, setError] = useState(null);

  const init = useCallback(async () => {
    try {
      setLoadingStatus('正在准备法庭资料...');
      
      // 1. 并行执行所有初始化任务
      const [locResult, manifestResult, textureResult] = await Promise.allSettled([
        // 任务 A: 地理位置定位
        fetchFullLocation((status) => setLoadingStatus(`正在定位: ${status}`)),
        
        // 任务 B: 数据清单加载
        loadManifest(),
        
        // 任务 C: 背景纹理预加载
        new Promise((resolve, reject) => {
          const img = new Image();
          img.src = '/assets/textures/wood-pattern.png';
          img.onload = resolve;
          img.onerror = reject;
        })
      ]);

      // 检查定位结果
      if (locResult.status === 'fulfilled') {
        setLocation(locResult.value);
      } else {
        console.warn('[初始化] 定位失败，将使用默认位置:', locResult.reason);
        setLocation({ adcode: '110101', province: '北京市', city: '北京市', district: '东城区' });
      }

      // 检查清单结果
      if (manifestResult.status === 'rejected') {
        console.error('[初始化] 清单加载失败:', manifestResult.reason);
      }

      // 检查纹理结果
      if (textureResult.status === 'rejected') {
        console.warn('[初始化] 背景纹理加载失败，将使用备用底色');
      }

      setLoadingStatus('法庭布置完毕');
      setIsReady(true);
    } catch (err) {
      console.error('[初始化] 严重错误:', err);
      setError('初始化失败，请刷新页面重试');
    }
  }, []);

  useEffect(() => {
    init();
  }, [init]);

  return { isReady, loadingStatus, location, error };
};
