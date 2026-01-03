import { useState, useEffect, useCallback } from 'react'
import { fetchFullLocation } from './services/locationService'
import { useGame } from './hooks/useGame'

// Components
import CriminalProfile from './view/CriminalProfile/CriminalProfile'
import EvidenceDossier from './view/EvidenceDossier/EvidenceDossier'
import JudgmentBalance from './view/JudgmentBalance/JudgmentBalance'
import PenaltyMeter from './view/PenaltyMeter/PenaltyMeter'
import VerdictFeedback from './view/VerdictFeedback/VerdictFeedback'
import JudgeRankStatus from './view/Common/JudgeRankStatus'
import LocationSelector from './view/Common/LocationSelector'

import './App.css'

function App() {
  const [location, setLocation] = useState(null)
  const [manualLocation, setManualLocation] = useState(null)
  const [locLoading, setLocLoading] = useState(true)
  const [districtStatus, setDistrictStatus] = useState('')
  const [scale, setScale] = useState(1)
  
  // 处理分辨率适配
  useEffect(() => {
    const handleResize = () => {
      const designWidth = 1920;
      const designHeight = 960; // 16:8 比例
      const windowWidth = window.innerWidth;
      const windowHeight = window.innerHeight;
      
      const scaleX = windowWidth / designWidth;
      const scaleY = windowHeight / designHeight;
      
      // 使用 cover 逻辑：让内容尽可能填满，但不裁剪核心区域
      // 或者使用 Math.min 确保全部可见，但背景铺满
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
    error,
    playerJudgment,
    showFeedback,
    scoring,
    totalScore,
    scoreChange,
    rankInfo,
    loadCase,
    submitJudgment,
    updateJudgment,
    toggleFactor
  } = useGame()

  // 统一的定位逻辑
  const initLocation = useCallback(async () => {
    setLocLoading(true)
    try {
      const loc = await fetchFullLocation(setDistrictStatus)
      setLocation(loc)
      setLocLoading(false)
      if (!manualLocation) {
        loadCase(loc.adcode || '110101')
      }
    } catch (err) {
      console.error('Location failed:', err)
      setLocLoading(false)
      if (!manualLocation) {
        loadCase('110101')
      }
    }
  }, [loadCase, manualLocation])

  // 处理位置切换
  const handleManualLocationChange = (newLoc) => {
    setManualLocation(newLoc)
    if (newLoc) {
      loadCase(newLoc.adcode)
    } else {
      // 切回自动模式，重新加载当前自动定位的案例
      if (location) {
        loadCase(location.adcode || '110101')
      } else {
        initLocation()
      }
    }
  }

  // Initial Location
  useEffect(() => {
    initLocation()
  }, []) // 仅在挂载时执行一次自动定位

  if (locLoading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>正在定位并准备您的法官办公室...</p>
        <p className="status">{districtStatus}</p>
      </div>
    )
  }

  return (
    <div className="app-viewport">
      <div 
        className="app-container" 
        style={{ 
          transform: `scale(${scale})`,
          width: '1920px',
          height: '960px',
          transformOrigin: 'top center'
        }}
      >
        <header className="game-header">
          <div className="header-left">
            <div className="logo">⚖️ I Wanna Be A Judge</div>
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
            {!manualLocation && location && (
              <div className="location">
                📍 {location.province} · {location.city} · {location.district}
              </div>
            )}
            {manualLocation && (
              <div className="location manual">
                📍 {manualLocation.province} · {manualLocation.city} · {manualLocation.district}
              </div>
            )}
          </div>
        </header>

        <main className="desk-area">
          {caseLoading ? (
            <div className="loading-case">案卷调取中...</div>
          ) : error ? (
            <div className="error-box">
              <p>案卷加载失败: {error}</p>
              <button onClick={() => loadCase(manualLocation?.adcode || location?.adcode || '110101')}>重试</button>
            </div>
          ) : currentCase && (
            <div className="workspace">
              {!showFeedback ? (
                <div className="trial-layout">
                  <div className="left-panel">
                    <CriminalProfile defendant={currentCase.defendant} />
                    <JudgeRankStatus rankInfo={rankInfo} totalScore={totalScore} scoreChange={scoreChange} />
                  </div>
                  
                  <div className="center-panel">
                    <EvidenceDossier 
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
                onNextCase={() => loadCase(manualLocation?.adcode || location?.adcode || '110101')}
              />
            )}
          </div>
        )}
      </main>
      </div>
    </div>
  )
}

export default App
