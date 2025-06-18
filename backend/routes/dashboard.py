# 仪表盘相关的API路由
# 这个文件包含所有与仪表盘相关的API端点，包括总体统计、趋势分析等功能

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
from sqlalchemy import func, and_, desc
import logging
from db import db

# 创建仪表盘蓝图
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/v1/dashboard')

# 配置日志
logger = logging.getLogger(__name__)

@dashboard_bp.route('/overview', methods=['GET'])
def get_dashboard_overview():
    """
    获取仪表盘总览数据
    查询参数: start_date, end_date (可选)
    返回: 总览统计数据
    """
    try:
        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 构建查询条件
        conditions = []
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                conditions.append(ChatMessage.timestamp >= start_dt)
            except ValueError:
                return jsonify({'success': False, 'error': '开始日期格式错误'}), 400
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                conditions.append(ChatMessage.timestamp <= end_dt)
            except ValueError:
                return jsonify({'success': False, 'error': '结束日期格式错误'}), 400
        
        # 统计总消息数
        total_messages_query = ChatMessage.query
        if conditions:
            total_messages_query = total_messages_query.filter(and_(*conditions))
        total_messages = total_messages_query.count()
        
        # 统计总文件数
        total_files_query = FileRecord.query
        if start_date:
            total_files_query = total_files_query.filter(FileRecord.upload_time >= start_dt)
        if end_date:
            total_files_query = total_files_query.filter(FileRecord.upload_time <= end_dt)
        total_files = total_files_query.count()
        
        # 统计活跃员工数
        active_employees_query = db.session.query(
            func.count(func.distinct(ChatMessage.sender_name))
        )
        if conditions:
            active_employees_query = active_employees_query.filter(and_(*conditions))
        active_employees = active_employees_query.scalar()
        
        # 统计项目数
        total_projects = Project.query.count()
        
        # 今日数据
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        today_messages = ChatMessage.query.filter(
            ChatMessage.timestamp >= today_start,
            ChatMessage.timestamp <= today_end
        ).count()
        
        today_files = FileRecord.query.filter(
            FileRecord.upload_time >= today_start,
            FileRecord.upload_time <= today_end
        ).count()
        
        # 本周数据
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        week_start_dt = datetime.combine(week_start, datetime.min.time())
        week_end_dt = datetime.combine(week_end, datetime.max.time())
        
        week_messages = ChatMessage.query.filter(
            ChatMessage.timestamp >= week_start_dt,
            ChatMessage.timestamp <= week_end_dt
        ).count()
        
        week_files = FileRecord.query.filter(
            FileRecord.upload_time >= week_start_dt,
            FileRecord.upload_time <= week_end_dt
        ).count()
        
        return jsonify({
            'success': True,
            'data': {
                'overview': {
                    'total_messages': total_messages,
                    'total_files': total_files,
                    'active_employees': active_employees,
                    'total_projects': total_projects
                },
                'today': {
                    'messages': today_messages,
                    'files': today_files
                },
                'this_week': {
                    'messages': week_messages,
                    'files': week_files
                },
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
        })
    except Exception as e:
        logger.error(f"获取仪表盘总览失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/trends', methods=['GET'])
def get_dashboard_trends():
    """
    获取趋势数据
    查询参数: days (默认30天)
    返回: 趋势统计数据
    """
    try:
        # 获取查询参数
        days = request.args.get('days', 30, type=int)
        
        # 计算日期范围
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        # 按日期统计消息数量
        message_trends = db.session.query(
            func.date(ChatMessage.timestamp).label('date'),
            func.count(ChatMessage.id).label('count')
        ).filter(
            ChatMessage.timestamp >= datetime.combine(start_date, datetime.min.time()),
            ChatMessage.timestamp <= datetime.combine(end_date, datetime.max.time())
        ).group_by(
            func.date(ChatMessage.timestamp)
        ).order_by(
            func.date(ChatMessage.timestamp)
        ).all()
        
        # 按日期统计文件数量
        file_trends = db.session.query(
            func.date(FileRecord.upload_time).label('date'),
            func.count(FileRecord.id).label('count')
        ).filter(
            FileRecord.upload_time >= datetime.combine(start_date, datetime.min.time()),
            FileRecord.upload_time <= datetime.combine(end_date, datetime.max.time())
        ).group_by(
            func.date(FileRecord.upload_time)
        ).order_by(
            func.date(FileRecord.upload_time)
        ).all()
        
        # 转换为字典格式，便于前端处理
        message_data = {str(trend.date): trend.count for trend in message_trends}
        file_data = {str(trend.date): trend.count for trend in file_trends}
        
        # 生成完整的日期序列
        date_series = []
        current_date = start_date
        while current_date <= end_date:
            date_str = str(current_date)
            date_series.append({
                'date': date_str,
                'messages': message_data.get(date_str, 0),
                'files': file_data.get(date_str, 0)
            })
            current_date += timedelta(days=1)
        
        return jsonify({
            'success': True,
            'data': {
                'trends': date_series,
                'period': {
                    'start_date': str(start_date),
                    'end_date': str(end_date),
                    'days': days
                }
            }
        })
    except Exception as e:
        logger.error(f"获取趋势数据失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/top-performers', methods=['GET'])
def get_top_performers():
    """
    获取表现最佳的员工
    查询参数: limit (默认10), period (today, week, month)
    返回: 员工表现排名
    """
    try:
        # 获取查询参数
        limit = request.args.get('limit', 10, type=int)
        period = request.args.get('period', 'week')
        
        # 计算时间范围
        now = datetime.now()
        if period == 'today':
            start_time = datetime.combine(now.date(), datetime.min.time())
        elif period == 'week':
            start_time = now - timedelta(days=7)
        elif period == 'month':
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(days=7)  # 默认一周
        
        # 统计消息数量排名
        message_rankings = db.session.query(
            ChatMessage.sender_name,
            func.count(ChatMessage.id).label('message_count')
        ).filter(
            ChatMessage.timestamp >= start_time
        ).group_by(
            ChatMessage.sender_name
        ).order_by(
            desc(func.count(ChatMessage.id))
        ).limit(limit).all()
        
        # 统计文件数量排名
        file_rankings = db.session.query(
            FileRecord.author_abbreviation,
            func.count(FileRecord.id).label('file_count')
        ).filter(
            FileRecord.upload_time >= start_time
        ).group_by(
            FileRecord.author_abbreviation
        ).order_by(
            desc(func.count(FileRecord.id))
        ).limit(limit).all()
        
        # 获取员工映射信息
        employee_mappings = {
            emp.wechat_nickname: emp.real_name 
            for emp in EmployeeMapping.query.all()
        }
        
        # 格式化消息排名数据
        message_data = []
        for rank, (sender_name, count) in enumerate(message_rankings, 1):
            message_data.append({
                'rank': rank,
                'sender_name': sender_name,
                'real_name': employee_mappings.get(sender_name, sender_name),
                'message_count': count
            })
        
        # 格式化文件排名数据
        file_data = []
        for rank, (author_abbr, count) in enumerate(file_rankings, 1):
            file_data.append({
                'rank': rank,
                'author_abbreviation': author_abbr,
                'file_count': count
            })
        
        return jsonify({
            'success': True,
            'data': {
                'message_rankings': message_data,
                'file_rankings': file_data,
                'period': period,
                'start_time': start_time.isoformat()
            }
        })
    except Exception as e:
        logger.error(f"获取表现最佳员工失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/project-summary', methods=['GET'])
def get_project_summary():
    """
    获取项目汇总数据
    返回: 项目汇总统计
    """
    try:
        # 获取所有项目
        projects = Project.query.all()
        project_summary = []
        
        for project in projects:
            # 统计项目相关的聊天消息
            chatroom_names = [
                chatroom.chatroom_name 
                for chatroom in ProjectChatroom.query.filter_by(project_id=project.id).all()
            ]
            
            message_count = 0
            if chatroom_names:
                message_count = ChatMessage.query.filter(
                    ChatMessage.talker_name.in_(chatroom_names)
                ).count()
            
            # 统计项目相关的文件
            file_count = FileRecord.query.filter(
                FileRecord.project_name == project.name
            ).count()
            
            project_summary.append({
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'status': project.status,
                'message_count': message_count,
                'file_count': file_count,
                'chatroom_count': len(chatroom_names)
            })
        
        # 按消息数量排序
        project_summary.sort(key=lambda x: x['message_count'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': project_summary
        })
    except Exception as e:
        logger.error(f"获取项目汇总失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500 