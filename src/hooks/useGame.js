import { useState, useCallback, useEffect } from 'react';
import { CaseLoader } from '../core/services/CaseLoader';
import { ScoringService } from '../core/services/ScoringService';
import { RankService } from '../core/services/RankService';
import { HistoryService } from '../core/services/HistoryService';
import { Judgment } from '../core/models/Judgment';
import { storageService } from '../services/storageService';

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

  useEffect(() => {
    HistoryService.saveTotalScore(storageService, totalScore);
  }, [totalScore]);

  const loadCase = useCallback(async (adcode) => {
    // 如果已经有预加载好的案例，直接使用
    if (nextCase) {
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
      setCurrentCase(caseObj);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [nextCase]);

  // 预加载逻辑
  const preloadNextCase = useCallback(async (adcode) => {
    if (preloading || nextCase) return;
    setPreloading(true);
    try {
      const caseObj = await CaseLoader.loadRandomCase(adcode);
      setNextCase(caseObj);
    } catch (err) {
      console.warn('Preload failed:', err);
    } finally {
      setPreloading(false);
    }
  }, [preloading, nextCase]);

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

    // 提交后立即开始预加载下一个案例
    preloadNextCase(currentCase.adCode || '110101');
  }, [currentCase, playerJudgment, totalScore, preloadNextCase]);

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
