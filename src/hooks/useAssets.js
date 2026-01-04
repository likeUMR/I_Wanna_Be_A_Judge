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
      
      // 1. 定位与清单加载 (允许失败/超时)
      const [locResult, manifestResult] = await Promise.allSettled([
        fetchFullLocation((status) => setLoadingStatus(`正在定位: ${status}`)),
        loadManifest()
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

      // 2. 核心纹理加载 (必须成功)
      setLoadingStatus('正在布置法庭背景...');
      await new Promise((resolve, reject) => {
        const remoteUrl = 'https://www.transparenttextures.com/patterns/wood-pattern.png';
        const localUrl = 'assets/textures/wood-pattern.png';
        const img = new Image();
        img.crossOrigin = "anonymous"; // 增加跨域支持
        
        let isTryingLocal = false;
        let resolved = false;

        // 设置 1s 超时
        const timer = setTimeout(() => {
          if (!resolved && !isTryingLocal) {
            console.warn('[初始化] 外部纹理下载超时，尝试加载本地资源');
            isTryingLocal = true;
            img.src = localUrl;
          }
        }, 1000);

          img.onload = async () => {
            if (!resolved) {
              // 确保图片确实有宽高（已完全解码）
              if (img.complete && img.naturalWidth > 0) {
                try {
                  // 强制解码，确保图片已准备好渲染
                  if (img.decode) {
                    await img.decode();
                  }
                  
                  // 将加载成功的纹理应用到全局 CSS 变量
                  document.documentElement.style.setProperty('--bg-texture', `url("${img.src}")`);
                  
                  resolved = true;
                  clearTimeout(timer);
                  resolve(img);
                } catch (e) {
                  console.warn('[初始化] 解码失败，直接返回:', e);
                  resolved = true;
                  clearTimeout(timer);
                  resolve(img);
                }
              }
            }
          };

        img.onerror = () => {
          if (!resolved) {
            if (!isTryingLocal) {
              console.warn('[初始化] 外部纹理加载失败，尝试加载本地资源');
              isTryingLocal = true;
              img.src = localUrl;
            } else {
              console.error('[初始化] 纹理加载完全失败');
              resolved = true;
              clearTimeout(timer);
              reject(new Error('背景纹理加载失败，无法进入法庭'));
            }
          }
        };

        img.src = remoteUrl; // 移除时间戳，确保与 CSS 中的 URL 一致以利用缓存
      });

      setLoadingStatus('法庭布置完毕');
      setIsReady(true);
    } catch (err) {
      console.error('[初始化] 严重错误:', err);
      setError(err.message || '初始化失败，请刷新页面重试');
      setLoadingStatus('初始化失败');
    }
  }, []);

  useEffect(() => {
    init();
  }, [init]);

  return { isReady, loadingStatus, location, error };
};
