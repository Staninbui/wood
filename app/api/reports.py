"""
报告生成相关路由
"""
import logging
from datetime import datetime
from flask import Blueprint, request, session, jsonify, send_file
from app.services.ebay_service import EbayService
from app.services.csv_service import CSVService
from app.utils.decorators import login_required, handle_api_errors

logger = logging.getLogger(__name__)
reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/generate', methods=['POST'])
@login_required
@handle_api_errors
def generate_report():
    """生成新的库存报告"""
    token_info = session['ebay_token']
    access_token = token_info.get('access_token')
    
    if not access_token:
        return jsonify({'error': 'アクセストークンが無効です'}), 401
    
    ebay_service = EbayService()
    task_response = ebay_service.create_inventory_task(access_token)
    
    if task_response is None:
        # 如果API调用失败，返回演示数据
        demo_data = _get_demo_data()
        session['listings_data'] = demo_data
        
        return jsonify({
            'status': 'success',
            'message': 'レポートの生成が成功しました！（デモデータを使用）',
            'data': {
                'total_items': len(demo_data),
                'active_listings': len([item for item in demo_data if item['listing_status'] == 'Active']),
                'categories': list(set([item['category'] for item in demo_data])),
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'summary': f'{len(demo_data)}個の商品の詳細情報を正常に取得しました（デモデータ）'
            }
        }), 200
    
    task_id = task_response.get('taskId')
    if not task_id:
        return jsonify({'error': 'タスクIDを取得できません'}), 500
    
    # 保存任务ID到session
    session['inventory_task_id'] = task_id
    
    return jsonify({
        'status': 'task_created',
        'message': 'Inventoryレポートタスクが作成されました。後でステータスをご確認ください。',
        'task_id': task_id,
        'data': {
            'task_status': 'IN_PROGRESS',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': 'eBay商品在庫レポートを生成中です。タスクの完了をお待ちください。'
        }
    }), 202


@reports_bp.route('/status', methods=['GET'])
@login_required
@handle_api_errors
def check_report_status():
    """检查报告状态"""
    if 'inventory_task_id' not in session:
        return jsonify({'error': 'Inventory タスクIDが見つかりません'}), 400
    
    token_info = session['ebay_token']
    access_token = token_info.get('access_token')
    task_id = session['inventory_task_id']
    
    ebay_service = EbayService()
    status_response = ebay_service.get_inventory_task_status(access_token, task_id)
    
    if status_response is None:
        return jsonify({'error': 'タスクステータスを取得できません'}), 500
    
    task_status = status_response.get('status')
    
    if task_status == 'COMPLETED':
        # 任务完成，可以下载结果
        return jsonify({
            'status': 'success',
            'message': 'Inventoryレポートが完了しました！',
            'data': {
                'task_status': task_status,
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'summary': 'レポートの生成が完了しました。ダウンロードできます。'
            }
        }), 200
    elif task_status == 'FAILED':
        return jsonify({'error': f'Inventoryタスクが失敗しました: {status_response.get("message", "不明なエラー")}'}), 500
    else:
        # 任务仍在进行中
        return jsonify({
            'status': 'in_progress',
            'message': f'タスクステータス: {task_status}',
            'task_status': task_status
        }), 202


@reports_bp.route('/recent')
@login_required
@handle_api_errors
def get_recent_reports():
    """获取最近的报告列表"""
    token_info = session['ebay_token']
    access_token = token_info.get('access_token')
    
    if not access_token:
        return jsonify({'error': 'アクセストークンが無効です'}), 401
    
    days = request.args.get('days', 7, type=int)
    
    ebay_service = EbayService()
    recent_tasks = ebay_service.get_recent_inventory_tasks(access_token, days)
    
    if recent_tasks and 'tasks' in recent_tasks:
        tasks_list = []
        for task in recent_tasks['tasks']:
            task_info = {
                'task_id': task.get('taskId'),
                'status': task.get('status'),
                'creation_date': task.get('creationDate'),
                'completion_date': task.get('completionDate'),
                'feed_type': task.get('feedType')
            }
            tasks_list.append(task_info)
        
        return jsonify({
            'status': 'success',
            'tasks': tasks_list,
            'total_count': len(tasks_list)
        }), 200
    else:
        return jsonify({
            'status': 'success',
            'tasks': [],
            'total_count': 0,
            'message': f'最近{days}日間にタスクが見つかりませんでした'
        }), 200


@reports_bp.route('/export/csv')
@login_required
@handle_api_errors
def export_csv():
    """导出基础CSV"""
    if 'listings_data' not in session:
        return jsonify({'error': 'エクスポートするデータがありません。まずレポートを生成してください'}), 400
    
    csv_service = CSVService()
    output = csv_service.generate_basic_csv(session['listings_data'])
    
    filename = f"ebay_listings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )


@reports_bp.route('/export/excel')
@login_required
@handle_api_errors
def export_excel():
    """导出Excel文件"""
    if 'listings_data' not in session:
        return jsonify({'error': 'エクスポートするデータがありません。まずレポートを生成してください'}), 400
    
    csv_service = CSVService()
    output = csv_service.generate_excel(session['listings_data'])
    
    filename = f"ebay_listings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


def _get_demo_data():
    """获取演示数据"""
    return [
        {
            'sku': 'DEMO-001',
            'title': 'Sample Electronics Item',
            'category': 'Electronics',
            'price': 99.99,
            'quantity': 10,
            'condition': 'New',
            'listing_status': 'Active'
        },
        {
            'sku': 'DEMO-002', 
            'title': 'Sample Fashion Item',
            'category': 'Fashion',
            'price': 49.99,
            'quantity': 5,
            'condition': 'New',
            'listing_status': 'Active'
        }
    ]
