/**
 * 玩家判决模型
 */
export class Judgment {
  constructor(data = {}) {
    this.charge = data.charge || '';
    this.mainPenalty = data.mainPenalty || '有期徒刑';
    this.years = parseInt(data.years) || 0;
    this.months = parseInt(data.months) || 0;
    this.days = parseInt(data.days) || 0;
    this.hasFine = data.hasFine || false;
    this.fineAmount = parseInt(data.fineAmount) || 0;
    
    // 玩家勾选的量刑因子 (用于逻辑计算/评分)
    this.selectedFactors = data.selectedFactors || {
      aggravating: [], // 加重因子
      mitigating: []   // 减轻因子
    };
  }

  /**
   * 获取总刑期（月）
   */
  getTotalMonths() {
    return this.years * 12 + this.months + (this.days / 30);
  }
}
