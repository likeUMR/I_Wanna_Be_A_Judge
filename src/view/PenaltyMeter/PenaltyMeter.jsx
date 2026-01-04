import React from 'react';
import './PenaltyMeter.css';

const PenaltyMeter = ({ hasFine, fineAmount, onChange }) => {
  // 使用本地状态同步滑块，解决在缩放容器中频繁重绘导致的失焦问题
  const [localAmount, setLocalAmount] = React.useState(fineAmount);

  // 同步外部变化（如点击快速按钮）
  React.useEffect(() => {
    setLocalAmount(fineAmount);
  }, [fineAmount]);

  const handleSliderChange = (e) => {
    const val = parseInt(e.target.value, 10);
    setLocalAmount(val);
    onChange('fineAmount', val);
  };

  const handleInputChange = (e) => {
    const val = parseInt(e.target.value, 10) || 0;
    setLocalAmount(val);
    onChange('fineAmount', val);
  };

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
              value={localAmount} 
              onChange={handleInputChange}
              step="500"
              min="0"
              max="50000"
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
            max="50000" 
            step="500"
            value={localAmount}
            onChange={handleSliderChange}
          />
        </div>
      )}
    </div>
  );
};

export default PenaltyMeter;
