# 项目管理相关的API路由
# 这个文件包含所有与项目管理相关的API端点，包括项目创建、查询、统计等功能

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import logging
from sqlalchemy import func, and_
from db import db
from models import Project, ProjectChatroom, ChatMessage, FileRecord, EmployeeMapping

# 创建蓝图
projects_bp = Blueprint('projects', __name__, url_prefix='/api/v1/projects')

# 配置日志
logger = logging.getLogger(__name__)

@projects_bp.route('/', methods=['GET'])
def get_projects():
    """
    获取所有项目列表
    返回: 项目数据列表，每个项目包含群聊信息
    """
    try:
        projects = Project.query.all()
        project_list = []
        for project in projects:
            # 获取项目关联的群聊列表
            chatrooms = list(project.chatrooms)
            # 分组
            internal_chat_groups = [c.chatroom_name for c in chatrooms if c.chatroom_type == '内部群聊']
            external_chat_groups = [c.chatroom_name for c in chatrooms if c.chatroom_type == '外部群聊']
            chatrooms_dict = [
                {
                    'id': c.id,
                    'chatroom_id': c.chatroom_id,
                    'chatroom_name': c.chatroom_name,
                    'chatroom_type': c.chatroom_type,
                    'created_at': c.created_at.isoformat() if c.created_at else None
                } for c in chatrooms
            ]
            project_list.append({
                'id': project.id,
                'project_name': project.project_name,
                'description': project.description,
                'status': project.status,
                'start_date': project.start_date.isoformat() if project.start_date else None,
                'end_date': project.end_date.isoformat() if project.end_date else None,
                'created_at': project.created_at.isoformat() if project.created_at else None,
                'updated_at': project.updated_at.isoformat() if project.updated_at else None,
                'chatrooms': chatrooms_dict,
                'internal_chat_groups': internal_chat_groups,
                'external_chat_groups': external_chat_groups
            })
        return jsonify({
            'success': True,
            'data': project_list
        })
    except Exception as e:
        logger.error(f"获取项目列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@projects_bp.route('/', methods=['POST'])
def create_project():
    """
    创建新项目
    请求体: JSON格式，包含项目信息
    返回: 创建结果
    """
    try:
        data = request.get_json()
        logger.info(f"[create_project] 收到数据: {data}")
        if not data:
            return jsonify({'success': False, 'error': '缺少请求数据'}), 400
        
        # 验证必填字段
        if 'project_name' not in data or not data['project_name']:
            return jsonify({'success': False, 'error': '缺少项目名称'}), 400
        
        # 检查是否已存在相同名称的项目
        existing_project = Project.query.filter_by(project_name=data['project_name']).first()
        if existing_project:
            return jsonify({'success': False, 'error': '项目名称已存在'}), 400
        
        # 创建新项目
        new_project = Project(
            project_name=data['project_name'],
            description=data.get('description', ''),
            status=data.get('status', '进行中'),
            start_date=datetime.fromisoformat(data['start_date']) if data.get('start_date') else None,
            end_date=datetime.fromisoformat(data['end_date']) if data.get('end_date') else None,
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_project)
        db.session.commit()
        
        # 新增：自动同步群聊
        internal_groups = data.get('internal_chat_groups', [])
        external_groups = data.get('external_chat_groups', [])
        logger.info(f"[create_project] internal_chat_groups: {internal_groups} 类型: {type(internal_groups)}")
        logger.info(f"[create_project] external_chat_groups: {external_groups} 类型: {type(external_groups)}")
        for name in internal_groups:
            chatroom = ProjectChatroom(
                project_id=new_project.id,
                chatroom_id=name,
                chatroom_name=name,
                chatroom_type='内部群聊',
                created_at=datetime.utcnow()
            )
            db.session.add(chatroom)
        for name in external_groups:
            chatroom = ProjectChatroom(
                project_id=new_project.id,
                chatroom_id=name,
                chatroom_name=name,
                chatroom_type='外部群聊',
                created_at=datetime.utcnow()
            )
            db.session.add(chatroom)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': new_project.id,
                'project_name': new_project.project_name,
                'description': new_project.description,
                'status': new_project.status,
                'start_date': new_project.start_date.isoformat() if new_project.start_date else None,
                'end_date': new_project.end_date.isoformat() if new_project.end_date else None,
                'created_at': new_project.created_at.isoformat()
            },
            'message': '项目创建成功'
        })
    except Exception as e:
        logger.error(f"创建项目失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@projects_bp.route('/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """
    获取单个项目详情
    参数: project_id - 项目ID
    返回: 项目详情
    """
    try:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'success': False, 'error': '项目不存在'}), 404
        chatrooms = ProjectChatroom.query.filter_by(project_id=project_id).all()
        internal_chat_groups = [c.chatroom_name for c in chatrooms if c.chatroom_type == '内部群聊']
        external_chat_groups = [c.chatroom_name for c in chatrooms if c.chatroom_type == '外部群聊']
        chatroom_list = [
            {
                'id': c.id,
                'chatroom_name': c.chatroom_name,
                'chatroom_type': c.chatroom_type,
                'created_at': c.created_at.isoformat() if c.created_at else None
            } for c in chatrooms
        ]
        return jsonify({
            'success': True,
            'data': {
                'id': project.id,
                'project_name': project.project_name,
                'description': project.description,
                'status': project.status,
                'start_date': project.start_date.isoformat() if project.start_date else None,
                'end_date': project.end_date.isoformat() if project.end_date else None,
                'created_at': project.created_at.isoformat() if project.created_at else None,
                'updated_at': project.updated_at.isoformat() if project.updated_at else None,
                'chatrooms': chatroom_list,
                'internal_chat_groups': internal_chat_groups,
                'external_chat_groups': external_chat_groups
            }
        })
    except Exception as e:
        logger.error(f"获取项目详情失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@projects_bp.route('/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """
    更新项目信息
    参数: project_id - 项目ID
    请求体: JSON格式，包含要更新的字段
    返回: 更新结果
    """
    try:
        data = request.get_json()
        logger.info(f"[update_project] 收到数据: {data}")
        if not data:
            return jsonify({'success': False, 'error': '缺少请求数据'}), 400
        
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'success': False, 'error': '项目不存在'}), 404
        
        # 更新字段
        if 'project_name' in data:
            project.project_name = data['project_name']
        if 'description' in data:
            project.description = data['description']
        if 'status' in data:
            project.status = data['status']
        if 'start_date' in data:
            project.start_date = datetime.fromisoformat(data['start_date']) if data['start_date'] else None
        if 'end_date' in data:
            project.end_date = datetime.fromisoformat(data['end_date']) if data['end_date'] else None
        
        project.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # 新增：自动同步群聊
        internal_groups = data.get('internal_chat_groups', [])
        external_groups = data.get('external_chat_groups', [])
        logger.info(f"[update_project] internal_chat_groups: {internal_groups} 类型: {type(internal_groups)}")
        logger.info(f"[update_project] external_chat_groups: {external_groups} 类型: {type(external_groups)}")
        # 先清空原有群聊
        ProjectChatroom.query.filter_by(project_id=project_id).delete()
        db.session.commit()
        for name in internal_groups:
            chatroom = ProjectChatroom(
                project_id=project_id,
                chatroom_id=name,
                chatroom_name=name,
                chatroom_type='内部群聊',
                created_at=datetime.utcnow()
            )
            db.session.add(chatroom)
        for name in external_groups:
            chatroom = ProjectChatroom(
                project_id=project_id,
                chatroom_id=name,
                chatroom_name=name,
                chatroom_type='外部群聊',
                created_at=datetime.utcnow()
            )
            db.session.add(chatroom)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': project.id,
                'project_name': project.project_name,
                'description': project.description,
                'status': project.status,
                'start_date': project.start_date.isoformat() if project.start_date else None,
                'end_date': project.end_date.isoformat() if project.end_date else None,
                'created_at': project.created_at.isoformat() if project.created_at else None,
                'updated_at': project.updated_at.isoformat()
            },
            'message': '项目更新成功'
        })
    except Exception as e:
        logger.error(f"更新项目失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@projects_bp.route('/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """
    删除项目
    参数: project_id - 项目ID
    返回: 删除结果
    """
    try:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'success': False, 'error': '项目不存在'}), 404
        
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '项目删除成功'
        })
    except Exception as e:
        logger.error(f"删除项目失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@projects_bp.route('/<int:project_id>/chatrooms', methods=['POST'])
def add_project_chatroom(project_id):
    """
    为项目添加群聊
    参数: project_id - 项目ID
    请求体: JSON格式，包含群聊信息
    返回: 添加结果
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '缺少请求数据'}), 400
        
        # 验证项目是否存在
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'success': False, 'error': '项目不存在'}), 404
        
        # 验证必填字段
        if not data.get('chatroom_name'):
            return jsonify({'success': False, 'error': '群聊名称不能为空'}), 400
        
        # 检查是否已存在相同的群聊
        existing_chatroom = ProjectChatroom.query.filter_by(
            project_id=project_id,
            chatroom_name=data['chatroom_name']
        ).first()
        
        if existing_chatroom:
            return jsonify({'success': False, 'error': '该群聊已存在'}), 400
        
        # 创建新群聊
        new_chatroom = ProjectChatroom(
            project_id=project_id,
            chatroom_id=data.get('chatroom_id', data['chatroom_name']),  # 如果没有提供chatroom_id，使用chatroom_name
            chatroom_name=data['chatroom_name'],
            chatroom_type=data.get('chatroom_type', '微信群'),
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_chatroom)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': new_chatroom.id,
                'project_id': new_chatroom.project_id,
                'chatroom_name': new_chatroom.chatroom_name,
                'chatroom_type': new_chatroom.chatroom_type,
                'created_at': new_chatroom.created_at.isoformat()
            },
            'message': '群聊添加成功'
        })
    except Exception as e:
        import traceback
        logger.exception(f"添加项目群聊失败: {str(e)}")  # 打印详细堆栈
        tb = traceback.format_exc()
        return jsonify({'success': False, 'error': str(e), 'traceback': tb}), 500

@projects_bp.route('/<int:project_id>/stats', methods=['GET'])
def get_project_stats(project_id):
    """
    获取项目统计信息
    参数: project_id - 项目ID
    查询参数: start_date, end_date (可选)
    返回: 项目统计数据
    """
    try:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'success': False, 'error': '项目不存在'}), 404
        
        # 获取项目关联的群聊
        chatrooms = ProjectChatroom.query.filter_by(project_id=project_id).all()
        chatroom_names = [cr.chatroom_name for cr in chatrooms]
        
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
        
        # 统计项目相关的聊天消息
        chat_query = ChatMessage.query.filter(
            ChatMessage.talker_name.in_(chatroom_names)
        )
        if conditions:
            chat_query = chat_query.filter(and_(*conditions))
        
        total_messages = chat_query.count()
        
        # 统计项目相关的文件
        file_query = FileRecord.query.filter(
            FileRecord.project_name == project.project_name
        )
        if start_date:
            file_query = file_query.filter(FileRecord.upload_time >= start_dt)
        if end_date:
            file_query = file_query.filter(FileRecord.upload_time <= end_dt)
        
        total_files = file_query.count()
        
        # 按日期统计消息数量
        daily_stats = db.session.query(
            func.date(ChatMessage.timestamp).label('date'),
            func.count(ChatMessage.id).label('message_count')
        ).filter(
            ChatMessage.talker_name.in_(chatroom_names)
        )
        
        if conditions:
            daily_stats = daily_stats.filter(and_(*conditions))
        
        daily_stats = daily_stats.group_by(
            func.date(ChatMessage.timestamp)
        ).order_by(
            func.date(ChatMessage.timestamp)
        ).all()
        
        daily_data = [
            {
                'date': str(stat.date),
                'message_count': stat.message_count
            }
            for stat in daily_stats
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'project': {
                    'id': project.id,
                    'project_name': project.project_name,
                    'description': project.description,
                    'status': project.status
                },
                'stats': {
                    'total_messages': total_messages,
                    'total_files': total_files,
                    'chatroom_count': len(chatroom_names),
                    'daily_message_stats': daily_data
                },
                'chatrooms': chatroom_names,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
        })
    except Exception as e:
        logger.error(f"获取项目统计失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500 