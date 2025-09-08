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
                                    <p>タスクIDをコピーして、タスク検索ボックスに貼り付けてください</p>
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
                <div id="loadingState" class="loading-container">
                    <div class="hourglass">
                        <div class="hourglass-top"></div>
                        <div class="hourglass-bottom"></div>
                        <div class="sand"></div>
                    </div>
                    <p>タスクを準備中...</p>
                </div>
                <div id="progressState" class="progress-container" style="display:none;">
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                    <div class="progress-text">
                        <span id="progressPercentage">0%</span>
                        <span id="progressMessage">処理中...</span>
                    </div>
                    <div class="progress-details">
                        <div>ステップ: <span id="currentStep">0</span>/<span id="totalSteps">5</span></div>
                        <div>出品数: <span id="currentItem">0</span>/<span id="totalItems">0</span></div>
                        <div>経過時間: <span id="elapsedTime">0</span>秒</div>
                    </div>
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
        .loading-container {
            margin: 30px 0;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .hourglass {
            position: relative;
            width: 40px;
            height: 60px;
            margin-bottom: 15px;
        }
        .hourglass-top, .hourglass-bottom {
            position: absolute;
            width: 40px;
            height: 25px;
            border: 3px solid #4CAF50;
        }
        .hourglass-top {
            top: 0;
            border-bottom: none;
            border-radius: 20px 20px 0 0;
            background: linear-gradient(to bottom, #FFD700 0%, #FFD700 60%, transparent 60%);
            animation: sandFlow 2s ease-in-out infinite;
        }
        .hourglass-bottom {
            bottom: 0;
            border-top: none;
            border-radius: 0 0 20px 20px;
            background: linear-gradient(to top, #FFD700 0%, #FFD700 40%, transparent 40%);
        }
        .sand {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translateX(-50%);
            width: 2px;
            height: 10px;
            background: #FFD700;
            animation: sandDrop 2s ease-in-out infinite;
        }
        @keyframes sandFlow {
            0% { background: linear-gradient(to bottom, #FFD700 0%, #FFD700 60%, transparent 60%); }
            50% { background: linear-gradient(to bottom, #FFD700 0%, #FFD700 30%, transparent 30%); }
            100% { background: linear-gradient(to bottom, #FFD700 0%, #FFD700 60%, transparent 60%); }
        }
        @keyframes sandDrop {
            0%, 100% { opacity: 0; }
            50% { opacity: 1; }
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
    let taskStarted = false;
    let pollAttempts = 0;
    const maxPollAttempts = 30; // 最多轮询30次（30秒）
    
    // 轮询函数
    function pollProgress() {
        pollAttempts++;
        
        fetch(`/progress-poll/${taskId}`)
        .then(response => {
            // 检查401认证错误
            if (response.status === 401) {
                console.error('认证失败，停止轮询');
                if (pollingInterval) {
                    clearInterval(pollingInterval);
                    pollingInterval = null;
                }
                updateProgress({error: '認証エラー。再度ログインしてください。'});
                return Promise.reject('Authentication failed');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                // 任务已开始，切换到进度显示
                if (!taskStarted) {
                    taskStarted = true;
                    switchToProgressView();
                }
                updateProgress(data.data);
            } else {
                // 如果轮询次数超过限制，显示错误
                if (pollAttempts >= maxPollAttempts) {
                    updateProgress({error: 'タスクの開始がタイムアウトしました'});
                }
                // 否则继续等待，不显示错误
                console.warn(`轮询获取进度失败 (${pollAttempts}/${maxPollAttempts}):`, data.error);
            }
        })
        .catch(error => {
            console.error('轮询错误:', error);
            if (error === 'Authentication failed') {
                return; // 认证失败时不继续处理
            }
            // 检查是否是网络错误或404
            if (error.message && error.message.includes('404')) {
                console.log('任务不存在，停止轮询');
                if (pollingInterval) {
                    clearInterval(pollingInterval);
                    pollingInterval = null;
                }
                updateProgress({error: 'タスクが見つかりません。ページを更新してください。'});
                return;
            }
            if (pollAttempts >= maxPollAttempts) {
                updateProgress({error: '接続エラー'});
            }
        });
    }
    
    // 切换到进度显示视图
    function switchToProgressView() {
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('progressState').style.display = 'block';
    }
    
    // 在Cloud Run环境下，优先使用轮询而不是SSE
    const isCloudRun = window.location.hostname.includes('run.app') || window.location.hostname.includes('.a.run.app');
    
    if (isCloudRun) {
        console.log('检测到Cloud Run环境，使用轮询模式');
        usePolling = true;
        // 延迟启动轮询，给任务时间启动
        setTimeout(() => {
            if (!downloadTriggered && usePolling) {
                pollingInterval = setInterval(pollProgress, 3000);
            }
        }, 2000);
    } else {
        // 本地环境尝试SSE连接
        const eventSource = new EventSource(`/progress/${taskId}`);
        let sseConnected = false;
    
    eventSource.onopen = function(event) {
        console.log('SSE连接已建立');
        sseConnected = true;
    };
    
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        // SSE有数据，切换到进度显示
        if (!taskStarted) {
            taskStarted = true;
            switchToProgressView();
        }
        
        updateProgress(data);
        
        // 如果SSE正常工作，确保不启动轮询
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
            usePolling = false;
        }
    };
    
    eventSource.onerror = function(event) {
        console.error('SSE connection error:', event);
        eventSource.close();
        
        // 检查是否是404错误（任务不存在）
        if (event.target.readyState === EventSource.CLOSED) {
            console.log('SSE连接被关闭，可能是任务不存在或已完成');
            // 先检查任务状态
            fetch(`/progress-poll/${taskId}`)
            .then(response => {
                if (response.status === 404) {
                    console.log('任务不存在，关闭进度模态框');
                    updateProgress({error: 'タスクが見つかりません。ページを更新してください。'});
                    return;
                }
                return response.json();
            })
            .then(data => {
                if (data && data.status === 'success') {
                    // 任务存在但SSE失败，切换到轮询
                    if (!usePolling) {
                        console.log('SSE失败，切换到轮询模式');
                        usePolling = true;
                        setTimeout(() => {
                            if (!downloadTriggered && usePolling) {
                                pollingInterval = setInterval(pollProgress, 3000);
                            }
                        }, 2000);
                    }
                }
            })
            .catch(error => {
                console.error('检查任务状态失败:', error);
                updateProgress({error: 'タスクの状態を確認できません。ページを更新してください。'});
            });
        } else if (!usePolling) {
            console.log('SSE失败，切换到轮询模式');
            usePolling = true;
            setTimeout(() => {
                if (!downloadTriggered && usePolling) {
                    pollingInterval = setInterval(pollProgress, 3000);
                }
            }, 2000);
        }
    };
    
    // 延迟触发后端处理，确保连接已建立
    setTimeout(() => {
        fetch(`/generate-enhanced-csv/${taskId}`, {
            method: 'HEAD'  // 使用HEAD请求只触发处理，不等待响应
        }).then(response => {
            if (response.status === 404) {
                console.error('任务不存在，无法触发处理');
                updateProgress({error: 'タスクが見つかりません。ページを更新してください。'});
                return;
            }
            console.log('Backend processing triggered, status:', response.status);
        }).catch(error => {
            console.log('Backend processing triggered with error:', error);
            // 如果是网络错误，可能是任务不存在
            updateProgress({error: 'タスクの処理を開始できません。ページを更新してください。'});
        });
    }, 200);
    
    // 备用轮询启动机制：如果3秒后还没有SSE连接，启动轮询
    setTimeout(() => {
        if (!sseConnected && !usePolling && !downloadTriggered) {
            console.log('SSE连接超时，启动备用轮询');
            usePolling = true;
            pollingInterval = setInterval(pollProgress, 3000);
        }
    }, 3000);
    }
    
    // 延迟触发后端处理，确保连接已建立
    setTimeout(() => {
        fetch(`/generate-enhanced-csv/${taskId}`, {
            method: 'HEAD'  // 使用HEAD请求只触发处理，不等待响应
        }).then(response => {
            if (response.status === 404) {
                console.error('任务不存在，无法触发处理');
                updateProgress({error: 'タスクが見つかりません。ページを更新してください。'});
                return;
            }
            console.log('Backend processing triggered, status:', response.status);
        }).catch(error => {
            console.log('Backend processing triggered with error:', error);
            // 如果是网络错误，可能是任务不存在
            updateProgress({error: 'タスクの処理を開始できません。ページを更新してください。'});
        });
    }, 200);
    
    // 更新进度显示的函数
    function updateProgress(data) {
        // 检查模态框是否还存在
        if (!document.getElementById('progressModal')) {
            console.log('Progress modal not found, stopping updates');
            if (pollingInterval) {
                clearInterval(pollingInterval);
            }
            return;
        }
        
        if (data.error) {
            // 确保切换到进度视图以显示错误
            if (!taskStarted) {
                switchToProgressView();
            }
            
            const messageEl = document.getElementById('progressMessage');
            const closeEl = document.getElementById('closeProgress');
            if (messageEl) messageEl.textContent = 'エラー: ' + data.error;
            if (closeEl) closeEl.style.display = 'block';
            isGeneratingCSV = false;
            return;
        }
        
        // 添加调试信息
        console.log('Progress update:', data);
        
        // 确保已切换到进度视图
        if (!taskStarted) {
            taskStarted = true;
            switchToProgressView();
        }
        
        // 安全地更新进度显示
        const percentage = Math.round(data.progress_percentage || 0);
        const fillEl = document.getElementById('progressFill');
        const percentageEl = document.getElementById('progressPercentage');
        const messageEl = document.getElementById('progressMessage');
        const stepEl = document.getElementById('currentStep');
        const totalStepsEl = document.getElementById('totalSteps');
        const itemEl = document.getElementById('currentItem');
        const totalItemsEl = document.getElementById('totalItems');
        const timeEl = document.getElementById('elapsedTime');
        
        if (fillEl) fillEl.style.width = percentage + '%';
        if (percentageEl) percentageEl.textContent = percentage + '%';
        if (messageEl) messageEl.textContent = data.message || '処理中...';
        if (stepEl) stepEl.textContent = data.current_step || 0;
        if (totalStepsEl) totalStepsEl.textContent = data.total_steps || 5;
        if (itemEl) itemEl.textContent = data.current_item || 0;
        if (totalItemsEl) totalItemsEl.textContent = data.total_items || 0;
        if (timeEl) timeEl.textContent = data.elapsed_time || 0;
        
        // 如果完成，触发下载 - 检查多种完成状态
        if ((data.status === 'completed' || percentage >= 100) && !downloadTriggered) {
            console.log('任务完成，准备下载文件');
            downloadTriggered = true;
            
            // 停止所有轮询和SSE连接
            if (pollingInterval) {
                clearInterval(pollingInterval);
                pollingInterval = null;
            }
            
            const closeEl = document.getElementById('closeProgress');
            if (closeEl) closeEl.style.display = 'block';
            isGeneratingCSV = false;
            
            // 单次下载，避免重复 - 添加3秒延迟
            console.log('等待3秒后开始下载文件...');
            setTimeout(() => {
                console.log('开始下载文件...');
                fetch(`/generate-enhanced-csv/${taskId}`)
            .then(response => {
                console.log('下载响应状态:', response.status);
                if (response.ok) {
                    return response.blob();
                } else {
                    throw new Error(`下载失败: HTTP ${response.status}`);
                }
            })
            .then(blob => {
                console.log('文件blob大小:', blob.size);
                if (blob.size > 0) {
                    const url = window.URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = `ebay_revise_template_${taskId}_${new Date().toISOString().slice(0,19).replace(/[-:]/g, '').replace('T', '_')}.csv`;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    window.URL.revokeObjectURL(url);
                    console.log('文件下载完成');
                } else {
                    throw new Error('下载的文件为空');
                }
            })
            .catch(error => {
                console.error('ダウンロードエラー:', error);
                if (messageEl) {
                    messageEl.textContent = 'ダウンロードエラー: ' + error.message;
                }
            });
            }, 3000); // 3秒延迟
        } else if (data.status === 'failed') {
            const closeEl = document.getElementById('closeProgress');
            if (closeEl) closeEl.style.display = 'block';
            isGeneratingCSV = false;
            if (pollingInterval) {
                clearInterval(pollingInterval);
                pollingInterval = null;
            }
        }
    }
}

function closeProgressModal() {
    const modal = document.getElementById('progressModal');
    if (modal) {
        modal.remove();
    }
    // 重置全局状态
    isGeneratingCSV = false;
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