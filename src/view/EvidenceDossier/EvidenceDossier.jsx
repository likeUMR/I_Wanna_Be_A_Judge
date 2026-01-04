import React from 'react';
import './EvidenceDossier.css';

const EvidenceDossier = ({ facts, evidences, caseId, children }) => {
  return (
    <div className="evidence-dossier">
      <div className="case-id-tag">{caseId}</div>
      <h2 className="dossier-title">证据与事实清单</h2>
      
      <div className="scroll-area">
        <div className="dossier-section">
          <h3 className="section-header">【经审理查明】</h3>
          <div className="content-box facts-box">
            {facts}
          </div>
        </div>

        <div className="dossier-section">
          <h3 className="section-header">【证据列举】</h3>
          <div className="content-box evidence-box">
            {evidences}
          </div>
        </div>

        {/* 量刑因子现在显示在清单底部 */}
        {children}
      </div>
    </div>
  );
};

export default EvidenceDossier;
