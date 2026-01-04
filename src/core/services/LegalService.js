/**
 * 法律手册服务 - 逻辑层
 */
export class LegalService {
  /**
   * 加载法律手册数据
   * @returns {Promise<Array>} 返回 top 20 法条列表
   */
  static async loadLegalManual() {
    try {
      const response = await fetch('legal_manual.json');
      if (!response.ok) {
        throw new Error('Failed to load legal manual');
      }
      return await response.json();
    } catch (error) {
      console.error('Error loading legal manual:', error);
      return [];
    }
  }
}
