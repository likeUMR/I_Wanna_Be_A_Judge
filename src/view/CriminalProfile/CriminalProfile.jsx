import React from 'react';
import './CriminalProfile.css';

const CriminalProfile = ({ defendant }) => {
  if (!defendant) return null;

  return (
    <div className="criminal-profile-card">
      <div className="confidential-stamp">CONFIDENTIAL</div>
      
      <div className="avatar-placeholder">
        <div className="avatar-icon">👤</div>
        <div className="avatar-overlay">刑事侦查案卷</div>
      </div>

      <h2 className="profile-title">被告人档案</h2>
      
      <div className="profile-content">
        <div className="profile-row">
          <span className="label">姓名：</span>
          <span className="value">{defendant.name}</span>
        </div>
        <div className="profile-row">
          <span className="label">性别：</span>
          <span className="value">{defendant.gender}</span>
          <span className="label ml-20">年龄：</span>
          <span className="value">{defendant.age > 0 ? `${defendant.age}岁` : '不详'}</span>
        </div>
        <div className="profile-row">
          <span className="label">职业：</span>
          <span className="value">{defendant.occupation}</span>
        </div>
        <div className="profile-row">
          <span className="label">文化程度：</span>
          <span className="value">{defendant.education}</span>
        </div>
        
        <div className="legal-status-section">
          <h3 className="section-subtitle">生理状态 (Physiological Status)</h3>
          <div className="tags-container">
            {defendant.isMinor && <span className="tag blue">未成年</span>}
            <span className="tag purple">{defendant.physiologicalStatus}</span>
          </div>
        </div>

        <div className="history-section">
          <h3 className="section-subtitle">历史战绩 (Criminal Record)</h3>
          <p className="record-text">{defendant.criminalRecord}</p>
        </div>
      </div>
    </div>
  );
};

export default CriminalProfile;
