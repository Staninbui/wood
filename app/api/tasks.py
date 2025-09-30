"""
任务管理相关路由
"""
import os
import logging
import threading
from flask import Blueprint, request, session, jsonify, send_file, Response, current_app
from app.services.ebay_service import EbayService
from app.services.xml_service import XMLService
from app.services.csv_service import CSVService
from app.utils.decorators import login_required, handle_api_errors, validate_task_id
from app.utils.progress_manager import progress_manager, TaskStatus
import json
import time

logger = logging.getLogger(__name__)
tasks_bp = Blueprint('tasks', __name__)


@tasks_bp.route('/query', methods=['POST'])
@login_required
@handle_api_errors
def query_task_by_id():
    """通过任务ID查询任务状态"""
    data = request.get_json()
    task_id = data.get('task_id')
    
    if not task_id:
        return jsonify({'error': 'task_idを提供してください'}), 400
    
    token_info = session['ebay_token']
    access_token = token_info.get('access_token')
    
    if not access_token:
        return jsonify({'error': 'アクセストークンが無効です'}), 401
    
    ebay_service = EbayService()
    task_info = ebay_service.get_inventory_task_status(access_token, task_id)
    
    if task_info:
        return jsonify({
            'status': 'success',
            'task': {
                'task_id': task_info.get('taskId'),
                'status': task_info.get('status'),
                'creation_date': task_info.get('creationDate'),
                'completion_date': task_info.get('completionDate'),
                'feed_type': task_info.get('feedType'),
                'schema_version': task_info.get('schemaVersion'),
                'detail_href': task_info.get('detailHref')
            }
        }), 200
    else:
        return jsonify({'error': f'タスクID: {task_id} のタスクが見つかりません'}), 404


@tasks_bp.route('/download/<task_id>')
@login_required
@handle_api_errors
@validate_task_id
def download_task_result(task_id):
    """下载任务结果文件"""
    token_info = session['ebay_token']
    access_token = token_info.get('access_token')
    
    if not access_token:
        return jsonify({'error': 'アクセストークンが無効です'}), 401
    
    ebay_service = EbayService()
    file_content = ebay_service.download_task_result(access_token, task_id)
    
    if file_content is None:
        return jsonify({'error': 'ファイルのダウンロードに失敗しました'}), 500
    
    # 生成文件名
    filename = f"ebay_inventory_report_{task_id}.zip"
    
    from flask import make_response
    response = make_response(file_content)
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@tasks_bp.route('/enhanced-csv/<task_id>', methods=['GET', 'HEAD'])
@login_required
@handle_api_errors
@validate_task_id
def generate_enhanced_csv(task_id):
    """生成增强CSV文件"""
    if request.method == 'HEAD':
        # HEAD请求：启动处理但不等待完成
        existing_progress = progress_manager.get_progress(task_id)
        if existing_progress and existing_progress.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            return '', 202  # 已在处理中
        
        token_info = session.get('ebay_token')
        if not token_info:
            return jsonify({'error': 'ログインしていません'}), 401
        
        # 立即创建进度跟踪
        progress_manager.start_task(task_id)
        
        # 获取当前应用实例和配置
        app = current_app._get_current_object()
        config = current_app.config.copy()
        
        # 启动异步处理
        def async_process():
            try:
                with app.app_context():
                    _process_enhanced_csv_async(task_id, token_info, config)
            except Exception as e:
                logger.error(f"异步处理错误: {e}")
                with app.app_context():
                    progress_manager.complete_task(task_id, success=False, message=f'エラー: {str(e)}')
        
        thread = threading.Thread(target=async_process)
        thread.daemon = True
        thread.start()
        
        return '', 202  # 处理已启动
    
    # GET请求：检查是否已完成并返回文件
    progress = progress_manager.get_progress(task_id)
    if progress and progress.status == TaskStatus.COMPLETED:
        csv_service = CSVService(current_app.config)
        temp_file_path = csv_service.get_temp_file_path(task_id)
        
        if temp_file_path and os.path.exists(temp_file_path):
            filename = csv_service.generate_filename(task_id, 'csv')
            return send_file(
                temp_file_path,
                mimetype='text/csv',
                as_attachment=True,
                download_name=filename
            )
    
    return jsonify({'error': 'ファイルが見つかりません'}), 404


@tasks_bp.route('/progress/<task_id>')
@login_required
def progress_stream(task_id):
    """Server-Sent Events进度推送"""
    def generate():
        try:
            # 发送初始连接确认
            yield f"data: {json.dumps({'status': 'connected', 'task_id': task_id})}\n\n"
            
            # 最多等待60秒
            max_iterations = 60
            iteration = 0
            
            while iteration < max_iterations:
                progress = progress_manager.get_progress(task_id)
                if progress:
                    data = {
                        'task_id': progress.task_id,
                        'status': progress.status.value,
                        'current_step': progress.current_step,
                        'total_steps': progress.total_steps,
                        'current_item': progress.current_item,
                        'total_items': progress.total_items,
                        'progress_percentage': progress.progress_percentage,
                        'message': progress.message,
                        'elapsed_time': round(progress.elapsed_time, 1)
                    }
                    
                    yield f"data: {json.dumps(data)}\n\n"
                    
                    # 如果任务完成或失败，结束推送
                    if progress.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                        break
                else:
                    # 任务不存在，但给一些时间让任务启动
                    if iteration > 5:  # 5秒后还没有任务就报错
                        yield f"data: {json.dumps({'error': 'Task not found'})}\n\n"
                        break
                
                time.sleep(1)  # 每秒推送一次
                iteration += 1
                
        except GeneratorExit:
            # 客户端断开连接
            pass
        except Exception as e:
            logger.error(f"SSE推送错误: {e}")
            yield f"data: {json.dumps({'error': f'SSE error: {str(e)}'})}\n\n"
    
    response = Response(generate(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Cache-Control'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['X-Accel-Buffering'] = 'no'  # 禁用nginx缓冲
    response.headers['Content-Type'] = 'text/event-stream; charset=utf-8'
    return response


@tasks_bp.route('/progress-poll/<task_id>')
@login_required
@validate_task_id
def progress_poll(task_id):
    """轮询方式获取任务进度状态"""
    progress = progress_manager.get_progress(task_id)
    if progress:
        return jsonify({
            'status': 'success',
            'data': {
                'task_id': progress.task_id,
                'status': progress.status.value,
                'current_step': progress.current_step,
                'total_steps': progress.total_steps,
                'current_item': progress.current_item,
                'total_items': progress.total_items,
                'progress_percentage': progress.progress_percentage,
                'message': progress.message,
                'elapsed_time': round(progress.elapsed_time, 1)
            }
        }), 200
    else:
        return jsonify({'error': 'Task not found'}), 404


def _process_enhanced_csv_async(task_id, token_info, config):
    """异步CSV生成处理逻辑"""
    # 注意：此函数必须在Flask应用上下文中调用
    access_token = token_info.get('access_token')
    
    if not access_token:
        progress_manager.complete_task(task_id, success=False, message='アクセストークンが無効です')
        return
    
    logger.info(f"开始生成增强CSV报告，任务ID: {task_id}")
    
    try:
        # 1. 下载ZIP文件
        progress_manager.update_progress(task_id, TaskStatus.DOWNLOADING, current_step=1, message='ZIPファイルをダウンロード中...')
        
        ebay_service = EbayService(config)
        zip_content = ebay_service.download_task_result(access_token, task_id)
        
        if not zip_content:
            progress_manager.complete_task(task_id, success=False, message='レポートのダウンロードに失敗しました')
            return
        
        # 2. 提取ItemID列表
        progress_manager.update_progress(task_id, TaskStatus.EXTRACTING, current_step=2, message='ItemIDを抽出中...')
        
        xml_service = XMLService(config)
        item_ids = xml_service.extract_item_ids_from_zip(zip_content)
        
        if not item_ids:
            progress_manager.complete_task(task_id, success=False, message='ZIPファイルからItemIDを抽出できませんでした')
            return
        
        logger.info(f"提取到 {len(item_ids)} 个ItemID")
        progress_manager.update_progress(task_id, TaskStatus.PROCESSING, current_step=3, total_items=len(item_ids), message=f'{len(item_ids)}個のアイテム詳細を取得中...')
        
        # 3. 批量获取商品详情
        def progress_callback(completed, total):
            progress_manager.update_progress(
                task_id, 
                TaskStatus.PROCESSING, 
                current_item=completed,
                message=f'アイテム詳細取得中... ({completed}/{total})'
            )
        
        enhanced_data = xml_service.get_item_details_batch(item_ids, access_token, task_id, progress_callback)
        
        if not enhanced_data:
            progress_manager.complete_task(task_id, success=False, message='商品の詳細情報を取得できませんでした')
            return
        
        # 4. 生成CSV文件
        progress_manager.update_progress(task_id, TaskStatus.GENERATING, current_step=4, message='CSVファイルを生成中...')
        
        csv_service = CSVService(config)
        temp_file_path = csv_service.generate_enhanced_csv(enhanced_data, task_id)
        
        if not temp_file_path:
            progress_manager.complete_task(task_id, success=False, message='CSVファイルの生成に失敗しました')
            return
        
        logger.info(f"增强CSV生成完成，成功处理 {len(enhanced_data)} 条记录")
        progress_manager.complete_task(task_id, success=True, message=f'CSV生成完了 - {len(enhanced_data)}件のUSアイテムが処理されました')
        
    except Exception as e:
        logger.error(f"增强CSV生成过程中出错: {e}")
        progress_manager.complete_task(task_id, success=False, message=f'処理中にエラーが発生しました: {str(e)}')
