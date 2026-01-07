/**
 * 法律手册服务 - 逻辑层
 */
export class LegalService {
  /**
   * 加载法律手册数据
   * @returns {Promise<Array>} 返回 top 20 法条列表
   */
  static async loadLegalManual() {
    // ...
  }

  /**
   * 生成罪名选项 (1个正确答案 + 7个基于概率采样的干扰项)
   * @param {string} correctCrime 正确罪名
   * @param {Array} allCrimes 所有罪名及其频率列表
   * @returns {Array<string>} 8个不重复的罪名选项
   */
  static getCrimeOptions(correctCrime, allCrimes) {
    if (!allCrimes || allCrimes.length === 0) return [correctCrime];

    const options = new Set();
    options.add(correctCrime);

    // 过滤掉正确答案后的池子
    const pool = allCrimes.filter(c => c.name !== correctCrime);
    
    // 如果池子太小，直接取所有
    if (pool.length <= 7) {
      pool.forEach(c => options.add(c.name));
    } else {
      // 简单权重采样逻辑：我们直接利用已排序的特性，或者使用加权随机
      // 为了性能和多样性，我们可以在 top 50 中选 4 个，在 top 51-300 中选 3 个
      // 或者直接进行加权随机采样
      const totalWeight = pool.reduce((sum, c) => sum + c.count, 0);
      
      while (options.size < 8) {
        let random = Math.random() * totalWeight;
        for (const crime of pool) {
          random -= crime.count;
          if (random <= 0) {
            options.add(crime.name);
            break;
          }
        }
      }
    }

    // 将 Set 转换为数组并随机洗牌
    const result = Array.from(options);
    for (let i = result.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [result[i], result[j]] = [result[j], result[i]];
    }

    return result;
  }
}
