import React from 'react';
import './JudgeRankStatus.css';

const JudgeRankStatus = ({ rankInfo, totalScore, scoreChange, statistics }) => {
  const { current, next, progress } = rankInfo;
  const { totalCases, averageScore, bestScore } = statistics || { totalCases: 0, averageScore: 0, bestScore: 0 };

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

      <div className="stats-sidebar">
        <div className="stat-row">
          <span className="stat-label">结案总数</span>
          <span className="stat-value">{totalCases}</span>
        </div>
        <div className="stat-row">
          <span className="stat-label">平均评分</span>
          <span className="stat-value">{averageScore}</span>
        </div>
        <div className="stat-row">
          <span className="stat-label">历史最高</span>
          <span className="stat-value">{bestScore}</span>
        </div>
      </div>
    </div>
  );
};

export default JudgeRankStatus;
