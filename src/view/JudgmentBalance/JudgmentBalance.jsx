import React from 'react';
import './JudgmentBalance.css';

const JudgmentBalance = ({ factors, selectedFactors, onToggleFactor }) => {
  const allAggravating = [
    { id: 'isRecidivist', label: '累犯', isActual: factors.isRecidivist },
    { id: 'isMain', label: '主犯', isActual: factors.role === '主犯' },
    { id: 'multiple', label: '多次作案', isActual: false }, // Placeholder
  ];

  const allMitigating = [
    { id: 'isAttempt', label: '犯罪未遂', isActual: factors.isAttempt },
    { id: 'isSurrender', label: '自首', isActual: factors.isSurrender },
    { id: 'isCommendable', label: '立功', isActual: factors.isCommendable },
    { id: 'isConfessed', label: '如实供述', isActual: factors.isConfessed },
    { id: 'isPlea', label: '认罪认罚', isActual: factors.isPlea },
    { id: 'isRepented', label: '退赃赔偿', isActual: factors.isRepented },
  ];

  return (
    <div className="judgment-balance-inner">
      <h4 className="inner-title">量刑调节因子</h4>
      
      <div className="balance-container">
        <div className="balance-side left-side">
          <h5>加重因子 (红色)</h5>
          <div className="factors-grid">
            {allAggravating.map(f => (
              <label key={f.id} className={`factor-item ${selectedFactors.aggravating.includes(f.id) ? 'selected' : ''}`}>
                <input 
                  type="checkbox" 
                  checked={selectedFactors.aggravating.includes(f.id)}
                  onChange={() => onToggleFactor('aggravating', f.id)}
                />
                {f.label}
              </label>
            ))}
          </div>
        </div>

        <div className="balance-pivot">⚖️</div>

        <div className="balance-side right-side">
          <h5>减轻因子 (绿色)</h5>
          <div className="factors-grid">
            {allMitigating.map(f => (
              <label key={f.id} className={`factor-item ${selectedFactors.mitigating.includes(f.id) ? 'selected' : ''}`}>
                <input 
                  type="checkbox" 
                  checked={selectedFactors.mitigating.includes(f.id)}
                  onChange={() => onToggleFactor('mitigating', f.id)}
                />
                {f.label}
              </label>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default JudgmentBalance;
