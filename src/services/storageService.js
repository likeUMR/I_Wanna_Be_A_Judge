/**
 * 平台特定的存储服务实现 (Web localStorage)
 * 遵循显示层/平台层逻辑，调用平台特定接口
 */
export const storageService = {
  /**
   * 保存数据
   * @param {string} key 键
   * @param {any} value 值
   */
  setItem(key, value) {
    try {
      const serializedValue = JSON.stringify(value);
      localStorage.setItem(key, serializedValue);
    } catch (error) {
      console.error('Storage setItem error:', error);
    }
  },

  /**
   * 读取数据
   * @param {string} key 键
   * @param {any} defaultValue 默认值
   * @returns {any}
   */
  getItem(key, defaultValue = null) {
    try {
      const item = localStorage.getItem(key);
      if (item === null) return defaultValue;
      return JSON.parse(item);
    } catch (error) {
      console.error('Storage getItem error:', error);
      return defaultValue;
    }
  },

  /**
   * 移除数据
   * @param {string} key 键
   */
  removeItem(key) {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error('Storage removeItem error:', error);
    }
  },

  /**
   * 清空所有数据
   */
  clear() {
    try {
      localStorage.clear();
    } catch (error) {
      console.error('Storage clear error:', error);
    }
  }
};
