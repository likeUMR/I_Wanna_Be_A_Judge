import Papa from 'papaparse';
import axios from 'axios';
import { storageService } from './storageService';
import { HistoryService } from '../core/services/HistoryService';

let blocksManifest = null;
const csvCache = new Map(); // 缓存已加载并解析的 CSV 数据: url -> Array of objects

/**
 * 加载分片清单
 */
export const loadManifest = async () => {
  if (blocksManifest) return blocksManifest;
  try {
    const res = await axios.get('data/blocks_manifest.json');
    blocksManifest = res.data;
    return blocksManifest;
  } catch (e) {
    console.warn('[数据] 加载分片清单失败:', e.message);
    return {};
  }
};

/**
 * 加载罪名统计数据
 */
export const fetchCrimes = async () => {
  try {
    const res = await axios.get('crimes.json');
    return res.data;
  } catch (e) {
    console.warn('[数据] 加载罪名数据失败:', e.message);
    return [];
  }
};

/**
 * 辅助函数：获取已玩过的案例ID列表
 */
const getPlayedCases = () => {
  return HistoryService.getPlayedCaseIds(storageService);
};

/**
 * 辅助函数：保存已玩过的案例ID
 */
const savePlayedCase = (caseId) => {
  HistoryService.recordPlayedCase(storageService, caseId);
};

/**
 * 辅助函数：从 CSV 数据中选择一个案例
 */
const pickNewCase = (cases, playedIds, ignorePlayed = false) => {
  // 过滤掉完全空的行
  const validCases = cases.filter(c => c && (c['案号'] || c['姓名'] || c['SECTION_5_经审理查明的犯罪事实']));
  
  const unplayed = ignorePlayed 
    ? validCases 
    : validCases.filter(c => !playedIds.includes(c['案号']));
  
  if (unplayed.length === 0) return null;

  // 随机选择
  const randomIndex = Math.floor(Math.random() * unplayed.length);
  const selected = unplayed[randomIndex];
  
  if (!ignorePlayed && selected['案号']) {
    savePlayedCase(selected['案号']);
  }
  return selected;
};

/**
 * 辅助函数：尝试加载一个特定的 block 并从中选一个案例
 */
const tryBlockAndPick = async (adcode, type, blockNum, playedIds, ignorePlayed = false) => {
  const blockNumStr = String(blockNum).padStart(2, '0');
  const url = type === 'perfect' 
    ? `data/perfect/${adcode}_perfect_${blockNumStr}.csv`
    : `data/${adcode}_filtered_${blockNumStr}.csv`;

  // 优先从缓存获取
  if (csvCache.has(url)) {
    const cachedData = csvCache.get(url);
    const selected = pickNewCase(cachedData, playedIds, ignorePlayed);
    return selected;
  }

  try {
    const response = await axios.get(url, { responseType: 'text' });
    let csvData = response.data;
    
    if (csvData.startsWith('\ufeff')) {
      csvData = csvData.slice(1);
    }
    
    const results = await new Promise((resolve, reject) => {
      Papa.parse(csvData, {
        header: true,
        skipEmptyLines: 'greedy',
        trimHeaders: true,
        complete: (results) => {
          resolve(results.data);
        },
        error: (error) => {
          console.error(`CSV 解析出错 (${url}):`, error);
          reject(new Error(`CSV 解析失败: ${error.message}`));
        }
      });
    });

    if (results && results.length > 0) {
      // 存入缓存
      csvCache.set(url, results);
      return pickNewCase(results, playedIds, ignorePlayed);
    }
    return null;

  } catch (error) {
    if (error.response && error.response.status === 404) {
      return null;
    }
    console.warn(`请求 CSV 失败 (${url}):`, error.message);
    return null;
  }
};

/**
 * 根据 adcode 加载对应的 CSV 数据并随机选择一行
 * 优先在完美的里面随机，都随机过一遍或者没有完美的，再在接近完美的里面随机
 */
export const getRandomCaseByAdcode = async (adcode) => {
  const playedIds = getPlayedCases();
  const adcodeStr = String(adcode);
  const manifest = await loadManifest();
  
  if (!manifest) {
    throw new Error('无法加载分片清单，请检查数据完整性');
  }

  const info = manifest[adcodeStr] || { p: 0, f: 0 };

  // 辅助函数：随机尝试所有 block
  const tryAllBlocks = async (type, totalBlocks, ignorePlayed) => {
    if (totalBlocks <= 0) return null;
    
    // 生成随机顺序的 block 索引
    const indices = Array.from({ length: totalBlocks }, (_, i) => i + 1);
    for (let i = indices.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [indices[i], indices[j]] = [indices[j], indices[i]];
    }

    for (const blockNum of indices) {
      const result = await tryBlockAndPick(adcodeStr, type, blockNum, playedIds, ignorePlayed);
      if (result) return result;
    }
    return null;
  };

  try {
    // 1. 尝试从完美池加载
    console.log(`[数据] 尝试完美池 (${info.p} 个分片)`);
    const perfectCase = await tryAllBlocks('perfect', info.p, false);
    if (perfectCase) return perfectCase;

    // 2. 尝试标准池
    console.log(`[数据] 尝试标准池 (${info.f} 个分片)`);
    const standardCase = await tryAllBlocks('filtered', info.f, false);
    if (standardCase) return standardCase;

    // 3. 重置逻辑
    console.log(`[数据] 所有分片案例已读完，重置随机选择流程`);
    const resetPerfect = await tryAllBlocks('perfect', info.p, true);
    if (resetPerfect) return resetPerfect;

    const resetStandard = await tryAllBlocks('filtered', info.f, true);
    if (resetStandard) return resetStandard;

    throw new Error(`找不到地区代码为 ${adcodeStr} 的任何有效案件数据 (分片模式)`);

  } catch (error) {
    console.error(`[数据] 加载数据最终失败:`, error);
    throw error;
  }
};
