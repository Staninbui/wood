document.addEventListener('DOMContentLoaded', function() {
    const generateBtn = document.getElementById('generate-report-btn');
    const checkStatusBtn = document.getElementById('check-status-btn');
    const statusDiv = document.getElementById('report-status');
    
    if (generateBtn) {
        generateBtn.addEventListener('click', function() {
            // 显示加载状态
            statusDiv.innerHTML = '<p>正在创建 Feed 任务...</p>';
            generateBtn.disabled = true;
            generateBtn.textContent = '创建中...';
            
            // 发送请求到后端
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
                            <p><strong>商品总数:</strong> ${data.data.total_items}</p>
                            <p><strong>活跃商品:</strong> ${data.data.active_listings}</p>
                            <p><strong>类别:</strong> ${data.data.categories.join(', ')}</p>
                            <p><strong>生成时间:</strong> ${data.data.generated_at}</p>
                            <p><strong>摘要:</strong> ${data.data.summary}</p>
                        </div>
                    `;
                    
                    // 显示导出按钮
                    const exportSection = document.getElementById('export-section');
                    if (exportSection) {
                        exportSection.style.display = 'block';
                    }
                } else if (data.status === 'task_created') {
                    statusDiv.innerHTML = `
                        <div style="background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 10px; border-radius: 5px; margin-top: 10px;">
                            <h4>${data.message}</h4>
                            <p><strong>任务 ID:</strong> ${data.task_id}</p>
                            <p><strong>任务状态:</strong> ${data.data.task_status}</p>
                            <p><strong>创建时间:</strong> ${data.data.generated_at}</p>
                            <p><strong>说明:</strong> ${data.data.summary}</p>
                            <p><em>请点击 "Check Feed Status" 按钮查看任务进度</em></p>
                        </div>
                    `;
                    
                    // 显示状态检查按钮
                    if (checkStatusBtn) {
                        checkStatusBtn.style.display = 'inline-block';
                    }
                } else {
                    statusDiv.innerHTML = `
                        <div style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 10px; border-radius: 5px; margin-top: 10px;">
                            <p>错误: ${data.error}</p>
                        </div>
                    `;
                }
            })
            .catch(error => {
                statusDiv.innerHTML = `
                    <div style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 10px; border-radius: 5px; margin-top: 10px;">
                        <p>请求失败: ${error.message}</p>
                    </div>
                `;
            })
            .finally(() => {
                // 恢复按钮状态
                generateBtn.disabled = false;
                generateBtn.textContent = 'Generate Item Specifics Report';
            });
        });
    }
    
    if (checkStatusBtn) {
        checkStatusBtn.addEventListener('click', function() {
            // 显示检查状态
            statusDiv.innerHTML = '<p>正在检查 Feed 任务状态...</p>';
            checkStatusBtn.disabled = true;
            checkStatusBtn.textContent = '检查中...';
            
            // 发送请求检查状态
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
                            <p><strong>商品总数:</strong> ${data.data.total_items}</p>
                            <p><strong>活跃商品:</strong> ${data.data.active_listings}</p>
                            <p><strong>类别:</strong> ${data.data.categories.join(', ')}</p>
                            <p><strong>完成时间:</strong> ${data.data.generated_at}</p>
                            <p><strong>摘要:</strong> ${data.data.summary}</p>
                        </div>
                    `;
                    
                    // 显示导出按钮
                    const exportSection = document.getElementById('export-section');
                    if (exportSection) {
                        exportSection.style.display = 'block';
                    }
                    
                    // 隐藏状态检查按钮
                    checkStatusBtn.style.display = 'none';
                } else if (data.status === 'in_progress') {
                    statusDiv.innerHTML = `
                        <div style="background: #cce5ff; border: 1px solid #99ccff; color: #004085; padding: 10px; border-radius: 5px; margin-top: 10px;">
                            <h4>${data.message}</h4>
                            <p><strong>当前状态:</strong> ${data.task_status}</p>
                            <p><em>任务仍在进行中，请稍后再次检查</em></p>
                        </div>
                    `;
                } else {
                    statusDiv.innerHTML = `
                        <div style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 10px; border-radius: 5px; margin-top: 10px;">
                            <p>错误: ${data.error}</p>
                        </div>
                    `;
                }
            })
            .catch(error => {
                statusDiv.innerHTML = `
                    <div style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 10px; border-radius: 5px; margin-top: 10px;">
                        <p>请求失败: ${error.message}</p>
                    </div>
                `;
            })
            .finally(() => {
                // 恢复按钮状态
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
                        <p>请输入任务ID</p>
                    </div>
                `;
                return;
            }
            
            taskQueryResult.innerHTML = '<p>正在查询任务状态...</p>';
            queryTaskBtn.disabled = true;
            queryTaskBtn.textContent = '查询中...';
            
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
                        `<div style="margin-top: 10px;">
                            <a href="/download-task-result/${task.task_id}" 
                               style="padding: 8px 16px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; display: inline-block; margin-right: 10px;"
                               class="download-btn">
                               下载结果文件
                            </a>
                            <button onclick="generateEnhancedCSV('${task.task_id}')" 
                               style="padding: 8px 16px; background-color: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;"
                               class="enhanced-csv-btn" id="enhanced-csv-${task.task_id}">
                               生成增强CSV (含Item Specifics)
                            </button>
                         </div>` : '';
                    
                    taskQueryResult.innerHTML = `
                        <div style="background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 10px; border-radius: 5px;">
                            <h4>任务详情</h4>
                            <p><strong>任务ID:</strong> ${task.task_id}</p>
                            <p><strong>状态:</strong> ${task.status}</p>
                            <p><strong>创建时间:</strong> ${task.creation_date || 'N/A'}</p>
                            <p><strong>完成时间:</strong> ${task.completion_date || 'N/A'}</p>
                            <p><strong>Feed类型:</strong> ${task.feed_type}</p>
                            ${task.schema_version ? `<p><strong>Schema版本:</strong> ${task.schema_version}</p>` : ''}
                            ${downloadButton}
                        </div>
                    `;
                } else {
                    taskQueryResult.innerHTML = `
                        <div style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 10px; border-radius: 5px;">
                            <p>错误: ${data.error}</p>
                        </div>
                    `;
                }
            })
            .catch(error => {
                taskQueryResult.innerHTML = `
                    <div style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 10px; border-radius: 5px;">
                        <p>请求失败: ${error.message}</p>
                    </div>
                `;
            })
            .finally(() => {
                queryTaskBtn.disabled = false;
                queryTaskBtn.textContent = '查询任务状态';
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
            
            recentReportsList.innerHTML = '<p>正在获取最近的报告...</p>';
            getRecentReportsBtn.disabled = true;
            getRecentReportsBtn.textContent = '获取中...';
            
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
                            <div style="background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 10px; border-radius: 5px;">
                                <h4>找到 ${data.total_count} 个任务</h4>
                                <div style="max-height: 300px; overflow-y: auto;">
                        `;
                        
                        data.tasks.forEach(task => {
                            const statusColor = task.status === 'COMPLETED' ? '#28a745' : 
                                              task.status === 'FAILED' ? '#dc3545' : '#ffc107';
                            
                            const downloadButton = task.status === 'COMPLETED' ? 
                                `<div style="margin-top: 8px;">
                                    <a href="/download-task-result/${task.task_id}" 
                                       style="padding: 6px 12px; background-color: #007bff; color: white; text-decoration: none; border-radius: 3px; font-size: 12px; margin-right: 8px;"
                                       class="download-btn">
                                       下载结果文件
                                    </a>
                                    <button onclick="generateEnhancedCSV('${task.task_id}')" 
                                       style="padding: 6px 12px; background-color: #28a745; color: white; border: none; border-radius: 3px; font-size: 12px; cursor: pointer;"
                                       class="enhanced-csv-btn" id="enhanced-csv-list-${task.task_id}">
                                       增强CSV
                                    </button>
                                 </div>` : '';
                            
                            tasksHtml += `
                                <div style="border: 1px solid #ddd; margin: 5px 0; padding: 10px; border-radius: 3px; background: white;">
                                    <p><strong>任务ID:</strong> ${task.task_id}</p>
                                    <p><strong>状态:</strong> <span style="color: ${statusColor}; font-weight: bold;">${task.status}</span></p>
                                    <p><strong>创建时间:</strong> ${task.creation_date || 'N/A'}</p>
                                    <p><strong>完成时间:</strong> ${task.completion_date || 'N/A'}</p>
                                    <p><strong>Feed类型:</strong> ${task.feed_type}</p>
                                    ${downloadButton}
                                </div>
                            `;
                        });
                        
                        tasksHtml += '</div></div>';
                        recentReportsList.innerHTML = tasksHtml;
                    } else {
                        recentReportsList.innerHTML = `
                            <div style="background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 10px; border-radius: 5px;">
                                <p>${data.message || `最近 ${days} 天内没有找到任务`}</p>
                            </div>
                        `;
                    }
                } else {
                    recentReportsList.innerHTML = `
                        <div style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 10px; border-radius: 5px;">
                            <p>错误: ${data.error}</p>
                        </div>
                    `;
                }
            })
            .catch(error => {
                recentReportsList.innerHTML = `
                    <div style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 10px; border-radius: 5px;">
                        <p>请求失败: ${error.message}</p>
                    </div>
                `;
            })
            .finally(() => {
                getRecentReportsBtn.disabled = false;
                getRecentReportsBtn.textContent = '获取最近报告';
            });
        });
    }
});

// 生成增强CSV的函数，带加载动画和防抖
let isGeneratingCSV = false;

function generateEnhancedCSV(taskId) {
    if (isGeneratingCSV) {
        alert('正在生成CSV，请稍候...');
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
            console.error('下载失败:', error);
            alert('下载失败，请重试');
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
                targetBtn.innerHTML = '生成增强CSV (含Item Specifics)';
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