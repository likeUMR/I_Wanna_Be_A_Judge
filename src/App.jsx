import { useState, useEffect, useCallback, useMemo } from 'react'
import { useAssets } from './hooks/useAssets'
import { useGame } from './hooks/useGame'

// Components
import CriminalProfile from './view/CriminalProfile/CriminalProfile'
import EvidenceDossier from './view/EvidenceDossier/EvidenceDossier'
import JudgmentBalance from './view/JudgmentBalance/JudgmentBalance'
import PenaltyMeter from './view/PenaltyMeter/PenaltyMeter'
import VerdictFeedback from './view/VerdictFeedback/VerdictFeedback'
import JudgeRankStatus from './view/Common/JudgeRankStatus'
import LocationSelector from './view/Common/LocationSelector'
import StartScreen from './view/StartScreen/StartScreen'
import LegalManual from './view/Common/LegalManual'

import './App.css'

function App() {
  const { isReady, loadingStatus, location: autoLocation, error: assetError } = useAssets()
  const [manualLocation, setManualLocation] = useState(null)
  const [isOpening, setIsOpening] = useState(false)
  const [gameStarted, setGameStarted] = useState(false)
  const [scale, setScale] = useState(1)
  
  // 当前生效的地理位置信息
  const currentLocation = manualLocation || autoLocation;

  // 处理分辨率适配
  useEffect(() => {
    const handleResize = () => {
      const designWidth = 1920;
      const designHeight = 960; // 16:8 比例
      const windowWidth = window.innerWidth;
      const windowHeight = window.innerHeight;
      
      const scaleX = windowWidth / designWidth;
      const scaleY = windowHeight / designHeight;
      
      const newScale = Math.min(scaleX, scaleY);
      setScale(newScale);
    };

    window.addEventListener('resize', handleResize);
    handleResize();
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  const {
    currentCase,
    loading: caseLoading,
    error: gameError,
    playerJudgment,
    showFeedback,
    scoring,
    totalScore,
    scoreChange,
    rankInfo,
    statistics,
    loadCase,
    submitJudgment,
    updateJudgment,
    toggleFactor
  } = useGame()

  // 当资产准备就绪且有位置信息时，预加载第一个案例
  useEffect(() => {
    if (isReady && autoLocation && !currentCase && !caseLoading) {
      loadCase(autoLocation.adcode || '110101')
    }
  }, [isReady, autoLocation, loadCase, currentCase, caseLoading])

  // 处理位置切换
  const handleManualLocationChange = (newLoc) => {
    setManualLocation(newLoc)
    if (newLoc) {
      loadCase(newLoc.adcode)
    } else {
      // 切回自动模式
      if (autoLocation) {
        loadCase(autoLocation.adcode || '110101')
      }
    }
  }

  // 内部结案状态同步，用于控制 App 层的法槌按钮和 Feedback 层的印章
  const [isSealed, setIsSealed] = useState(false);

  // 当反馈关闭时，重置结案状态
  useEffect(() => {
    if (!showFeedback) {
      setIsSealed(false);
    }
  }, [showFeedback]);

  const handleNextCase = useCallback(() => {
    if (isSealed) return;
    setIsSealed(true);
    // 延迟 1.5s 进入下一案，给印章动画留出时间
    setTimeout(() => {
      loadCase(currentLocation?.adcode || '110101');
    }, 600);
  }, [isSealed, loadCase, currentLocation]);

  // 错误合并
  const error = assetError || gameError;

  // 缓存容器样式，避免因对象引用变动导致浏览器重新计算变换而使滑块失焦
  const containerStyle = useMemo(() => ({
    transform: `scale(${scale}) translateZ(0)`, // 增加 translateZ(0) 开启硬件加速，提升缩放后的清晰度
    width: '1920px',
    height: '960px',
    transformOrigin: 'top center',
    visibility: 'visible',
    filter: isOpening ? 'none' : 'brightness(0.5)',
    transition: 'filter 1.5s ease',
    backfaceVisibility: 'hidden',
    WebkitFontSmoothing: 'antialiased'
  }), [scale, isOpening]);

  return (
    <div className="app-viewport">
      {/* 预加载关键图标，防止加载延迟 */}
      <div style={{ display: 'none', visibility: 'hidden', position: 'absolute', width: 0, height: 0, overflow: 'hidden' }}>
        <img src="favicon.svg" alt="preload-gavel" />
      </div>

      {!gameStarted && (
        <StartScreen 
          isReady={isReady} 
          status={loadingStatus} 
          onOpening={() => setIsOpening(true)}
          onStart={() => setGameStarted(true)} 
          scale={scale}
        />
      )}

      <div 
        className="app-container" 
        style={containerStyle}
      >
        {/* 庄重版法槌控件 - 现在位于 App 层级，绝对不受内部滚动影响 */}
        {showFeedback && (
          <div 
            className={`gavel-action-container ${isSealed ? 'sealed' : ''}`} 
            onClick={handleNextCase} 
            title="敲击法槌以结案"
          >
            <div className="gavel-action-icon">
              <img src="favicon.svg" alt="法槌" />
            </div>
            <div className="gavel-action-hint">结案</div>
          </div>
        )}

        <header className="game-header">
          <div className="header-left">
            <div className="logo">⚖️ 我 要 当 法 官</div>
          </div>
          <div className="header-center">
            {currentCase ? (
              <h2 className="court-name">
                {currentCase.court}
              </h2>
            ) : (
              <h2 className="court-name">
                中华人民共和国人民法院
              </h2>
            )}
          </div>
          <div className="header-right">
            <LocationSelector onLocationChange={handleManualLocationChange} />
            {currentLocation && (
              <div className={`location ${manualLocation ? 'manual' : ''}`}>
                📍 {currentLocation.province} · {currentLocation.city} · {currentLocation.district}
              </div>
            )}
          </div>
        </header>

        <main className="desk-area">
          {caseLoading ? (
            <div className="loading-case">案卷调取中...</div>
          ) : error ? (
            <div className="error-box">
              <p>异常: {error}</p>
              <button onClick={() => loadCase(currentLocation?.adcode || '110101')}>重试</button>
            </div>
          ) : currentCase && (
            <div className="workspace">
              {!showFeedback ? (
                <div className="trial-layout">
                  <div className="left-panel">
                    <CriminalProfile 
                      defendant={currentCase.defendant} 
                      court={currentCase.court}
                    />
                    <JudgeRankStatus 
                      rankInfo={rankInfo} 
                      totalScore={totalScore} 
                      scoreChange={scoreChange} 
                      statistics={statistics}
                    />
                  </div>
                  
                  <div className="center-panel">
                    <EvidenceDossier 
                      caseId={currentCase.id}
                      facts={currentCase.facts} 
                      evidences={currentCase.evidences} 
                    >
                      <JudgmentBalance 
                        factors={currentCase.factors}
                        selectedFactors={playerJudgment.selectedFactors}
                        onToggleFactor={toggleFactor}
                      />
                    </EvidenceDossier>
                  </div>
                  
                  <div className="right-panel">
                    <div className="judgment-form-container">
                      <h3>⚖️ 宣判草案</h3>
                      <div className="form-group">
                        <label>认定罪名</label>
                        <input 
                          type="text" 
                          value={playerJudgment.charge}
                          onChange={(e) => updateJudgment({ charge: e.target.value })}
                          placeholder="请输入罪名"
                        />
                      </div>
                      
                      <div className="form-group">
                        <label>刑罚类型</label>
                        <select 
                          value={playerJudgment.mainPenalty}
                          onChange={(e) => updateJudgment({ mainPenalty: e.target.value })}
                        >
                          <option value="有期徒刑">有期徒刑</option>
                          <option value="拘役">拘役</option>
                          <option value="管制">管制</option>
                          <option value="无期徒刑">无期徒刑</option>
                          <option value="死刑">死刑</option>
                        </select>
                      </div>

                      {['有期徒刑', '拘役', '管制'].includes(playerJudgment.mainPenalty) && (
                        <div className="duration-inputs">
                          <div className="input-with-label">
                            <input 
                              type="number" 
                              value={playerJudgment.years}
                              onChange={(e) => updateJudgment({ years: parseInt(e.target.value) || 0 })}
                              onWheel={(e) => {
                                e.preventDefault();
                                const delta = e.deltaY < 0 ? 1 : -1;
                                const newVal = Math.max(0, Math.min(25, playerJudgment.years + delta));
                                updateJudgment({ years: newVal });
                              }}
                              min="0"
                              max="25"
                            />
                            <span>年</span>
                          </div>
                          <div className="input-with-label">
                            <input 
                              type="number" 
                              value={playerJudgment.months}
                              onChange={(e) => updateJudgment({ months: parseInt(e.target.value) || 0 })}
                              onWheel={(e) => {
                                e.preventDefault();
                                const delta = e.deltaY < 0 ? 1 : -1;
                                const newVal = Math.max(0, Math.min(11, playerJudgment.months + delta));
                                updateJudgment({ months: newVal });
                              }}
                              min="0" max="11"
                            />
                            <span>月</span>
                          </div>
                        </div>
                      )}

                      <PenaltyMeter 
                        hasFine={playerJudgment.hasFine} 
                        fineAmount={playerJudgment.fineAmount} 
                        onChange={(field, val) => updateJudgment({ [field]: val })}
                      />

                      <button className="gavel-btn" onClick={submitJudgment}>
                        敲响法槌
                      </button>
                    </div>
                  </div>
                </div>
            ) : (
              <VerdictFeedback 
                caseObj={currentCase}
                playerJudgment={playerJudgment}
                scoring={scoring}
                scoreChange={scoreChange}
                rankInfo={rankInfo}
                isSealed={isSealed}
              />
            )}
          </div>
        )}
      </main>
      
      {/* 法律手册入口 */}
      <LegalManual />
      </div>
    </div>
  )
}

export default App
