# 员工管理相关的API路由
# 这个文件包含所有与员工管理相关的API端点，包括员工映射、统计等功能

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
from sqlalchemy import func, and_
import logging
from db import db

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
        from models import EmployeeMapping, ChatMessage, FileRecord
        
        employee = EmployeeMapping.query.get(employee_id)
        if not employee:
            return jsonify({'success': False, 'error': '员工不存在'}), 404
        
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
        
        # 统计消息数量
        message_query = ChatMessage.query.filter_by(sender_name=employee.wechat_nickname)
        if time_filter:
            message_query = message_query.filter(*time_filter)
        
        total_messages = message_query.count()
        
        # 统计文件数量
        file_messages = message_query.filter_by(message_type=49).count()
        
        # 统计图片数量
        image_messages = message_query.filter_by(message_type=3).count()
        
        # 统计文本消息数量
        text_messages = message_query.filter_by(message_type=1).count()
        
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
        
        # 统计按项目分组的消息数量
        project_stats_query = db.session.query(
            ChatMessage.project_id,
            func.count(ChatMessage.id).label('message_count')
        ).filter_by(sender_name=employee.wechat_nickname)
        
        if time_filter:
            project_stats_query = project_stats_query.filter(*time_filter)
        
        project_stats = project_stats_query.group_by(ChatMessage.project_id).all()
        
        # 获取项目名称
        project_details = []
        for project_id, message_count in project_stats:
            if project_id:
                from models import Project
                project = Project.query.get(project_id)
                project_name = project.project_name if project else f"项目{project_id}"
            else:
                project_name = "未分类"
            
            project_details.append({
                'project_id': project_id,
                'project_name': project_name,
                'message_count': message_count
            })
        
        # 按消息数量排序
        project_details.sort(key=lambda x: x['message_count'], reverse=True)
        
        # 计算平均每天消息数
        if active_days > 0:
            avg_messages_per_day = round(total_messages / active_days, 2)
        else:
            avg_messages_per_day = 0
        
        return jsonify({
            'success': True,
            'data': {
                'employee_info': {
                    'id': employee.id,
                    'wechat_nickname': employee.wechat_nickname,
                    'real_name': employee.real_name,
                    'position': employee.position,
                    'role': employee.role
                },
                'message_stats': {
                    'total_messages': total_messages,
                    'text_messages': text_messages,
                    'image_messages': image_messages,
                    'file_messages': file_messages,
                    'avg_messages_per_day': avg_messages_per_day
                },
                'activity_stats': {
                    'active_days': active_days,
                    'latest_activity': latest_activity.isoformat() if latest_activity else None
                },
                'project_stats': project_details,
                'time_range': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
        })
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
        from models import EmployeeMapping, ChatMessage
        
        # 获取所有已映射的微信昵称
        mapped_nicknames = db.session.query(EmployeeMapping.wechat_nickname).all()
        mapped_nicknames_set = {nickname[0] for nickname in mapped_nicknames}
        
        # 获取所有聊天记录中的发送者昵称
        all_senders = db.session.query(ChatMessage.sender_name).distinct().all()
        all_senders_set = {sender[0] for sender in all_senders if sender[0]}
        
        # 找出未映射的发送者
        unmapped_senders = all_senders_set - mapped_nicknames_set
        
        # 统计每个未映射发送者的消息数量
        unmapped_senders_with_stats = []
        for sender in unmapped_senders:
            message_count = ChatMessage.query.filter_by(sender_name=sender).count()
            unmapped_senders_with_stats.append({
                'sender_name': sender,
                'message_count': message_count
            })
        
        # 按消息数量降序排列
        unmapped_senders_with_stats.sort(key=lambda x: x['message_count'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'unmapped_senders': unmapped_senders_with_stats,
                'total_count': len(unmapped_senders_with_stats),
                'mapped_count': len(mapped_nicknames_set),
                'total_senders': len(all_senders_set)
            }
        })
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
        from models import EmployeeMapping
        
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
        
        # 检查是否有重复的微信昵称
        sender_names = [s['sender_name'] for s in senders]
        existing_employees = EmployeeMapping.query.filter(
            EmployeeMapping.wechat_nickname.in_(sender_names)
        ).all()
        
        if existing_employees:
            existing_names = [emp.wechat_nickname for emp in existing_employees]
            return jsonify({
                'success': False, 
                'error': f'以下微信昵称已存在: {", ".join(existing_names)}'
            }), 400
        
        # 批量创建员工映射
        new_employees = []
        for sender in senders:
            new_employee = EmployeeMapping(
                wechat_nickname=sender['sender_name'],
                real_name=sender['real_name'],
                position=sender['position'],
                name_abbreviation=sender['name_abbreviation'],
                role=sender.get('role', '员工'),
                created_at=datetime.utcnow()
            )
            new_employees.append(new_employee)
            db.session.add(new_employee)
        
        db.session.commit()
        
        # 返回创建结果
        created_data = []
        for emp in new_employees:
            created_data.append({
                'id': emp.id,
                'wechat_nickname': emp.wechat_nickname,
                'real_name': emp.real_name,
                'position': emp.position,
                'name_abbreviation': emp.name_abbreviation,
                'role': emp.role,
                'created_at': emp.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'data': created_data,
            'message': f'成功添加 {len(created_data)} 个员工映射'
        })
    except Exception as e:
        logger.error(f"批量添加未映射用户失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@employees_bp.route('/batch-import', methods=['POST'])
def batch_import_employees():
    """
    批量导入员工映射（支持CSV/JSON格式）
    请求体: 文件上传或JSON数组
    返回: 导入结果
    """
    try:
        from models import EmployeeMapping
        
        # 检查是否有文件上传
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({'success': False, 'error': '未选择文件'}), 400
            
            # 这里可以添加CSV解析逻辑
            # 暂时返回错误，提示使用JSON格式
            return jsonify({'success': False, 'error': '暂不支持文件上传，请使用JSON格式'}), 400
        
        # 处理JSON格式的批量导入
        data = request.get_json()
        if not data or 'employees' not in data:
            return jsonify({'success': False, 'error': '缺少请求数据或employees字段'}), 400
        
        employees_data = data['employees']
        if not isinstance(employees_data, list):
            return jsonify({'success': False, 'error': 'employees必须是数组格式'}), 400
        
        # 验证数据格式
        for emp in employees_data:
            required_fields = ['wechat_nickname', 'real_name', 'position', 'name_abbreviation']
            for field in required_fields:
                if field not in emp or not emp[field]:
                    return jsonify({'success': False, 'error': f'缺少必填字段: {field}'}), 400
        
        # 检查重复的微信昵称
        wechat_nicknames = [emp['wechat_nickname'] for emp in employees_data]
        existing_employees = EmployeeMapping.query.filter(
            EmployeeMapping.wechat_nickname.in_(wechat_nicknames)
        ).all()
        
        if existing_employees:
            existing_names = [emp.wechat_nickname for emp in existing_employees]
            return jsonify({
                'success': False, 
                'error': f'以下微信昵称已存在: {", ".join(existing_names)}'
            }), 400
        
        # 批量创建员工映射
        new_employees = []
        for emp_data in employees_data:
            new_employee = EmployeeMapping(
                wechat_nickname=emp_data['wechat_nickname'],
                real_name=emp_data['real_name'],
                position=emp_data['position'],
                name_abbreviation=emp_data['name_abbreviation'],
                role=emp_data.get('role', '员工'),
                created_at=datetime.utcnow()
            )
            new_employees.append(new_employee)
            db.session.add(new_employee)
        
        db.session.commit()
        
        # 返回创建结果
        created_data = []
        for emp in new_employees:
            created_data.append({
                'id': emp.id,
                'wechat_nickname': emp.wechat_nickname,
                'real_name': emp.real_name,
                'position': emp.position,
                'name_abbreviation': emp.name_abbreviation,
                'role': emp.role,
                'created_at': emp.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'data': created_data,
            'message': f'成功导入 {len(created_data)} 个员工映射'
        })
    except Exception as e:
        logger.error(f"批量导入员工失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@employees_bp.route('/export', methods=['GET'])
def export_employees():
    """
    导出员工映射数据
    返回: JSON格式的员工映射列表
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
            'data': employee_list,
            'export_time': datetime.utcnow().isoformat(),
            'total_count': len(employee_list)
        })
    except Exception as e:
        logger.error(f"导出员工数据失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500 