# 员工管理相关的API路由
# 这个文件包含所有与员工管理相关的API端点，包括员工映射、统计等功能
# 更新为使用统一的数据管理器

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
from sqlalchemy import func, and_
import logging
from db import db

# 导入统一数据管理器
from data_manager import data_manager

# 创建员工管理蓝图
employees_bp = Blueprint('employees', __name__, url_prefix='/api/v1/employees')

# 配置日志
logger = logging.getLogger(__name__)

@employees_bp.route('/', methods=['GET'])
def get_employees():
    """
    获取所有员工映射列表
    返回: 员工映射数据列表
    """
    try:
        from models import EmployeeMapping
        
        employees = EmployeeMapping.query.all()
        employee_list = []
        
        for emp in employees:
            employee_list.append({
                'id': emp.id,
                'wechat_nickname': emp.wechat_nickname,
                'real_name': emp.real_name,
                'position': emp.position,
                'name_abbreviation': emp.name_abbreviation,
                'role': emp.role,
                'created_at': emp.created_at.isoformat() if emp.created_at else None,
                'updated_at': emp.updated_at.isoformat() if emp.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'data': employee_list
        })
    except Exception as e:
        logger.error(f"获取员工列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@employees_bp.route('/', methods=['POST'])
def create_employee():
    """
    创建新的员工映射
    请求体: JSON格式，包含员工信息
    返回: 创建结果
    """
    try:
        from models import EmployeeMapping
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '缺少请求数据'}), 400
        
        # 验证必填字段
        required_fields = ['wechat_nickname', 'real_name', 'position', 'name_abbreviation']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'error': f'缺少必填字段: {field}'}), 400
        
        # 检查是否已存在相同的微信昵称
        existing_employee = EmployeeMapping.query.filter_by(
            wechat_nickname=data['wechat_nickname']
        ).first()
        
        if existing_employee:
            return jsonify({'success': False, 'error': '该微信昵称已存在'}), 400
        
        # 创建新员工映射
        new_employee = EmployeeMapping(
            wechat_nickname=data['wechat_nickname'],
            real_name=data['real_name'],
            position=data['position'],
            name_abbreviation=data['name_abbreviation'],
            role=data.get('role', '员工'),
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_employee)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': new_employee.id,
                'wechat_nickname': new_employee.wechat_nickname,
                'real_name': new_employee.real_name,
                'position': new_employee.position,
                'name_abbreviation': new_employee.name_abbreviation,
                'role': new_employee.role,
                'created_at': new_employee.created_at.isoformat()
            },
            'message': '员工映射创建成功'
        })
    except Exception as e:
        logger.error(f"创建员工映射失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@employees_bp.route('/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    """
    更新员工映射信息
    参数: employee_id - 员工ID
    请求体: JSON格式，包含要更新的字段
    返回: 更新结果
    """
    try:
        from models import EmployeeMapping
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '缺少请求数据'}), 400
        
        employee = EmployeeMapping.query.get(employee_id)
        if not employee:
            return jsonify({'success': False, 'error': '员工不存在'}), 404
        
        # 更新字段
        if 'wechat_nickname' in data:
            employee.wechat_nickname = data['wechat_nickname']
        if 'real_name' in data:
            employee.real_name = data['real_name']
        if 'position' in data:
            employee.position = data['position']
        if 'name_abbreviation' in data:
            employee.name_abbreviation = data['name_abbreviation']
        if 'role' in data:
            employee.role = data['role']
        
        employee.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': employee.id,
                'wechat_nickname': employee.wechat_nickname,
                'real_name': employee.real_name,
                'position': employee.position,
                'name_abbreviation': employee.name_abbreviation,
                'role': employee.role,
                'created_at': employee.created_at.isoformat() if employee.created_at else None,
                'updated_at': employee.updated_at.isoformat()
            },
            'message': '员工映射更新成功'
        })
    except Exception as e:
        logger.error(f"更新员工映射失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@employees_bp.route('/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    """
    删除员工映射
    参数: employee_id - 员工ID
    返回: 删除结果
    """
    try:
        from models import EmployeeMapping
        
        employee = EmployeeMapping.query.get(employee_id)
        if not employee:
            return jsonify({'success': False, 'error': '员工不存在'}), 404
        
        db.session.delete(employee)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '员工映射删除成功'
        })
    except Exception as e:
        logger.error(f"删除员工映射失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@employees_bp.route('/<int:employee_id>/stats', methods=['GET'])
def get_employee_stats(employee_id):
    """
    获取员工工作统计
    参数: employee_id - 员工ID
    查询参数: start_date, end_date (可选)
    返回: 员工统计数据
    """
    try:
        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 使用统一数据管理器获取员工统计
        result = data_manager.get_employee_stats(employee_id, start_date, end_date)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"获取员工统计失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@employees_bp.route('/stats/overview', methods=['GET'])
def get_employees_overview():
    """
    获取所有员工的统计概览
    查询参数: start_date, end_date (可选)
    返回: 所有员工的统计概览
    """
    try:
        from models import EmployeeMapping, ChatMessage
        
        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 构建时间过滤条件
        time_filter = []
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                time_filter.append(ChatMessage.timestamp >= start_datetime)
            except ValueError:
                return jsonify({'success': False, 'error': '开始日期格式错误'}), 400
        
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                time_filter.append(ChatMessage.timestamp <= end_datetime)
            except ValueError:
                return jsonify({'success': False, 'error': '结束日期格式错误'}), 400
        
        # 获取所有员工
        employees = EmployeeMapping.query.all()
        overview_data = []
        
        for employee in employees:
            # 统计该员工的消息数量
            message_query = ChatMessage.query.filter_by(sender_name=employee.wechat_nickname)
            if time_filter:
                message_query = message_query.filter(*time_filter)
            
            total_messages = message_query.count()
            file_messages = message_query.filter_by(message_type=49).count()
            
            # 统计活跃天数
            active_days_query = db.session.query(
                func.date(ChatMessage.timestamp).label('date')
            ).filter_by(sender_name=employee.wechat_nickname)
            
            if time_filter:
                active_days_query = active_days_query.filter(*time_filter)
            
            active_days = active_days_query.distinct().count()
            
            # 获取最近活跃时间
            latest_message = message_query.order_by(ChatMessage.timestamp.desc()).first()
            latest_activity = latest_message.timestamp if latest_message else None
            
            overview_data.append({
                'employee_id': employee.id,
                'wechat_nickname': employee.wechat_nickname,
                'real_name': employee.real_name,
                'position': employee.position,
                'role': employee.role,
                'total_messages': total_messages,
                'file_messages': file_messages,
                'active_days': active_days,
                'latest_activity': latest_activity.isoformat() if latest_activity else None
            })
        
        # 按消息数量排序
        overview_data.sort(key=lambda x: x['total_messages'], reverse=True)
        
        # 计算总体统计
        total_employees = len(overview_data)
        total_messages = sum(item['total_messages'] for item in overview_data)
        total_files = sum(item['file_messages'] for item in overview_data)
        total_active_days = sum(item['active_days'] for item in overview_data)
        
        return jsonify({
            'success': True,
            'data': {
                'employees': overview_data,
                'summary': {
                    'total_employees': total_employees,
                    'total_messages': total_messages,
                    'total_files': total_files,
                    'total_active_days': total_active_days,
                    'avg_messages_per_employee': round(total_messages / total_employees, 2) if total_employees > 0 else 0
                },
                'time_range': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
        })
    except Exception as e:
        logger.error(f"获取员工统计概览失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@employees_bp.route('/unmapped', methods=['GET'])
def get_unmapped_senders():
    """
    获取未映射的微信用户列表
    这个接口会查询所有在聊天记录中出现但未被映射的微信昵称
    返回: 未映射用户列表
    """
    try:
        # 使用统一数据管理器获取未映射用户
        result = data_manager.get_unmapped_senders()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"获取未映射用户列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@employees_bp.route('/unmapped/batch-add', methods=['POST'])
def batch_add_unmapped_senders():
    """
    批量添加未映射用户为员工
    请求体: JSON格式，包含要添加的用户列表
    返回: 批量添加结果
    """
    try:
        data = request.get_json()
        if not data or 'senders' not in data:
            return jsonify({'success': False, 'error': '缺少请求数据或senders字段'}), 400
        
        senders = data['senders']
        if not isinstance(senders, list):
            return jsonify({'success': False, 'error': 'senders必须是数组格式'}), 400
        
        # 验证每个发送者的数据格式
        for sender in senders:
            required_fields = ['sender_name', 'real_name', 'position', 'name_abbreviation']
            for field in required_fields:
                if field not in sender or not sender[field]:
                    return jsonify({'success': False, 'error': f'缺少必填字段: {field}'}), 400
        
        # 转换为员工映射格式
        mappings = []
        for sender in senders:
            mappings.append({
                'wechat_nickname': sender['sender_name'],
                'real_name': sender['real_name'],
                'position': sender['position'],
                'name_abbreviation': sender['name_abbreviation'],
                'role': sender.get('role', '内部员工')
            })
        
        # 使用统一数据管理器批量添加
        result = data_manager.batch_add_employee_mappings(mappings)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"批量添加未映射用户失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@employees_bp.route('/batch-import', methods=['POST'])
def batch_import_employees():
    """
    批量导入员工数据
    请求体: JSON格式，包含员工列表
    返回: 批量导入结果
    """
    try:
        data = request.get_json()
        if not data or 'employees' not in data:
            return jsonify({'success': False, 'error': '缺少请求数据或employees字段'}), 400
        
        employees = data['employees']
        if not isinstance(employees, list):
            return jsonify({'success': False, 'error': 'employees必须是数组格式'}), 400
        
        # 验证每个员工的数据格式
        for employee in employees:
            required_fields = ['wechat_nickname', 'real_name', 'position', 'name_abbreviation']
            for field in required_fields:
                if field not in employee or not employee[field]:
                    return jsonify({'success': False, 'error': f'缺少必填字段: {field}'}), 400
        
        # 使用统一数据管理器批量添加
        result = data_manager.batch_add_employee_mappings(employees)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"批量导入员工失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@employees_bp.route('/export', methods=['GET'])
def export_employees():
    """
    导出员工数据
    返回: CSV格式的员工数据
    """
    try:
        from models import EmployeeMapping
        import csv
        from io import StringIO
        
        employees = EmployeeMapping.query.all()
        
        # 创建CSV数据
        output = StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow(['ID', '微信昵称', '真实姓名', '职位', '姓名缩写', '角色', '创建时间', '更新时间'])
        
        # 写入数据
        for emp in employees:
            writer.writerow([
                emp.id,
                emp.wechat_nickname,
                emp.real_name,
                emp.position,
                emp.name_abbreviation,
                emp.role,
                emp.created_at.isoformat() if emp.created_at else '',
                emp.updated_at.isoformat() if emp.updated_at else ''
            ])
        
        from flask import Response
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=employees.csv'}
        )
        
    except Exception as e:
        logger.error(f"导出员工数据失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500 