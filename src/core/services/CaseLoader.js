import { getRandomCaseByAdcode } from '../../services/dataService';
import { Case } from '../models/Case';

/**
 * 案件加载服务
 */
export class CaseLoader {
  /**
   * 加载随机案件
   * @param {string} adcode 行政区划代码
   * @returns {Promise<Case>}
   */
  static async loadRandomCase(adcode) {
    const rawData = await getRandomCaseByAdcode(adcode);
    return new Case(rawData);
  }
}
