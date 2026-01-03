/**
 * 游戏历史与进度管理服务 (逻辑层)
 * 负责管理得分、已玩案例等业务逻辑
 */
export class HistoryService {
  static KEYS = {
    TOTAL_SCORE: 'judge_total_score',
    PLAYED_CASE_IDS: 'played_case_ids',
    GAME_HISTORY: 'judge_game_history'
  };

  /**
   * 获取当前总分
   * @param {Object} storage 存储引擎接口
   */
  static getTotalScore(storage) {
    return storage.getItem(this.KEYS.TOTAL_SCORE, 0);
  }

  /**
   * 保存总分
   * @param {Object} storage 存储引擎接口
   * @param {number} score 分数
   */
  static saveTotalScore(storage, score) {
    storage.setItem(this.KEYS.TOTAL_SCORE, score);
  }

  /**
   * 获取已玩过的案例ID列表
   * @param {Object} storage 存储引擎接口
   */
  static getPlayedCaseIds(storage) {
    return storage.getItem(this.KEYS.PLAYED_CASE_IDS, []);
  }

  /**
   * 记录已玩过的案例
   * @param {Object} storage 存储引擎接口
   * @param {string} caseId 案例ID
   */
  static recordPlayedCase(storage, caseId) {
    if (!caseId) return;
    const played = this.getPlayedCaseIds(storage);
    if (!played.includes(caseId)) {
      played.push(caseId);
      // 限制记录数量，防止溢出
      if (played.length > 1000) played.shift();
      storage.setItem(this.KEYS.PLAYED_CASE_IDS, played);
    }
  }

  /**
   * 记录判决历史
   * @param {Object} storage 存储引擎接口
   * @param {Object} record 判决记录
   */
  static recordJudgment(storage, record) {
    const history = storage.getItem(this.KEYS.GAME_HISTORY, []);
    history.push({
      ...record,
      timestamp: Date.now()
    });
    // 只保留最近 100 条详细记录
    if (history.length > 100) history.shift();
    storage.setItem(this.KEYS.GAME_HISTORY, history);
  }

  /**
   * 获取判决历史
   * @param {Object} storage 存储引擎接口
   */
  static getHistory(storage) {
    return storage.getItem(this.KEYS.GAME_HISTORY, []);
  }
}
