document.addEventListener('DOMContentLoaded', function() {
    const generateBtn = document.getElementById('generate-report-btn');
    const checkStatusBtn = document.getElementById('check-status-btn');
    const statusDiv = document.getElementById('report-status');
    
    if (generateBtn) {
        generateBtn.addEventListener('click', function() {
            // レポート作成中
            statusDiv.innerHTML = '<p>レポート作成中...</p>';
            generateBtn.disabled = true;
            generateBtn.textContent = '作成中...';
            
            // レポート作成リクエスト
            fetch('/generate-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    statusDiv.innerHTML = `
                        <div style="background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 10px; border-radius: 5px; margin-top: 10px;">
                            <h4>${data.message}</h4>
                            <p><strong>商品数:</strong> ${data.data.total_items}</p>
                            <p><strong>アクティブな商品:</strong> ${data.data.active_listings}</p>
                            <p><strong>カテゴリー:</strong> ${data.data.categories.join(', ')}</p>
                            <p><strong>生成時間:</strong> ${data.data.generated_at}</p>
                            <p><strong>要約:</strong> ${data.data.summary}</p>
                        </div>
                    `;
                    
                    // ダウンロードボタンを表示
                    const exportSection = document.getElementById('export-section');
                    if (exportSection) {
                        exportSection.style.display = 'block';
                    }
                } else if (data.status === 'task_created') {
                    statusDiv.innerHTML = `
                        <div style="background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 10px; border-radius: 5px; margin-top: 10px;">
                            <h4>${data.message}</h4>
                            <p><strong>タスクID:</strong> ${data.task_id}</p>
                            <p><strong>タスクステータス:</strong> ${data.data.task_status}</p>
                            <p><strong>生成時間:</strong> ${data.data.generated_at}</p>
                            <p><strong>説明:</strong> ${data.data.summary}</p>
                            <p><em>タスクの進行状況を確認するには、"Check Feed Status" ボタンを押してください</em></p>
                        </div>
                    `;
                    
                    // 状態チェックボタンを表示
                    if (checkStatusBtn) {
                        checkStatusBtn.style.display = 'inline-block';
                    }
                } else {
                    statusDiv.innerHTML = `
                        <div style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 10px; border-radius: 5px; margin-top: 10px;">
                            <p>エラー: ${data.error}</p>
                        </div>
                    `;
                }
            })
            .catch(error => {
                statusDiv.innerHTML = `
                    <div style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 10px; border-radius: 5px; margin-top: 10px;">
                        <p>リクエスト失敗: ${error.message}</p>
                    </div>
                `;
            })
            .finally(() => {
                // ボタンの状態を復元
                generateBtn.disabled = false;
                generateBtn.textContent = 'レポート作成';
            });
        });
    }
    
    if (checkStatusBtn) {
        checkStatusBtn.addEventListener('click', function() {
            // レポートの状態をチェック中
            statusDiv.innerHTML = '<p>リポート状態をチェック中...</p>';
            checkStatusBtn.disabled = true;
            checkStatusBtn.textContent = 'チェック中...';
            
            // レポートの状態をチェックするリクエスト
            fetch('/check-feed-status', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    statusDiv.innerHTML = `
                        <div style="background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 10px; border-radius: 5px; margin-top: 10px;">
                            <h4>${data.message}</h4>
                            <p><strong>生成時間:</strong> ${data.data.generated_at}</p>
                        </div>
                    `;
                    
                    // ダウンロードボタンを表示
                    const exportSection = document.getElementById('export-section');
                    if (exportSection) {
                        exportSection.style.display = 'block';
                    }
                    
                    // 状態チェックボタンを非表示
                    checkStatusBtn.style.display = 'none';
                } else if (data.status === 'in_progress') {
                    statusDiv.innerHTML = `
                        <div style="background: #cce5ff; border: 1px solid #99ccff; color: #004085; padding: 10px; border-radius: 5px; margin-top: 10px;">
                            <h4>${data.message}</h4>
                            <p><strong>タスクステータス:</strong> ${data.task_status}</p>
                            <p><em>タスクがまだ進行中です。しばらくしてから再度確認してください。</em></p>
                        </div>
                    `;
                } else {
                    statusDiv.innerHTML = `
                        <div style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 10px; border-radius: 5px; margin-top: 10px;">
                            <p>エラー: ${data.error}</p>
                        </div>
                    `;
                }
            })
            .catch(error => {
                statusDiv.innerHTML = `
                    <div style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 10px; border-radius: 5px; margin-top: 10px;">
                        <p>リクエスト失敗: ${error.message}</p>
                    </div>
                `;
            })
            .finally(() => {
                // ボタンの状態を復元
                checkStatusBtn.disabled = false;
                checkStatusBtn.textContent = 'Check Feed Status';
            });
        });
    }
    
    // 通过任务ID查询功能
    const queryTaskBtn = document.getElementById('query-task-btn');
    const taskIdInput = document.getElementById('task-id-input');
    const taskQueryResult = document.getElementById('task-query-result');
    
    if (queryTaskBtn && taskIdInput && taskQueryResult) {
        queryTaskBtn.addEventListener('click', function() {
            const taskId = taskIdInput.value.trim();
            
            if (!taskId) {
                taskQueryResult.innerHTML = `
                    <div style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 10px; border-radius: 5px;">
                        <p>タスクIDを入力してください</p>
                    </div>
                `;
                return;
            }
            
            taskQueryResult.innerHTML = '<p>タスク状態を検索中...</p>';
            queryTaskBtn.disabled = true;
            queryTaskBtn.textContent = '検索中...';
            
            fetch('/query-task-by-id', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ task_id: taskId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    const task = data.task;
                    const downloadButton = task.status === 'COMPLETED' ? 
                        `<div class="action-group" style="margin-top: 15px;">
                            <a href="/download-task-result/${task.task_id}" 
                               class="btn btn-primary download-btn">
                               📥 元ファイルダウンロード
                            </a>
                            <button onclick="generateEnhancedCSV('${task.task_id}')" 
                               class="btn btn-success enhanced-csv-btn" id="enhanced-csv-${task.task_id}">
                               📊 拡張CSV生成
                            </button>
                         </div>` : '';
                    
                    taskQueryResult.innerHTML = `
                        <div class="status-message status-success">
                            <h4>タスク詳細</h4>
                            <p><strong>タスクID:</strong> ${task.task_id}</p>
                            <p><strong>ステータス:</strong> <span class="report-status status-${task.status.toLowerCase()}">${task.status}</span></p>
                            <p><strong>作成時間:</strong> ${task.creation_date || 'N/A'}</p>
                            <p><strong>完了時間:</strong> ${task.completion_date || 'N/A'}</p>
                            <p><strong>Feedタイプ:</strong> ${task.feed_type}</p>
                            ${task.schema_version ? `<p><strong>Schemaバージョン:</strong> ${task.schema_version}</p>` : ''}
                            ${downloadButton}
                        </div>
                    `;
                } else {
                    taskQueryResult.innerHTML = `
                        <div class="status-message status-error">
                            <p>検索失敗: ${data.error}</p>
                        </div>
                    `;
                }
            })
            .catch(error => {
                taskQueryResult.innerHTML = `
                    <div class="status-message status-error">
                        <p>リクエスト失敗: ${error.message}</p>
                    </div>
                `;
            })
            .finally(() => {
                queryTaskBtn.disabled = false;
                queryTaskBtn.textContent = 'ステータス検索';
            });
        });
    }
    
    // 获取最近报告功能
    const getRecentReportsBtn = document.getElementById('get-recent-reports-btn');
    const daysInput = document.getElementById('days-input');
    const recentReportsList = document.getElementById('recent-reports-list');
    
    if (getRecentReportsBtn && daysInput && recentReportsList) {
        getRecentReportsBtn.addEventListener('click', function() {
            const days = daysInput.value || 7;
            
            recentReportsList.innerHTML = '<p>最近のリポートを取得中...</p>';
            getRecentReportsBtn.disabled = true;
            getRecentReportsBtn.textContent = '取得中...';
            
            fetch(`/get-recent-reports?days=${days}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    if (data.tasks && data.tasks.length > 0) {
                        let tasksHtml = `
                            <div class="status-message status-success">
                                <h4>📋 ${data.total_count} 個のタスクが見つかりました</h4>
                            </div>
                            <div class="reports-grid" style="max-height: 400px; overflow-y: auto;">
                        `;
                        
                        data.tasks.forEach(task => {
                            const downloadButton = task.status === 'COMPLETED' ? 
                                `<div class="action-group" style="margin-top: 15px;">
                                    <a href="/download-task-result/${task.task_id}" 
                                       class="btn btn-primary download-btn">
                                       📥 元ファイルダウンロード
                                    </a>
                                    <button onclick="generateEnhancedCSV('${task.task_id}')" 
                                       class="btn btn-success enhanced-csv-btn" id="enhanced-csv-list-${task.task_id}">
                                       📊 拡張CSV生成
                                    </button>
                                 </div>` : '';
                            
                            tasksHtml += `
                                <div class="report-item">
                                    <div class="report-meta">
                                        <strong>タスクID: ${task.task_id}</strong>
                                        <span class="report-status status-${task.status.toLowerCase()}">${task.status}</span>
                                    </div>
                                    <p><strong>作成時間:</strong> ${task.creation_date || 'N/A'}</p>
                                    <p><strong>完了時間:</strong> ${task.completion_date || 'N/A'}</p>
                                    <p><strong>Feedタイプ:</strong> ${task.feed_type}</p>
                                    ${downloadButton}
                                </div>
                            `;
                        });
                        
                        tasksHtml += '</div>';
                        recentReportsList.innerHTML = tasksHtml;
                    } else {
                        recentReportsList.innerHTML = `
                            <div class="status-message status-info">
                                <p>📭 タスクが見つかりません</p>
                            </div>
                        `;
                    }
                } else {
                    recentReportsList.innerHTML = `
                        <div class="status-message status-error">
                            <p>タスク取得失敗: ${data.error}</p>
                        </div>
                    `;
                }
            })
            .catch(error => {
                recentReportsList.innerHTML = `
                    <div class="status-message status-error">
                        <p>リクエスト失敗: ${error.message}</p>
                    </div>
                `;
            })
            .finally(() => {
                getRecentReportsBtn.disabled = false;
                getRecentReportsBtn.textContent = 'レポート取得';
            });
        });
    }
});

// 实时进度显示功能
function showProgressModal(taskId) {
    // 创建进度模态框
    const modal = document.createElement('div');
    modal.id = 'progressModal';
    modal.innerHTML = `
        <div class="modal-overlay">
            <div class="modal-content">
                <h3>CSV生成中</h3>
                <div class="progress-container">
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                    <div class="progress-text">
                        <span id="progressPercentage">0%</span>
                        <span id="progressMessage">処理中...</span>
                    </div>
                </div>
                <div class="progress-details">
                    <div>ステップ: <span id="currentStep">0</span>/<span id="totalSteps">5</span></div>
                    <div>項目: <span id="currentItem">0</span>/<span id="totalItems">0</span></div>
                    <div>経過時間: <span id="elapsedTime">0</span>秒</div>
                </div>
                <button id="closeProgress" style="display:none;" onclick="closeProgressModal()">閉じる</button>
            </div>
        </div>
    `;
    
    // 添加样式
    const style = document.createElement('style');
    style.textContent = `
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        .modal-content {
            background: white;
            padding: 20px;
            border-radius: 8px;
            min-width: 400px;
            text-align: center;
        }
        .progress-container {
            margin: 20px 0;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #f0f0f0;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 10px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4CAF50, #45a049);
            width: 0%;
            transition: width 0.3s ease;
        }
        .progress-text {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        .progress-details {
            text-align: left;
            background: #f9f9f9;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
        .progress-details div {
            margin: 5px 0;
        }
    `;
    
    document.head.appendChild(style);
    document.body.appendChild(modal);
    
    let downloadTriggered = false;
    let usePolling = false;
    let pollingInterval = null;
    
    // 更新进度显示的函数
    function updateProgress(data) {
        if (data.error) {
            document.getElementById('progressMessage').textContent = 'エラー: ' + data.error;
            document.getElementById('closeProgress').style.display = 'block';
            isGeneratingCSV = false;
            return;
        }
        
        // 更新进度显示
        const percentage = Math.round(data.progress_percentage || 0);
        document.getElementById('progressFill').style.width = percentage + '%';
        document.getElementById('progressPercentage').textContent = percentage + '%';
        document.getElementById('progressMessage').textContent = data.message || '処理中...';
        document.getElementById('currentStep').textContent = data.current_step || 0;
        document.getElementById('totalSteps').textContent = data.total_steps || 5;
        document.getElementById('currentItem').textContent = data.current_item || 0;
        document.getElementById('totalItems').textContent = data.total_items || 0;
        document.getElementById('elapsedTime').textContent = data.elapsed_time || 0;
        
        // 如果完成，触发下载
        if (data.status === 'completed' && !downloadTriggered) {
            downloadTriggered = true;
            document.getElementById('closeProgress').style.display = 'block';
            isGeneratingCSV = false;
            
            if (pollingInterval) {
                clearInterval(pollingInterval);
            }
            
            // 下载文件
            setTimeout(() => {
                fetch(`/generate-enhanced-csv/${taskId}`)
                .then(response => {
                    if (response.ok) {
                        return response.blob();
                    }
                    throw new Error('ダウンロード失敗');
                })
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = `ebay_revise_template_${taskId}_${new Date().toISOString().slice(0,19).replace(/[-:]/g, '').replace('T', '_')}.csv`;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    window.URL.revokeObjectURL(url);
                })
                .catch(error => {
                    console.error('ダウンロードエラー:', error);
                });
            }, 500);
        } else if (data.status === 'failed') {
            document.getElementById('closeProgress').style.display = 'block';
            isGeneratingCSV = false;
            if (pollingInterval) {
                clearInterval(pollingInterval);
            }
        }
    }
    
    // 轮询函数
    function pollProgress() {
        fetch(`/progress-poll/${taskId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateProgress(data.data);
            } else {
                updateProgress({error: data.error || '不明なエラー'});
            }
        })
        .catch(error => {
            console.error('轮询错误:', error);
            updateProgress({error: '接続エラー'});
        });
    }
    
    // 先尝试SSE连接
    const eventSource = new EventSource(`/progress/${taskId}`);
    
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        updateProgress(data);
    };
    
    eventSource.onerror = function(event) {
        console.error('SSE connection error:', event);
        eventSource.close();
        
        if (!usePolling) {
            console.log('SSE失败，切换到轮询模式');
            usePolling = true;
            // 切换到轮询模式
            pollingInterval = setInterval(pollProgress, 1000);
        }
    };
    
    // 延迟触发后端处理，确保连接已建立
    setTimeout(() => {
        fetch(`/generate-enhanced-csv/${taskId}`, {
            method: 'HEAD'  // 使用HEAD请求只触发处理，不等待响应
        }).catch(error => {
            console.log('Backend processing triggered');
        });
    }, 200);
}

function closeProgressModal() {
    const modal = document.getElementById('progressModal');
    if (modal) {
        modal.remove();
    }
}

// 生成增强CSV的函数，带实时进度显示
let isGeneratingCSV = false;

function generateEnhancedCSV(taskId) {
    if (isGeneratingCSV) {
        alert('CSV生成中です。しばらくお待ちください...');
        return false;
    }
    
    isGeneratingCSV = true;
    
    // 显示进度模态框
    showProgressModal(taskId);
    
    return false;
}