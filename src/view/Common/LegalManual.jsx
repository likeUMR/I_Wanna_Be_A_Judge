import React, { useState, useEffect } from 'react';
import { LegalService } from '../../core/services/LegalService';
import './LegalManual.css';

const LegalManual = ({ scale = 1 }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [lawArticles, setLawArticles] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && (!lawArticles || lawArticles.length === 0)) {
      setLoading(true);
      LegalService.loadLegalManual().then(data => {
        setLawArticles(data || []);
        setLoading(false);
      });
    }
  }, [isOpen, lawArticles]);

  return (
    <>
      {/* 触发器包装器：镜像 app-container 的布局逻辑 */}
      <div 
        className="legal-manual-trigger-wrapper"
        style={{
          transform: `translateX(-50%) scale(${scale})`
        }}
      >
        <div 
          className="desk-book" 
          onClick={() => setIsOpen(true)}
          title="点击查阅《中华人民共和国刑法》"
        >
          <div className="book-tag">参考手册</div>
        </div>
      </div>

      {/* 手册弹出层 (全屏遮罩 + 侧边缩放内容) */}
      {isOpen && (
        <div className="manual-overlay" onClick={() => setIsOpen(false)}>
          <div 
            className="manual-content" 
            onClick={e => e.stopPropagation()}
            style={{
              '--manual-scale': scale,
              transformOrigin: 'bottom right'
            }}
          >
            <div className="manual-header">
              <h2>⚖️ 中华人民共和国刑法</h2>
              <button className="close-btn" onClick={() => setIsOpen(false)}>×</button>
            </div>
            
            <div className="manual-body">
              {loading ? (
                <div className="loading-text">正在翻阅法典...</div>
              ) : (
                <div className="articles-list">
                  <p className="manual-intro">
                    本手册收录了审判实践中引用频率最高的 20 条刑法条文，供各位法官参考。
                  </p>
                  {lawArticles.map((art, index) => (
                    <div key={art.id} className="article-item">
                      <div className="article-num">
                        <span className="rank">#{index + 1}</span> {art.num_cn}
                      </div>
                      <div className="article-title">{art.title}</div>
                      <div className="article-text">{art.content}</div>
                      <div className="article-footer">
                        引用次数: {art.citation_count?.toLocaleString() || 0}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default LegalManual;
