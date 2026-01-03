import React from 'react';
import './PenaltyMeter.css';

const PenaltyMeter = ({ hasFine, fineAmount, onChange }) => {
  return (
    <div className="penalty-meter">
      <div className="meter-header">
        <h3>财产刑控制台</h3>
        <label className="switch-container">
          <span>处罚金</span>
          <input 
            type="checkbox" 
            checked={hasFine} 
            onChange={(e) => onChange('hasFine', e.target.checked)} 
          />
        </label>
      </div>

      {hasFine && (
        <div className="meter-body">
          <div className="amount-display">
            <span className="currency">¥</span>
            <input 
              type="number" 
              value={fineAmount} 
              onChange={(e) => onChange('fineAmount', e.target.value)}
              step="500"
              min="0"
            />
          </div>
          
          <div className="quick-buttons">
            {[1000, 2000, 5000, 10000, 20000, 50000].map(amt => (
              <button 
                key={amt} 
                className="quick-btn"
                onClick={() => onChange('fineAmount', amt)}
              >
                {amt >= 10000 ? `${amt/10000}万` : amt}
              </button>
            ))}
          </div>
          
          <input 
            type="range" 
            className="fine-slider"
            min="0" 
            max="100000" 
            step="500"
            value={fineAmount}
            onChange={(e) => onChange('fineAmount', e.target.value)}
          />
        </div>
      )}
    </div>
  );
};

export default PenaltyMeter;
