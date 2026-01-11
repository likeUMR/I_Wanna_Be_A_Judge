/**
 * 案件模型 - 纯逻辑层，不依赖任何平台特定方法
 */
export class Case {
  constructor(data) {
    this.id = data['案号'] || '';
    this.adCode = data['AdCode'] || '';
    this.court = data['法院'] || '';
    this.cause = data['案由'] || '';
    this.procedure = data['审理程序'] || '';
    this.organization = data['审判组织形式'] || '';
    this.isOpen = data['是否公开审理'] === '是';
    
    // 被告人信息
    const mental = data['精神状态'] || '正常';
    const physical = data['特殊身体状况'] || '正常';
    
    let physioStatus = '正常';
    if (mental.includes('精神') || mental.includes('限制刑事责任能力')) {
      physioStatus = '精神病';
    } else if (physical.includes('盲')) {
      physioStatus = '盲人';
    } else if (physical.includes('聋哑')) {
      physioStatus = '聋哑';
    } else if (physical.includes('残疾')) {
      physioStatus = '残疾';
    }

    this.defendant = {
      name: data['姓名'] || '不详',
      gender: data['性别'] || '不详',
      birthDate: data['出生日期'] || '',
      education: data['文化程度'] || '不详',
      occupation: data['职业'] || '不详',
      criminalRecord: data['刑事前科'] || '无',
      age: parseInt(data['年龄']) || 0,
      isMinor: data['是否未成年'] === '1',
      physiologicalStatus: physioStatus
    };

    // 案情核心
    this.facts = data['SECTION_5_经审理查明的犯罪事实'] || '';
    this.evidences = data['SECTION_6_证据列举'] || '';
    this.legalReasoning = data['SECTION_7_罪名认定理由'] || '';
    this.verdictText = data['SECTION_10_判决主文'] || '';
    
    // 量刑因子
    this.factors = {
      isRecidivist: data['是否累犯'] === '1',
      isAttempt: data['是否未遂'] === '1',
      isSurrender: data['是否自首'] === '1',
      isCommendable: data['是否立功'] === '1',
      isConfessed: data['是否如实供述'] === '1',
      isPlea: data['是否认罪认罚'] === '1',
      isRepented: data['是否退赃'] === '1' || data['是否取得谅解'] === '1',
      surrenderType: data['surrender_type'] || '0',
      role: data['主从犯身份'] || '主犯'
    };

    // 真实判决结果 (标答)
    this.actualJudgment = {
      charge: data['罪名'] || '',
      mainPenalty: data['主刑'] || '',
      years: parseInt(data['刑期_年']) || 0,
      months: parseInt(data['刑期_月']) || 0,
      days: parseInt(data['刑期_日']) || 0,
      hasFine: !!data['罚金'] && parseInt(data['罚金']) > 0,
      fineAmount: parseInt(data['罚金']) || 0,
      date: data['判决日期'] || ''
    };
  }

  /**
   * 获取格式化的刑期
   */
  getFormattedActualPenalty() {
    const { mainPenalty, years, months, days } = this.actualJudgment;
    if (['无期徒刑', '死刑'].includes(mainPenalty)) return mainPenalty;
    let result = mainPenalty;
    if (years > 0) result += ` ${years}年`;
    if (months > 0) result += ` ${months}个月`;
    if (days > 0) result += ` ${days}日`;
    return result;
  }
}
