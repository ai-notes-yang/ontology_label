import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './App.css';

// API地址：优先使用环境变量，否则使用本地开发地址
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

// Toast通知组件
function Toast({ toasts, removeToast }) {
  return (
    <div className="toast-container">
      {toasts.map((toast, index) => (
        <div key={index} className={`toast ${toast.type}`} onClick={() => removeToast(index)}>
          {toast.type === 'success' && '✓ '}
          {toast.type === 'error' && '✕ '}
          {toast.type === 'info' && 'ℹ '}
          {toast.message}
        </div>
      ))}
    </div>
  );
}

// 单行意图组件 - 支持行内编辑
function IntentRow({ intent, onReview, onPass, getCategoryClass, getStatusClass }) {
  const [editData, setEditData] = useState({
    judgement: intent.judgement || '',
    judged_by: intent.judged_by || 'user1',
    modified_content: intent.modified_content || ''
  });
  const [isEditing, setIsEditing] = useState(false);
  const [showModifyInput, setShowModifyInput] = useState(false);

  // 当intent变化时重置编辑数据
  useEffect(() => {
    setEditData({
      judgement: intent.judgement || '',
      judged_by: intent.judged_by || 'user1',
      modified_content: intent.modified_content || ''
    });
    setShowModifyInput(intent.judgement === '需修改');
  }, [intent]);

  const handleJudgementChange = (value) => {
    setEditData(prev => ({ ...prev, judgement: value }));
    setShowModifyInput(value === '需修改');
    setIsEditing(true);
  };

  const handleSubmit = () => {
    if (!editData.judgement) {
      alert('请选择核对结果');
      return;
    }
    onReview(intent.id, editData);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditData({
      judgement: intent.judgement || '',
      judged_by: intent.judged_by || 'user1',
      modified_content: intent.modified_content || ''
    });
    setShowModifyInput(intent.judgement === '需修改');
    setIsEditing(false);
  };

  return (
    <tr className={isEditing ? 'editing' : ''}>
      <td><span className="intent-id">{intent.intent_id}</span></td>
      <td><span className="intent-stage">{intent.stage.replace(/_/g, ' ')}</span></td>
      <td>
        <span className={`intent-category ${getCategoryClass(intent.category)}`}>
          {intent.category}
        </span>
      </td>
      <td>
        <div className="intent-comment-full">
          {intent.original_comment}
        </div>
      </td>
      <td>
        <span className={`intent-status ${getStatusClass(intent.review_status)}`}>
          {intent.review_status === '待核对' && '○ '}
          {intent.review_status === '已核对' && '● '}
          {intent.review_status === '直接通过' && '✓ '}
          {intent.review_status}
        </span>
      </td>
      <td>
        <div className="inline-judgement">
          <select
            className="judgement-select"
            value={editData.judgement}
            onChange={(e) => handleJudgementChange(e.target.value)}
          >
            <option value="">请选择</option>
            <option value="通过">✓ 通过</option>
            <option value="需修改">✎ 需修改</option>
            <option value="删除">✕ 删除</option>
            <option value="待定">⋯ 待定</option>
          </select>
        </div>
      </td>
      <td>
        {showModifyInput ? (
          <textarea
            className="inline-textarea"
            value={editData.modified_content}
            onChange={(e) => {
              setEditData(prev => ({ ...prev, modified_content: e.target.value }));
              setIsEditing(true);
            }}
            placeholder="请输入修改后内容"
            rows={2}
          />
        ) : (
          <span className="modified-content-display">
            {intent.modified_content || '-'}
          </span>
        )}
      </td>
      <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
        {intent.judge_date || '-'}
      </td>
      <td>
        <div className="intent-actions">
          {isEditing ? (
            <>
              <button className="btn btn-primary btn-sm" onClick={handleSubmit}>
                保存
              </button>
              <button className="btn btn-ghost btn-sm" onClick={handleCancel}>
                取消
              </button>
            </>
          ) : (
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => onPass(intent)}
              disabled={intent.review_status !== '待核对'}
            >
              直接通过
            </button>
          )}
        </div>
      </td>
    </tr>
  );
}

function App() {
  // 状态管理
  const [stepTypes, setStepTypes] = useState([]);
  const [selectedStep, setSelectedStep] = useState('atomic_intent');
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [intents, setIntents] = useState([]);
  const [pagination, setPagination] = useState({
    total: 0,
    pages: 1,
    current_page: 1,
    per_page: 10
  });
  const [loading, setLoading] = useState(false);
  const [toasts, setToasts] = useState([]);
  const [dragOver, setDragOver] = useState(false);
  const [jumpPage, setJumpPage] = useState('');

  // Toast提示
  const showToast = useCallback((message, type = 'info') => {
    setToasts(prev => [...prev, { message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.slice(1));
    }, 3000);
  }, []);

  const removeToast = useCallback((index) => {
    setToasts(prev => prev.filter((_, i) => i !== index));
  }, []);

  // 获取步骤类型
  useEffect(() => {
    axios.get(`${API_BASE}/step-types`)
      .then(res => {
        if (res.data.success) {
          setStepTypes(res.data.data);
        }
      })
      .catch(err => {
        console.error('获取步骤类型失败:', err);
        showToast('获取步骤类型失败', 'error');
      });
  }, [showToast]);

  // 获取文件列表
  const fetchFiles = useCallback(() => {
    if (selectedStep !== 'atomic_intent') return;
    
    axios.get(`${API_BASE}/files`, { params: { step_type: selectedStep } })
      .then(res => {
        if (res.data.success) {
          setFiles(res.data.data);
          // 更新选中文件的信息
          if (selectedFile) {
            const updatedFile = res.data.data.find(f => f.id === selectedFile.id);
            if (updatedFile) {
              setSelectedFile(updatedFile);
            }
          }
        }
      })
      .catch(err => {
        console.error('获取文件列表失败:', err);
        showToast('获取文件列表失败', 'error');
      });
  }, [selectedStep, selectedFile, showToast]);

  useEffect(() => {
    fetchFiles();
  }, [selectedStep]); // eslint-disable-line react-hooks/exhaustive-deps

  // 获取意图列表
  const fetchIntents = useCallback((page = 1, perPage = pagination.per_page) => {
    if (!selectedFile) return;
    
    setLoading(true);
    axios.get(`${API_BASE}/intents`, {
      params: {
        file_id: selectedFile.id,
        page: page,
        per_page: perPage
      }
    })
      .then(res => {
        if (res.data.success) {
          setIntents(res.data.data.items);
          setPagination({
            total: res.data.data.total,
            pages: res.data.data.pages,
            current_page: res.data.data.current_page,
            per_page: res.data.data.per_page
          });
        }
      })
      .catch(err => {
        console.error('获取意图列表失败:', err);
        showToast('获取意图列表失败', 'error');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [selectedFile, pagination.per_page, showToast]);

  useEffect(() => {
    if (selectedFile) {
      fetchIntents(1);
    }
  }, [selectedFile]); // eslint-disable-line react-hooks/exhaustive-deps

  // 文件上传处理
  const handleFileUpload = async (file) => {
    if (!file) return;
    if (!file.name.endsWith('.json')) {
      showToast('请上传JSON文件', 'error');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('step_type', selectedStep);

    try {
      const res = await axios.post(`${API_BASE}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      if (res.data.success) {
        showToast(res.data.message, 'success');
        fetchFiles();
        setSelectedFile(res.data.data);
      } else {
        showToast(res.data.message || '上传失败', 'error');
      }
    } catch (err) {
      console.error('上传失败:', err);
      showToast(err.response?.data?.message || '上传失败', 'error');
    }
  };

  // 拖拽上传
  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    handleFileUpload(file);
  };

  // 删除文件
  const handleDeleteFile = async (fileId, e) => {
    e.stopPropagation();
    if (!window.confirm('确定要删除此文件吗？所有相关数据将被删除。')) return;

    try {
      const res = await axios.delete(`${API_BASE}/files/${fileId}`);
      if (res.data.success) {
        showToast('删除成功', 'success');
        if (selectedFile?.id === fileId) {
          setSelectedFile(null);
          setIntents([]);
        }
        fetchFiles();
      }
    } catch (err) {
      showToast('删除失败', 'error');
    }
  };

  // 行内核对提交
  const handleInlineReview = async (intentId, formData) => {
    try {
      const res = await axios.post(`${API_BASE}/intents/${intentId}/review`, formData);
      if (res.data.success) {
        showToast('核对成功', 'success');
        fetchIntents(pagination.current_page);
        fetchFiles();
      }
    } catch (err) {
      showToast('核对失败', 'error');
    }
  };

  // 直接通过
  const handlePassIntent = async (intent) => {
    try {
      const res = await axios.post(`${API_BASE}/intents/${intent.id}/pass`, {
        judged_by: 'user1'
      });
      if (res.data.success) {
        showToast('已标记为通过', 'success');
        fetchIntents(pagination.current_page);
        fetchFiles();
      }
    } catch (err) {
      showToast('操作失败', 'error');
    }
  };

  // 页码跳转
  const handlePageJump = () => {
    const page = parseInt(jumpPage);
    if (page && page >= 1 && page <= pagination.pages) {
      fetchIntents(page);
      setJumpPage('');
    }
  };

  // 导出文件下载
  const handleExportFile = (fileId, format) => {
    const url = `${API_BASE}/files/${fileId}/export?format=${format}`;
    
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', '');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showToast(`正在导出${format.toUpperCase()}文件...`, 'info');
  };

  // 获取状态标签样式
  const getStatusClass = (status) => {
    switch (status) {
      case '待核对': return 'pending';
      case '已核对': return 'reviewed';
      case '直接通过': return 'passed';
      default: return 'pending';
    }
  };

  // 获取类别样式
  const getCategoryClass = (category) => {
    switch (category?.toLowerCase()) {
      case 'fact': return 'fact';
      case 'action': return 'action';
      case 'logic': return 'logic';
      default: return '';
    }
  };

  return (
    <div className="app">
      <Toast toasts={toasts} removeToast={removeToast} />
      
      {/* 头部导航 */}
      <header className="header">
        <div className="header-left">
          <div className="logo">
            <div className="logo-icon">O</div>
            <span className="logo-text">本体数据标注平台</span>
          </div>
          
          <div className="step-selector">
            <label>当前步骤：</label>
            <select
              value={selectedStep}
              onChange={(e) => {
                setSelectedStep(e.target.value);
                setSelectedFile(null);
                setIntents([]);
              }}
            >
              {stepTypes.map(step => (
                <option key={step.value} value={step.value}>
                  {step.label}
                </option>
              ))}
            </select>
          </div>
        </div>
        
        <div className="header-right">
          <div className="user-info">
            <div className="user-avatar">U1</div>
            <span>user1</span>
          </div>
        </div>
      </header>
      
      {/* 主内容区 */}
      <main className="main-content">
        {selectedStep !== 'atomic_intent' ? (
          // 建设中提示
          <div className="under-construction">
            <div className="construction-icon">🚧</div>
            <h2 className="construction-title">正在建设中...</h2>
            <p className="construction-text">
              "{stepTypes.find(s => s.value === selectedStep)?.label || selectedStep}" 功能即将上线，敬请期待！
            </p>
          </div>
        ) : (
          <>
            {/* 文件上传区域 */}
            <section className="upload-section">
              <h3>📤 上传JSON文件</h3>
              <div
                className={`upload-zone ${dragOver ? 'dragover' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
              >
                <input
                  type="file"
                  accept=".json"
                  onChange={(e) => handleFileUpload(e.target.files[0])}
                />
                <div className="upload-icon">📁</div>
                <p className="upload-text">
                  拖拽文件到此处，或 <span>点击选择文件</span>
                </p>
              </div>
            </section>
            
            {/* 文件列表 */}
            {files.length > 0 && (
              <section className="file-list-section">
                <h3>📂 已上传文件 ({files.length})</h3>
                <div className="file-list">
                  {files.map(file => (
                    <div
                      key={file.id}
                      className={`file-item ${selectedFile?.id === file.id ? 'active' : ''}`}
                      onClick={() => setSelectedFile(file)}
                    >
                      <div className="file-info">
                        <span className="file-name">{file.original_filename}</span>
                        <span className="file-meta">{file.created_at}</span>
                      </div>
                      <div className="file-progress">
                        <div className="progress-bar">
                          <div
                            className="progress-fill"
                            style={{ width: `${file.total_items > 0 ? (file.reviewed_items / file.total_items * 100) : 0}%` }}
                          />
                        </div>
                        <span>{file.reviewed_items}/{file.total_items}</span>
                      </div>
                      <div className="file-actions">
                        <button
                          className="btn-icon btn-export"
                          onClick={(e) => { e.stopPropagation(); handleExportFile(file.id, 'json'); }}
                          title="导出JSON"
                        >
                          📥
                        </button>
                        <button
                          className="btn-icon btn-export"
                          onClick={(e) => { e.stopPropagation(); handleExportFile(file.id, 'csv'); }}
                          title="导出CSV"
                        >
                          📊
                        </button>
                        <button
                          className="btn-icon"
                          onClick={(e) => handleDeleteFile(file.id, e)}
                          title="删除文件"
                        >
                          🗑
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}
            
            {/* 意图列表 */}
            {selectedFile && (
              <section className="intent-list-section">
                <div className="section-header">
                  <h3>📋 意图列表 - {selectedFile.original_filename}</h3>
                  <div className="section-header-right">
                    <div className="intent-stats">
                      <span>共 {pagination.total} 条</span>
                      <span>已核对 {selectedFile.reviewed_items} 条</span>
                    </div>
                    <div className="export-buttons">
                      <button
                        className="btn btn-export-main"
                        onClick={() => handleExportFile(selectedFile.id, 'json')}
                      >
                        📥 导出JSON
                      </button>
                      <button
                        className="btn btn-export-main"
                        onClick={() => handleExportFile(selectedFile.id, 'csv')}
                      >
                        📊 导出CSV
                      </button>
                    </div>
                  </div>
                </div>
                
                {loading ? (
                  <div className="loading">
                    <div className="loading-spinner" />
                  </div>
                ) : intents.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-state-icon">📭</div>
                    <p className="empty-state-text">暂无数据</p>
                  </div>
                ) : (
                  <>
                    <div className="table-container">
                      <table className="intent-table inline-edit-table">
                        <thead>
                          <tr>
                            <th style={{ width: '100px' }}>意图ID</th>
                            <th style={{ width: '160px' }}>阶段</th>
                            <th style={{ width: '70px' }}>类别</th>
                            <th style={{ minWidth: '200px' }}>原始内容</th>
                            <th style={{ width: '90px' }}>状态</th>
                            <th style={{ width: '110px' }}>核对结果</th>
                            <th style={{ width: '180px' }}>修改后内容</th>
                            <th style={{ width: '140px' }}>核对时间</th>
                            <th style={{ width: '130px' }}>操作</th>
                          </tr>
                        </thead>
                        <tbody>
                          {intents.map(intent => (
                            <IntentRow
                              key={intent.id}
                              intent={intent}
                              onReview={handleInlineReview}
                              onPass={handlePassIntent}
                              getCategoryClass={getCategoryClass}
                              getStatusClass={getStatusClass}
                            />
                          ))}
                        </tbody>
                      </table>
                    </div>
                    
                    {/* 分页 */}
                    <div className="pagination">
                      <div className="pagination-info">
                        第 {pagination.current_page} 页，共 {pagination.pages} 页
                      </div>
                      
                      <div className="pagination-controls">
                        <div className="page-size-selector">
                          <label>每页</label>
                          <select
                            value={pagination.per_page}
                            onChange={(e) => fetchIntents(1, parseInt(e.target.value))}
                          >
                            <option value={5}>5</option>
                            <option value={10}>10</option>
                            <option value={20}>20</option>
                            <option value={50}>50</option>
                          </select>
                          <label>条</label>
                        </div>
                        
                        <button
                          className="pagination-btn"
                          onClick={() => fetchIntents(1)}
                          disabled={pagination.current_page === 1}
                        >
                          ««
                        </button>
                        <button
                          className="pagination-btn"
                          onClick={() => fetchIntents(pagination.current_page - 1)}
                          disabled={pagination.current_page === 1}
                        >
                          ‹
                        </button>
                        
                        {/* 页码按钮 */}
                        {Array.from({ length: Math.min(5, pagination.pages) }, (_, i) => {
                          let pageNum;
                          if (pagination.pages <= 5) {
                            pageNum = i + 1;
                          } else if (pagination.current_page <= 3) {
                            pageNum = i + 1;
                          } else if (pagination.current_page >= pagination.pages - 2) {
                            pageNum = pagination.pages - 4 + i;
                          } else {
                            pageNum = pagination.current_page - 2 + i;
                          }
                          return (
                            <button
                              key={pageNum}
                              className={`pagination-btn ${pagination.current_page === pageNum ? 'active' : ''}`}
                              onClick={() => fetchIntents(pageNum)}
                            >
                              {pageNum}
                            </button>
                          );
                        })}
                        
                        <button
                          className="pagination-btn"
                          onClick={() => fetchIntents(pagination.current_page + 1)}
                          disabled={pagination.current_page === pagination.pages}
                        >
                          ›
                        </button>
                        <button
                          className="pagination-btn"
                          onClick={() => fetchIntents(pagination.pages)}
                          disabled={pagination.current_page === pagination.pages}
                        >
                          »»
                        </button>
                        
                        <div className="page-jump">
                          <label>跳转</label>
                          <input
                            type="number"
                            min="1"
                            max={pagination.pages}
                            value={jumpPage}
                            onChange={(e) => setJumpPage(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handlePageJump()}
                          />
                          <button className="btn btn-ghost" onClick={handlePageJump}>Go</button>
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default App;
