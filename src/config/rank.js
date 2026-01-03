/**
 * 法官等级体系配置
 * id: 等级ID
 * name: 等级名称
 * minScore: 晋升该等级所需的最低总积分
 * benchmark: 该等级对应的判决基准分（判决得分高于此分则增加总分）
 */
export const JUDGE_RANKS = [
  { id: 0, name: '见习法官', minScore: 0, benchmark: 60 },
  { id: 1, name: '五级法官', minScore: 100, benchmark: 65 },
  { id: 2, name: '四级法官', minScore: 800, benchmark: 70 },
  { id: 3, name: '三级法官', minScore: 1400, benchmark: 75 },
  { id: 4, name: '二级法官', minScore: 1900, benchmark: 80 },
  { id: 5, name: '一级法官', minScore: 2300, benchmark: 82 },
  { id: 6, name: '四级高级法官', minScore: 2660, benchmark: 85 },
  { id: 7, name: '三级高级法官', minScore: 2960, benchmark: 88 },
  { id: 8, name: '二级高级法官', minScore: 3200, benchmark: 90 },
  { id: 9, name: '一级高级法官', minScore: 3400, benchmark: 92 },
  { id: 10, name: '二级大法官', minScore: 3560, benchmark: 94 },
  { id: 11, name: '一级大法官', minScore: 3680, benchmark: 96 },
  { id: 12, name: '首席大法官', minScore: 3760, benchmark: 98 }
];

export const RANK_CONFIG = {
  MULTIPLIER: 2.0, // 分数变动系数
};
