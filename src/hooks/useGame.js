import { useState, useCallback, useEffect } from 'react';
import { CaseLoader } from '../core/services/CaseLoader';
import { ScoringService } from '../core/services/ScoringService';
import { RankService } from '../core/services/RankService';
import { HistoryService } from '../core/services/HistoryService';
import { LegalService } from '../core/services/LegalService';
import { Judgment } from '../core/models/Judgment';
import { storageService } from '../services/storageService';
import { fetchCrimes } from '../services/dataService';

export const useGame = (initialAdcode) => {
  const [currentCase, setCurrentCase] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [playerJudgment, setPlayerJudgment] = useState(new Judgment());
  const [showFeedback, setShowFeedback] = useState(false);
  const [scoring, setScoring] = useState(null);
  
  // 段位分数持久化
  const [totalScore, setTotalScore] = useState(() => {
    return HistoryService.getTotalScore(storageService);
  });

  const [scoreChange, setScoreChange] = useState(0);
  const [nextCase, setNextCase] = useState(null);
  const [preloading, setPreloading] = useState(false);
  
  const [statistics, setStatistics] = useState(() => {
    return HistoryService.getStatistics(storageService);
  });

  const [allCrimes, setAllCrimes] = useState([]);
  
  // 初始化加载罪名库
  useEffect(() => {
    fetchCrimes().then(setAllCrimes);
  }, []);

  useEffect(() => {
    HistoryService.saveTotalScore(storageService, totalScore);
  }, [totalScore]);

  const loadCase = useCallback(async (adcode) => {
    // 如果已经有预加载好的案例，直接使用
    if (nextCase) {
      // 如果预加载时还没生成选项，这里生成
      if (!nextCase.crimeOptions && allCrimes.length > 0) {
        nextCase.crimeOptions = LegalService.getCrimeOptions(nextCase.actualJudgment.charge, allCrimes);
      }
      setCurrentCase(nextCase);
      setNextCase(null);
      setShowFeedback(false);
      setPlayerJudgment(new Judgment());
      setScoreChange(0);
      return;
    }

    setLoading(true);
    setError(null);
    setShowFeedback(false);
    setPlayerJudgment(new Judgment());
    setScoreChange(0);
    try {
      const caseObj = await CaseLoader.loadRandomCase(adcode);
      // 生成罪名选项
      if (allCrimes.length > 0) {
        caseObj.crimeOptions = LegalService.getCrimeOptions(caseObj.actualJudgment.charge, allCrimes);
      }
      setCurrentCase(caseObj);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [nextCase, allCrimes]);

  // 预加载逻辑
  const preloadNextCase = useCallback(async (adcode) => {
    if (preloading || nextCase) return;
    setPreloading(true);
    try {
      const caseObj = await CaseLoader.loadRandomCase(adcode);
      // 预加载时也尝试生成选项
      if (allCrimes.length > 0) {
        caseObj.crimeOptions = LegalService.getCrimeOptions(caseObj.actualJudgment.charge, allCrimes);
      }
      setNextCase(caseObj);
    } catch (err) {
      console.warn('Preload failed:', err);
    } finally {
      setPreloading(false);
    }
  }, [preloading, nextCase, allCrimes]);

  // 当 currentCase 变化且没有 nextCase 时，立即开始预加载下一个案例
  useEffect(() => {
    if (currentCase && !nextCase && !preloading) {
      // 这里的 adcode 优先使用当前案例的，作为兜底使用初始值或默认值
      const targetAdcode = currentCase.adCode || initialAdcode || '110101';
      preloadNextCase(targetAdcode);
    }
  }, [currentCase, nextCase, preloading, preloadNextCase, initialAdcode]);

  const submitJudgment = useCallback(() => {
    if (!currentCase) return;
    const result = ScoringService.score(currentCase, playerJudgment);
    
    // 计算段位分变动
    const change = RankService.calculateScoreChange(result.totalScore, totalScore);
    setScoreChange(change);
    const newTotalScore = Math.max(0, totalScore + change);
    setTotalScore(newTotalScore);
    
    // 记录到历史
    HistoryService.recordJudgment(storageService, {
      caseId: currentCase.id,
      score: result.totalScore,
      change: change,
      adcode: currentCase.adCode,
      cause: currentCase.cause
    });
    
    // 更新统计数据
    setStatistics(HistoryService.getStatistics(storageService));
    
    setScoring(result);
    setShowFeedback(true);
  }, [currentCase, playerJudgment, totalScore]);

  const updateJudgment = useCallback((updates) => {
    setPlayerJudgment(prev => {
      const newData = { ...prev, ...updates };
      return new Judgment(newData);
    });
  }, []);

  const toggleFactor = useCallback((type, factorId) => {
    setPlayerJudgment(prev => {
      const factors = { ...prev.selectedFactors };
      const list = [...factors[type]];
      const index = list.indexOf(factorId);
      if (index > -1) {
        list.splice(index, 1);
      } else {
        list.push(factorId);
      }
      factors[type] = list;
      return new Judgment({ ...prev, selectedFactors: factors });
    });
  }, []);

  const rankInfo = RankService.getRankByTotalScore(totalScore);

  return {
    currentCase,
    loading,
    error,
    playerJudgment,
    showFeedback,
    scoring,
    totalScore,
    scoreChange,
    rankInfo,
    statistics,
    loadCase,
    submitJudgment,
    updateJudgment,
    toggleFactor
  };
};
