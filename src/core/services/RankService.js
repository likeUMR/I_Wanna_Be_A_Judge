/**
 * 法官等级体系与段位计算服务
 */
import { JUDGE_RANKS, RANK_CONFIG } from '../../config/rank';

export { JUDGE_RANKS };

export class RankService {
  /**
   * 根据当前总分获取等级信息
   */
  static getRankByTotalScore(totalScore) {
    for (let i = JUDGE_RANKS.length - 1; i >= 0; i--) {
      if (totalScore >= JUDGE_RANKS[i].minScore) {
        const currentRank = JUDGE_RANKS[i];
        const nextRank = JUDGE_RANKS[i + 1] || null;
        return {
          current: currentRank,
          next: nextRank,
          progress: nextRank 
            ? ((totalScore - currentRank.minScore) / (nextRank.minScore - currentRank.minScore)) * 100 
            : 100
        };
      }
    }
    return { current: JUDGE_RANKS[0], next: JUDGE_RANKS[1], progress: 0 };
  }

  /**
   * 计算单次判决后的分数变动
   * @param {number} judgmentScore 判决得分 (0-100)
   * @param {number} currentTotalScore 当前段位总分
   */
  static calculateScoreChange(judgmentScore, currentTotalScore) {
    const rankInfo = this.getRankByTotalScore(currentTotalScore);
    const benchmark = rankInfo.current.benchmark;
    
    // 分数差值
    const diff = judgmentScore - benchmark;
    
    // 基础变动系数
    const multiplier = RANK_CONFIG.MULTIPLIER; 
    
    let change = Math.round(diff * multiplier);
    
    return change;
  }
}
