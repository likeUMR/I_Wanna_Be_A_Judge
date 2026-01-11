import React from 'react';
import './VerdictFeedback.css';

const VerdictFeedback = ({ caseObj, playerJudgment, scoring, scoreChange, rankInfo, isSealed }) => {
  const { breakdown, totalScore } = scoring;
  const currentRankName = rankInfo?.current?.name || '见习法官';
  
  const getScoreClass = (score, max) => {
    if (score === max) return 'score-high';
    if (score >= max / 2) return 'score-medium';
    return 'score-low';
  };

  return (
    <div className={`verdict-feedback-container ${isSealed ? 'sealed' : ''}`}>
      <div className="verdict-paper">
        <div className="verdict-header">
          <h1 className="verdict-title">中华人民共和国法院</h1>
          <div className="verdict-case-id">{caseObj.id}</div>
        </div>

        {/* 结案印章 - 圆形且更大，盖在文书右上角 */}
        {isSealed && (
          <div className="verdict-seal">
            <div className="seal-inner">
              <div className="seal-text-top">中华人民共和国</div>
              <div className="seal-text-main">已结案</div>
              <div className="seal-text-bottom">人民法院</div>
              <div className="seal-date">{new Date().toLocaleDateString()}</div>
            </div>
          </div>
        )}

        <div className="feedback-header">
          <div className="rating-badge">{currentRankName}</div>
          <div className="score-summary">
            <div className="total-score">本次得分: {totalScore}</div>
            <div className={`rank-change ${scoreChange >= 0 ? 'plus' : 'minus'}`}>
              段位分: {scoreChange >= 0 ? `+${scoreChange}` : scoreChange}
            </div>
          </div>
        </div>

        <div className="comparison-grid">
          <div className="comp-item">
            <div className={`block-score ${getScoreClass(breakdown.charge.score, 50)}`}>
              {breakdown.charge.score}/50
            </div>
            <h4>罪名判定</h4>
            <div className="comp-row">
              <div className="comp-col">
                <label>玩家</label>
                <div className={`val ${breakdown.charge.isCorrect ? 'correct' : 'wrong'}`}>
                  {playerJudgment.charge || '无罪'}
                </div>
              </div>
              <div className="comp-col">
                <label>实际</label>
                <div className="val actual">{caseObj.actualJudgment.charge}</div>
              </div>
            </div>
            <div className="deviation-note">
              {breakdown.charge.isCorrect ? '判定准确' : '判定有误'}
            </div>
          </div>

          <div className="comp-item">
            <div className={`block-score ${getScoreClass(breakdown.penalty.score, 40)}`}>
              {breakdown.penalty.score}/40
            </div>
            <h4>刑期判定</h4>
            <div className="comp-row">
              <div className="comp-col">
                <label>玩家</label>
                <div className="val">
                  {playerJudgment.mainPenalty}
                  {!['无期徒刑', '死刑'].includes(playerJudgment.mainPenalty) && (
                    <>
                      {playerJudgment.years > 0 && ` ${playerJudgment.years}年`}
                      {playerJudgment.months > 0 && ` ${playerJudgment.months}个月`}
                      {playerJudgment.days > 0 && ` ${playerJudgment.days}日`}
                      {playerJudgment.years === 0 && playerJudgment.months === 0 && playerJudgment.days === 0 && ' 0天'}
                    </>
                  )}
                </div>
              </div>
              <div className="comp-col">
                <label>实际</label>
                <div className="val actual">
                  {caseObj.actualJudgment.mainPenalty}
                  {!['无期徒刑', '死刑'].includes(caseObj.actualJudgment.mainPenalty) && (
                    <>
                      {caseObj.actualJudgment.years > 0 && ` ${caseObj.actualJudgment.years}年`}
                      {caseObj.actualJudgment.months > 0 && ` ${caseObj.actualJudgment.months}个月`}
                      {caseObj.actualJudgment.days > 0 && ` ${caseObj.actualJudgment.days}日`}
                      {caseObj.actualJudgment.years === 0 && caseObj.actualJudgment.months === 0 && caseObj.actualJudgment.days === 0 && ' 0天'}
                    </>
                  )}
                </div>
              </div>
            </div>
            <div className="deviation-note">{breakdown.penalty.deviation}</div>
          </div>

          <div className="comp-item">
            <div className={`block-score ${getScoreClass(breakdown.fine.score, 10)}`}>
              {breakdown.fine.score}/10
            </div>
            <h4>罚金判定</h4>
            <div className="comp-row">
              <div className="comp-col">
                <label>玩家</label>
                <div className={`val ${breakdown.fine.score >= 8 ? 'correct' : ''}`}>
                  {playerJudgment.hasFine ? `${playerJudgment.fineAmount}元` : '无罚金'}
                </div>
              </div>
              <div className="comp-col">
                <label>实际</label>
                <div className="val actual">
                  {caseObj.actualJudgment.hasFine ? `${caseObj.actualJudgment.fineAmount}元` : '无罚金'}
                </div>
              </div>
            </div>
            <div className="deviation-note">
              {breakdown.fine.score === 10 ? '分毫不差' : breakdown.fine.score > 0 ? '有所偏差' : '偏差较大或漏判'}
            </div>
          </div>
        </div>

        <div className="reasoning-section">
          <h3>【法院认定理由】</h3>
          <p>{caseObj.legalReasoning}</p>
        </div>

        <div className="verdict-section">
          <h3>【判决主文原文】</h3>
          <p className="verdict-text">{caseObj.verdictText}</p>
        </div>
      </div>
    </div>
  );
};

export default VerdictFeedback;
