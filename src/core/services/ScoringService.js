/**
 * 评分服务 - 比较玩家判决与实际判决
 */
export class ScoringService {
  /**
   * 计算得分
   * @param {Case} caseObj 案件对象
   * @param {Judgment} playerJudgment 玩家判决
   * @returns {Object} 评分结果
   */
  static score(caseObj, playerJudgment) {
    if (!caseObj || !playerJudgment) return { totalScore: 0, breakdown: {} };
    const actual = caseObj.actualJudgment;
    
    // 1. 罪名准确性 (50%)
    const isChargeCorrect = playerJudgment.charge === actual.charge;
    const chargeScore = isChargeCorrect ? 50 : 0;
    
    // 2. 刑期平衡度 (20% 类型 + 20% 长度 = 40%)
    let typeScore = 0;
    let durationScore = 0;
    
    if (playerJudgment.mainPenalty === actual.mainPenalty) {
      typeScore = 20;
      
      if (['无期徒刑', '死刑'].includes(actual.mainPenalty)) {
        durationScore = 20;
      } else {
        const playerTotalMonths = playerJudgment.years * 12 + playerJudgment.months;
        const actualTotalMonths = (actual.years || 0) * 12 + (actual.months || 0);
        
        if (playerTotalMonths === actualTotalMonths) {
          durationScore = 20;
        } else if (playerTotalMonths === 0 || actualTotalMonths === 0) {
          durationScore = 0;
        } else {
          // min(标准长度/玩家长度, 玩家长度/标准长度) * 20 取整
          const ratio = Math.min(actualTotalMonths / playerTotalMonths, playerTotalMonths / actualTotalMonths);
          durationScore = Math.round(ratio * 20);
        }
      }
    }
    
    // 3. 罚金/财产刑 (10%)
    let fineScore = 0;
    if (playerJudgment.hasFine === actual.hasFine) {
      if (!actual.hasFine) {
        fineScore = 10;
      } else {
        const playerFine = playerJudgment.fineAmount || 0;
        const actualFine = actual.fineAmount || 0;
        
        if (playerFine === actualFine) {
          fineScore = 10;
        } else if (playerFine === 0 || actualFine === 0) {
          fineScore = 0;
        } else {
          // min(标准金额/玩家金额, 玩家金额/标准金额) * 10 取整
          const ratio = Math.min(actualFine / playerFine, playerFine / actualFine);
          fineScore = Math.round(ratio * 10);
        }
      }
    }
    
    const totalScore = chargeScore + typeScore + durationScore + fineScore;
    
    return {
      totalScore,
      breakdown: {
        charge: { score: chargeScore, isCorrect: isChargeCorrect },
        penalty: { 
          score: typeScore + durationScore, 
          typeScore,
          durationScore,
          deviation: this._getPenaltyDeviation(playerJudgment, actual) 
        },
        fine: { score: fineScore, isCorrect: playerJudgment.hasFine === actual.hasFine }
      }
    };
  }

  static _getPenaltyDeviation(player, actual) {
    if (player.mainPenalty !== actual.mainPenalty) return '主刑类型错误';
    const playerTotal = (player.years || 0) * 12 + (player.months || 0);
    const actualTotal = (actual.years || 0) * 12 + (actual.months || 0);
    if (playerTotal === actualTotal) return '分毫不差';
    const diff = playerTotal - actualTotal;
    
    let timeStr = '';
    const absDiff = Math.abs(diff);
    const years = Math.floor(absDiff / 12);
    const months = absDiff % 12;
    
    if (years > 0) timeStr += `${years}年`;
    if (months > 0) timeStr += `${months}个月`;
    if (timeStr === '') timeStr = '0个月';

    return diff > 0 ? `偏重 ${timeStr}` : `偏轻 ${timeStr}`;
  }
}
