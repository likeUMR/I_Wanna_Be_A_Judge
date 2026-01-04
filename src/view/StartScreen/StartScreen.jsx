import { useState } from 'react';
import { storageService } from '../../services/storageService';
import './StartScreen.css';

/**
 * 启动屏幕组件
 * @param {boolean} isReady 是否准备就绪
 * @param {string} status 当前加载状态描述
 * @param {function} onStart 点击开始后的回调
 * @param {function} onOpening 开始拉开帷幕的回调
 */
const StartScreen = ({ isReady, status, onStart, onOpening }) => {
  const [isStarted, setIsStarted] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleStart = () => {
    if (!isReady || showConfirm) return;
    setIsStarted(true);
    if (onOpening) onOpening();
    
    // 等待拉开动画执行完毕后再通知父组件
    setTimeout(() => {
      onStart();
    }, 1500);
  };

  const handleClearHistory = () => {
    storageService.clear();
    setShowConfirm(false);
    window.location.reload(); // 刷新页面以重置所有状态
  };

  // 刺绣文字内容
  const TitleSVG = () => (
    <svg className="embroidery-svg" viewBox="0 0 2000 400">
      <defs>
        <linearGradient id="goldGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#ffd700" />
          <stop offset="50%" stopColor="#b8860b" />
          <stop offset="100%" stopColor="#ffd700" />
        </linearGradient>
        <filter id="embroidery-filter">
          <feTurbulence type="fractalNoise" baseFrequency="0.5" numOctaves="3" result="noise" />
          <feDisplacementMap in="SourceGraphic" in2="noise" scale="2" />
        </filter>
      </defs>
      <text 
        x="50%" 
        y="50%" 
        dominantBaseline="middle" 
        textAnchor="middle" 
        className="embroidery-text"
        filter="url(#embroidery-filter)"
      >
        我要当法官
      </text>
    </svg>
  );

  return (
    <div className={`start-screen ${isStarted ? 'started' : ''}`}>
      <div className="curtain-container">
        <div className="curtain-left">
          <div className="embroidery-container left">
            <TitleSVG />
          </div>
        </div>
        <div className="curtain-right">
          <div className="embroidery-container right">
            <TitleSVG />
          </div>
          
          {/* 清除存档按钮 - 火漆印章风格 */}
          {!isStarted && (
            <div className="seal-button-container">
              <button className="seal-button" onClick={() => setShowConfirm(true)}>
                <div className="seal-icon">废</div>
                <div className="seal-text">清除存档</div>
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="start-content">
        <button 
          className={`gavel-icon-btn ${!isReady ? 'loading' : ''}`} 
          onClick={handleStart}
          disabled={!isReady || showConfirm}
        >
          <img src="/favicon.svg" alt="法槌图标" />
          <span className="start-btn-text">
            {isReady ? '开启审判' : '正在准备'}
          </span>
        </button>
        <p className="loading-status">{status}</p>
      </div>

      {/* 复古确认弹窗 */}
      {showConfirm && (
        <div className="vintage-modal-overlay">
          <div className="vintage-modal">
            <div className="modal-paper">
              <h3>⚠️ 档案清理确认</h3>
              <p>您确定要焚毁所有的审判记录和荣誉存档吗？此操作不可撤销，法官职业生涯将重新开始。</p>
              <div className="modal-actions">
                <button className="modal-btn confirm" onClick={handleClearHistory}>确认焚毁</button>
                <button className="modal-btn cancel" onClick={() => setShowConfirm(false)}>暂且保留</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StartScreen;
