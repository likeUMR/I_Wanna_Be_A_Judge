import React from 'react';
import './VerdictFeedback.css';

const VerdictFeedback = ({ caseObj, playerJudgment, scoring, scoreChange, rankInfo, onNextCase }) => {
  const { breakdown, totalScore } = scoring;
  const currentRankName = rankInfo?.current?.name || '见习法官';
  
  return (
    <div className="verdict-feedback">
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
          <h4>罪名判定</h4>
          <div className="comp-row">
            <div className="comp-col">
              <label>玩家</label>
              <div className={`val ${breakdown.charge.isCorrect ? 'correct' : 'wrong'}`}>
                {playerJudgment.charge}
              </div>
            </div>
            <div className="comp-col">
              <label>实际</label>
              <div className="val actual">{caseObj.actualJudgment.charge}</div>
            </div>
          </div>
        </div>

        <div className="comp-item">
          <h4>刑期判定</h4>
          <div className="comp-row">
            <div className="comp-col">
              <label>玩家</label>
              <div className="val">
                {playerJudgment.mainPenalty}
                {!['无期徒刑', '死刑'].includes(playerJudgment.mainPenalty) && ` ${playerJudgment.years}年${playerJudgment.months}月`}
              </div>
            </div>
            <div className="comp-col">
              <label>实际</label>
              <div className="val actual">
                {caseObj.actualJudgment.mainPenalty}
                {!['无期徒刑', '死刑'].includes(caseObj.actualJudgment.mainPenalty) && ` ${caseObj.actualJudgment.years}年${caseObj.actualJudgment.months}月`}
              </div>
            </div>
          </div>
          <div className="deviation-note">{breakdown.penalty.deviation}</div>
        </div>

        <div className="comp-item">
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

      <button className="next-btn" onClick={onNextCase}>审理下一案</button>
    </div>
  );
};

export default VerdictFeedback;
