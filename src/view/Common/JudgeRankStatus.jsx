import React from 'react';
import './JudgeRankStatus.css';

const JudgeRankStatus = ({ rankInfo, totalScore, scoreChange }) => {
  const { current, next, progress } = rankInfo;

  return (
    <div className="judge-rank-status">
      <div className="rank-badge">
        <div className="badge-inner">
          <div className="rank-name">{current.name}</div>
          <div className="score-display">
            <span className="total-val">{totalScore}</span>
            {scoreChange !== 0 && (
              <span className={`score-pop ${scoreChange > 0 ? 'plus' : 'minus'}`}>
                {scoreChange > 0 ? `+${scoreChange}` : scoreChange}
              </span>
            )}
          </div>
        </div>
      </div>
      
      <div className="rank-progress-container">
        <div className="progress-track">
          <div className="progress-fill" style={{ width: `${progress}%` }}></div>
        </div>
        <div className="next-rank-hint">
          {next ? `距离 ${next.name} 还需要 ${next.minScore - totalScore} 分` : '已达最高级别'}
        </div>
      </div>
    </div>
  );
};

export default JudgeRankStatus;
