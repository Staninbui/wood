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

// 生成增强CSV的函数，带加载动画和防抖
let isGeneratingCSV = false;

function generateEnhancedCSV(taskId) {
    if (isGeneratingCSV) {
        alert('CSV生成中です。しばらくお待ちください...');
        return;
    }
    
    isGeneratingCSV = true;
    
    // 禁用所有按钮
    const allButtons = document.querySelectorAll('button, .download-btn, .enhanced-csv-btn');
    allButtons.forEach(btn => {
        btn.style.opacity = '0.6';
        btn.style.pointerEvents = 'none';
        if (btn.tagName === 'BUTTON') {
            btn.disabled = true;
        }
    });
    
    // 更新按钮文本显示加载状态
    const targetBtn = document.getElementById(`enhanced-csv-${taskId}`) || 
                     document.getElementById(`enhanced-csv-list-${taskId}`);
    if (targetBtn) {
        targetBtn.innerHTML = '生成中... <span style="animation: spin 1s linear infinite;">⟳</span>';
    }
    
    // 使用fetch API来处理下载
    fetch(`/generate-enhanced-csv/${taskId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.blob();
        })
        .then(blob => {
            // 创建下载链接
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `ebay_revise_template_${taskId}_${new Date().toISOString().slice(0,19).replace(/[-:]/g, '').replace('T', '_')}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        })
        .catch(error => {
            console.error('ダウンロード失敗:', error);
            alert('ダウンロード失敗しました。再試行してください');
        })
        .finally(() => {
            isGeneratingCSV = false;
            
            // 恢复所有按钮
            allButtons.forEach(btn => {
                btn.style.opacity = '1';
                btn.style.pointerEvents = 'auto';
                if (btn.tagName === 'BUTTON') {
                    btn.disabled = false;
                }
            });
            
            // 恢复按钮文本
            if (targetBtn) {
                targetBtn.innerHTML = '📊 拡張CSV生成';
            }
        });
}

// 添加CSS动画
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);