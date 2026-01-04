import { useState } from 'react';
import './StartScreen.css';

/**
 * 启动屏幕组件
 * @param {boolean} isReady 是否准备就绪
 * @param {string} status 当前加载状态描述
 * @param {function} onStart 点击开始后的回调
 */
const StartScreen = ({ isReady, status, onStart, onOpening }) => {
  const [isStarted, setIsStarted] = useState(false);

  const handleStart = () => {
    if (!isReady) return;
    setIsStarted(true);
    if (onOpening) onOpening(); // 通知父组件开始拉开了
    
    // 等待拉开动画执行完毕后再通知父组件卸载
    setTimeout(() => {
      onStart();
    }, 1500);
  };

  return (
    <div className={`start-screen ${isStarted ? 'started' : ''}`}>
      <div className="curtain-container">
        <div className="curtain-left"></div>
        <div className="curtain-right"></div>
      </div>

      <div className="start-content">
        <button 
          className={`gavel-icon-btn ${!isReady ? 'loading' : ''}`} 
          onClick={handleStart}
          disabled={!isReady}
        >
          <img src="/favicon.svg" alt="法槌图标" />
          <span className="start-btn-text">
            {isReady ? '开启审判' : '正在准备'}
          </span>
        </button>
        <p className="loading-status">{status}</p>
      </div>
    </div>
  );
};

export default StartScreen;
