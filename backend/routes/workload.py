# 工作量记录API路由
# 实现WorkloadRecord的数据闭环，支持按员工、按项目查询工作量明细
# 按照《精准评估模型 (V2)》实现WE计算和负荷分析

from flask import Blueprint, request, jsonify
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import func, and_, or_, desc
from sqlalchemy.orm import joinedload

from backend.db import db
from backend.models.workload import WorkloadRecord, EmployeeLoadBaseline, WorkloadWeights
from backend.models.employee import EmployeeMapping
from backend.models.project import Project
from backend.models.file import FileRecord
from backend.models.chat import ChatMessage
from backend.parser_service import ParserService
from backend.analysis_service import AnalysisService
from backend.utils import APIResponse, ValidationHelper, PaginationHelper

# 创建蓝图
workload_bp = Blueprint('workload', __name__, url_prefix='/api/v1/workload')

# 初始化服务
parser_service = ParserService()
analysis_service = AnalysisService()

@workload_bp.route('/records', methods=['GET'])
def get_workload_records():
    """
    获取工作量记录列表
    支持按员工、项目、时间范围等条件筛选
    """
    try:
        # 获取查询参数
        employee_id = request.args.get('employee_id', type=int)
        project_id = request.args.get('project_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        role = request.args.get('role')
        output_type = request.args.get('output_type')
        
        # 构建查询条件
        query = WorkloadRecord.query.options(
            joinedload(WorkloadRecord.employee),
            joinedload(WorkloadRecord.project),
            joinedload(WorkloadRecord.file_record)
        )
        
        if employee_id:
            query = query.filter(WorkloadRecord.employee_id == employee_id)
        if project_id:
            query = query.filter(WorkloadRecord.project_id == project_id)
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(WorkloadRecord.date >= start_date_obj)
            except ValueError:
                return jsonify({'success': False, 'data': None, 'message': "开始日期格式错误，请使用YYYY-MM-DD格式"})
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(WorkloadRecord.date <= end_date_obj)
            except ValueError:
                return jsonify({'success': False, 'data': None, 'message': "结束日期格式错误，请使用YYYY-MM-DD格式"})
        if role:
            query = query.filter(WorkloadRecord.role == role)
        if output_type:
            query = query.filter(WorkloadRecord.output_type == output_type)
        
        # 按日期倒序排列
        query = query.order_by(desc(WorkloadRecord.date), desc(WorkloadRecord.created_at))
        
        # 分页处理
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 正确解包apply_pagination返回值
        paginated_query, total = PaginationHelper.apply_pagination(query, page, per_page)
        records = paginated_query.all()
        total_pages = (total + per_page - 1) // per_page
        
        # 转换为字典格式
        records_data = [record.to_dict() for record in records]
        
        return jsonify({'success': True, 'data': {
            'records': records_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': total_pages
            }
        }, 'message': None})
        
    except Exception as e:
        return jsonify({'success': False, 'data': None, 'message': f"获取工作量记录失败: {str(e)}"}), 500

@workload_bp.route('/records/<int:record_id>', methods=['GET'])
def get_workload_record_detail(record_id: int):
    """
    获取单个工作量记录详情
    """
    try:
        record = WorkloadRecord.query.options(
            joinedload(WorkloadRecord.employee),
            joinedload(WorkloadRecord.project),
            joinedload(WorkloadRecord.file_record)
        ).filter(WorkloadRecord.id == record_id).first()
        
        if not record:
            return jsonify({'success': False, 'data': None, 'message': "工作量记录不存在"})
        
        return jsonify({'success': True, 'data': record.to_dict(), 'message': None})
        
    except Exception as e:
        return jsonify({'success': False, 'data': None, 'message': f"获取工作量记录详情失败: {str(e)}"}), 500

@workload_bp.route('/employees/<int:employee_id>/stats', methods=['GET'])
def get_employee_workload_stats(employee_id: int):
    """
    获取员工工作量统计
    包括WE总量、负荷指数、效率评分等
    """
    try:
        # 获取时间范围参数
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # 默认查询最近30天
        if not start_date_str:
            start_date = date.today() - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            
        if not end_date_str:
            end_date = date.today()
        else:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # 获取员工信息
        employee = EmployeeMapping.query.filter(EmployeeMapping.id == employee_id).first()
        if not employee:
            return jsonify({'success': False, 'data': None, 'message': "员工不存在"})
        
        # 获取工作量记录
        records = WorkloadRecord.query.filter(
            and_(
                WorkloadRecord.employee_id == employee_id,
                WorkloadRecord.date >= start_date,
                WorkloadRecord.date <= end_date
            )
        ).all()
        
        # 计算统计数据
        total_we = sum(record.we_value for record in records)
        total_records = len(records)
        final_records = sum(1 for record in records if record.is_final)
        iteration_records = sum(1 for record in records if record.is_iteration)
        
        # 按岗位分组统计
        role_stats = {}
        for record in records:
            role = record.role
            if role not in role_stats:
                role_stats[role] = {
                    'total_we': 0,
                    'record_count': 0,
                    'final_count': 0
                }
            role_stats[role]['total_we'] += record.we_value
            role_stats[role]['record_count'] += 1
            if record.is_final:
                role_stats[role]['final_count'] += 1
        
        # 计算负荷指数
        load_index = analysis_service.calculate_employee_load_index(
            employee_id, start_date, end_date
        )
        
        return jsonify({'success': True, 'data': {
            'employee': {
                'id': employee.id,
                'real_name': employee.real_name,
                'nickname': employee.nickname,
                'position': employee.position
            },
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': (end_date - start_date).days + 1
            },
            'summary': {
                'total_we': round(total_we, 2),
                'total_records': total_records,
                'final_records': final_records,
                'iteration_records': iteration_records,
                'avg_we_per_day': round(total_we / max(1, (end_date - start_date).days + 1), 2)
            },
            'role_stats': role_stats,
            'load_index': load_index
        }, 'message': None})
        
    except Exception as e:
        return jsonify({'success': False, 'data': None, 'message': f"获取员工工作量统计失败: {str(e)}"}), 500

@workload_bp.route('/projects/<int:project_id>/stats', methods=['GET'])
def get_project_workload_stats(project_id: int):
    """
    获取项目工作量统计
    包括项目总WE、参与员工、健康度评分等
    """
    try:
        # 获取项目信息
        project = Project.query.filter(Project.id == project_id).first()
        if not project:
            return jsonify({'success': False, 'data': None, 'message': "项目不存在"})
        
        # 获取项目工作量记录
        records = WorkloadRecord.query.options(
            joinedload(WorkloadRecord.employee)
        ).filter(WorkloadRecord.project_id == project_id).all()
        
        # 计算项目统计数据
        total_we = sum(record.we_value for record in records)
        total_records = len(records)
        unique_employees = len(set(record.employee_id for record in records))
        
        # 按员工分组统计
        employee_stats = {}
        for record in records:
            employee_id = record.employee_id
            if employee_id not in employee_stats:
                employee_stats[employee_id] = {
                    'employee_name': record.employee.real_name if record.employee else '未知',
                    'total_we': 0,
                    'record_count': 0,
                    'roles': set()
                }
            employee_stats[employee_id]['total_we'] += record.we_value
            employee_stats[employee_id]['record_count'] += 1
            employee_stats[employee_id]['roles'].add(record.role)
        
        # 转换roles为列表
        for stats in employee_stats.values():
            stats['roles'] = list(stats['roles'])
        
        # 计算项目健康度
        health_score = analysis_service.calculate_project_health_score(project_id)
        
        return jsonify({'success': True, 'data': {
            'project': {
                'id': project.id,
                'project_name': project.project_name,
                'client_name': project.client_name,
                'status': project.status
            },
            'summary': {
                'total_we': round(total_we, 2),
                'total_records': total_records,
                'unique_employees': unique_employees,
                'avg_we_per_employee': round(total_we / max(1, unique_employees), 2)
            },
            'employee_stats': employee_stats,
            'health_score': health_score
        }, 'message': None})
        
    except Exception as e:
        return jsonify({'success': False, 'data': None, 'message': f"获取项目工作量统计失败: {str(e)}"}), 500

@workload_bp.route('/sync', methods=['POST'])
def sync_workload_records():
    """
    同步工作量记录
    从文件记录和聊天记录中解析并创建WorkloadRecord
    """
    try:
        # 获取同步参数
        data = request.get_json() or {}
        force_sync = data.get('force_sync', False)
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # 解析时间范围
        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date_obj = date.today() - timedelta(days=7)  # 默认同步最近7天
            
        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date_obj = date.today()
        
        # 同步文件记录
        file_records_synced = _sync_file_records(start_date_obj, end_date_obj, force_sync)
        
        # 同步聊天记录
        chat_records_synced = _sync_chat_records(start_date_obj, end_date_obj, force_sync)
        
        return jsonify({'success': True, 'data': {
            'message': '工作量记录同步完成',
            'file_records_synced': file_records_synced,
            'chat_records_synced': chat_records_synced,
            'period': {
                'start_date': start_date_obj.isoformat(),
                'end_date': end_date_obj.isoformat()
            }
        }, 'message': None})
        
    except Exception as e:
        return jsonify({'success': False, 'data': None, 'message': f"同步工作量记录失败: {str(e)}"}), 500

def _sync_file_records(start_date: date, end_date: date, force_sync: bool = False) -> int:
    """
    同步文件记录为工作量记录
    """
    synced_count = 0
    
    # 获取指定时间范围内的文件记录
    file_records = FileRecord.query.filter(
        and_(
            FileRecord.upload_time >= datetime.combine(start_date, datetime.min.time()),
            FileRecord.upload_time <= datetime.combine(end_date, datetime.max.time())
        )
    ).all()
    
    for file_record in file_records:
        # 检查是否已经存在对应的工作量记录
        if not force_sync:
            existing_record = WorkloadRecord.query.filter(
                WorkloadRecord.related_file_id == file_record.id
            ).first()
            if existing_record:
                continue
        
        # 解析文件名
        parsed_data = parser_service.parse(file_record.original_name)
        if not parsed_data:
            continue
        
        # 查找员工映射
        employee = EmployeeMapping.query.filter(
            EmployeeMapping.nickname == file_record.uploader
        ).first()
        if not employee:
            continue
        
        # 查找或创建项目
        project = Project.query.filter(
            Project.project_name == parsed_data.project_name
        ).first()
        if not project:
            project = Project(
                project_name=parsed_data.project_name,
                client_name='未知客户',
                status='进行中'
            )
            db.session.add(project)
            db.session.flush()  # 获取project.id
        
        # 计算WE值
        we_value = analysis_service.calculate_workload_equivalent_from_parsed_data(parsed_data)
        
        # 创建工作量记录
        workload_record = WorkloadRecord(
            employee_id=employee.id,
            project_id=project.id,
            date=parsed_data.submission_date,
            role=_determine_role_from_file(file_record.original_name),
            output_type='文件交付',
            output_value=file_record.original_name,
            we_value=we_value,
            is_final=parsed_data.version >= 3,  # 版本3以上认为是最终版
            is_iteration=parsed_data.version > 1,
            iteration_count=parsed_data.version - 1,
            related_file_id=file_record.id,
            business_unit=parsed_data.workload_amount,
            quantity=1.0
        )
        
        db.session.add(workload_record)
        synced_count += 1
    
    db.session.commit()
    return synced_count

def _sync_chat_records(start_date: date, end_date: date, force_sync: bool = False) -> int:
    """
    同步聊天记录为工作量记录
    """
    synced_count = 0
    
    # 获取指定时间范围内的聊天记录
    chat_messages = ChatMessage.query.filter(
        and_(
            ChatMessage.time >= datetime.combine(start_date, datetime.min.time()),
            ChatMessage.time <= datetime.combine(end_date, datetime.max.time())
        )
    ).all()
    
    for message in chat_messages:
        # 检查是否已经存在对应的工作量记录
        if not force_sync:
            existing_record = WorkloadRecord.query.filter(
                WorkloadRecord.related_message_id == str(message.id)
            ).first()
            if existing_record:
                continue
        
        # 查找员工映射
        employee = EmployeeMapping.query.filter(
            EmployeeMapping.nickname == message.sender_name
        ).first()
        if not employee:
            continue
        
        # 查找项目（通过群聊名称）
        project = Project.query.filter(
            Project.project_name.like(f"%{message.talker_name}%")
        ).first()
        if not project:
            continue
        
        # 分析消息内容，确定产出类型和WE值
        output_type, we_value = _analyze_chat_message(message)
        if we_value == 0:
            continue
        
        # 创建工作量记录
        workload_record = WorkloadRecord(
            employee_id=employee.id,
            project_id=project.id,
            date=message.time.date(),
            role=_determine_role_from_chat(message),
            output_type=output_type,
            output_value=message.content[:100],  # 截取前100个字符
            we_value=we_value,
            is_final=False,  # 聊天记录通常不是最终产出
            is_iteration=False,
            iteration_count=0,
            related_message_id=str(message.id),
            business_unit='次',
            quantity=1.0
        )
        
        db.session.add(workload_record)
        synced_count += 1
    
    db.session.commit()
    return synced_count

def _determine_role_from_file(filename: str) -> str:
    """根据文件名确定岗位"""
    filename_lower = filename.lower()
    
    if any(ext in filename_lower for ext in ['.psd', '.ai', '.sketch', '.fig', '.xd']):
        return '设计'
    elif any(ext in filename_lower for ext in ['.doc', '.docx', '.txt', '.md']):
        return '文案'
    elif any(ext in filename_lower for ext in ['.xls', '.xlsx', '.ppt', '.pptx']):
        return 'PM'
    else:
        return 'AE'

def _determine_role_from_chat(message) -> str:
    """根据聊天内容确定岗位"""
    # 这里可以根据关键词或员工映射来确定岗位
    # 暂时返回默认值
    return 'AE'

def _analyze_chat_message(message) -> tuple:
    """分析聊天消息，返回产出类型和WE值"""
    content = message.content.lower()
    
    # 根据消息内容判断产出类型和WE值
    if any(word in content for word in ['收到', '好的', '没问题']):
        return '确认回复', 0.1
    elif any(word in content for word in ['修改', '调整', '更新']):
        return '修改意见', 0.3
    elif any(word in content for word in ['完成', '搞定', '交付']):
        return '工作交付', 0.5
    elif message.type == '49':  # 文件消息
        return '文件分享', 0.2
    else:
        return '日常沟通', 0.05 