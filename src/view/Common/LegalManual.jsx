import React, { useState, useEffect } from 'react';
import { LegalService } from '../../core/services/LegalService';
import './LegalManual.css';

const LegalManual = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [lawArticles, setLawArticles] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && lawArticles.length === 0) {
      setLoading(true);
      LegalService.loadLegalManual().then(data => {
        setLawArticles(data);
        setLoading(false);
      });
    }
  }, [isOpen, lawArticles.length]);

  return (
    <div className="legal-manual-container">
      {/* 桌面上的书本入口 */}
      <div 
        className="desk-book" 
        onClick={() => setIsOpen(true)}
        title="点击查阅《中华人民共和国刑法》"
      >
        <div className="book-tag">参考手册</div>
      </div>

      {/* 手册弹出层 (双页书本样式) */}
      {isOpen && (
        <div className="manual-overlay" onClick={() => setIsOpen(false)}>
          <div className="manual-content" onClick={e => e.stopPropagation()}>
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
                        引用次数: {art.citation_count.toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LegalManual;
