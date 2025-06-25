# 聊天记录相关的API路由
# 这个文件包含所有与聊天记录相关的API端点，包括聊天记录导入、查询、分析等功能

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
from sqlalchemy import func, and_, desc
import logging
import requests
# from config import CHATLOG_BASE_URL, CHATLOG_API_KEY # 移除直接导入
from db import db
from models import ChatMessage, EmployeeMapping

# 创建聊天记录蓝图
chatlog_bp = Blueprint('chatlog', __name__, url_prefix='/api/v1/chatlog')

# 配置日志
logger = logging.getLogger(__name__)

@chatlog_bp.route('/import', methods=['POST'])
def import_chatlog():
    """
    导入聊天记录
    请求体: JSON格式，包含导入参数
    返回: 导入结果
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '缺少请求数据'}), 400
        
        # 验证必填字段
        required_fields = ['chatroom_name', 'start_date', 'end_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'缺少必填字段: {field}'}), 400
        
        # 调用chatlog工具API - 使用正确的API格式
        chatroom_name = data['chatroom_name']
        start_date = data['start_date']
        end_date = data['end_date']
        
        # 构建API URL
        api_url = f"{CHATLOG_BASE_URL}/api/v1/chatlog"
        params = {
            'talker': chatroom_name,
            'time': f"{start_date},{end_date}"
        }
        
        response = requests.get(
            api_url,
            params=params,
            timeout=30
        )
        
        if response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Chatlog工具API调用失败: {response.text}'
            }), 500
        
        # 解析聊天记录数据 - chatlog服务返回的是纯文本格式
        chatlog_text = response.text
        if not chatlog_text or chatlog_text.startswith('"time range not found'):
            return jsonify({
                'success': False,
                'error': f'指定时间范围内没有找到聊天记录: {chatlog_text}'
            }), 404
        
        # 解析聊天记录文本格式
        messages_data = []
        lines = chatlog_text.strip().split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line and not line.startswith('"'):
                # 解析格式: "发送者昵称(发送者ID) 时间"
                # 例如: "张大妃●﹏●(zhangliya-peter) 15:55:45"
                try:
                    # 查找最后一个空格，分割发送者信息和时间
                    last_space_idx = line.rfind(' ')
                    if last_space_idx > 0:
                        sender_info = line[:last_space_idx]
                        time_str = line[last_space_idx + 1:]
                        
                        # 解析发送者信息: "昵称(ID)"
                        paren_idx = sender_info.rfind('(')
                        if paren_idx > 0:
                            sender_name = sender_info[:paren_idx]
                            sender_id = sender_info[paren_idx + 1:-1]  # 去掉括号
                            
                            # 获取下一行作为消息内容
                            content = ""
                            if i + 1 < len(lines):
                                content = lines[i + 1].strip()
                                i += 1  # 跳过内容行
                            
                            # 构建完整的日期时间
                            full_time = f"2025-06-17 {time_str}:00"
                            
                            msg_data = {
                                'time': full_time,
                                'talkerName': chatroom_name,
                                'senderName': sender_name,
                                'senderId': sender_id,
                                'type': 1,  # 默认为文本消息
                                'content': content,
                                'id': f"{full_time}_{sender_id}_{hash(line)}"  # 生成唯一ID
                            }
                            messages_data.append(msg_data)
                except Exception as e:
                    logger.warning(f"解析聊天记录行失败: {line}, 错误: {str(e)}")
            i += 1
        
        imported_count = 0
        skipped_count = 0
        
        for msg_data in messages_data:
            try:
                # 检查消息是否已存在
                existing_msg = ChatMessage.query.filter_by(
                    message_id=msg_data.get('id'),
                    talker_name=msg_data.get('talkerName'),
                    sender_name=msg_data.get('senderName')
                ).first()
                
                if existing_msg:
                    skipped_count += 1
                    continue
                
                # 解析时间戳
                try:
                    timestamp = datetime.fromisoformat(msg_data.get('time').replace('Z', '+00:00'))
                except:
                    timestamp = datetime.utcnow()
                
                # 创建新的聊天消息记录
                new_message = ChatMessage(
                    message_id=msg_data.get('id') or msg_data.get('seq'),  # 修复：确保唯一标识赋值
                    talker_name=msg_data.get('talkerName'),
                    sender_name=msg_data.get('senderName'),
                    timestamp=timestamp,
                    message_type=msg_data.get('type'),
                    content=msg_data.get('content'),
                    created_at=datetime.utcnow()
                )
                
                db.session.add(new_message)
                imported_count += 1
                
            except Exception as e:
                logger.error(f"处理消息数据失败: {str(e)}, 数据: {msg_data}")
                skipped_count += 1
                continue
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'imported_count': imported_count,
                'skipped_count': skipped_count,
                'total_processed': len(messages_data),
                'chatroom_name': data['chatroom_name'],
                'period': {
                    'start_date': data['start_date'],
                    'end_date': data['end_date']
                }
            },
            'message': f'成功导入 {imported_count} 条聊天记录'
        })
    except Exception as e:
        logger.error(f"导入聊天记录失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@chatlog_bp.route('/messages', methods=['GET'])
def get_chat_messages():
    """
    获取聊天消息列表
    查询参数: chatroom_name, sender_name, start_date, end_date, page, per_page (可选)
    返回: 聊天消息列表
    """
    try:
        # 获取查询参数
        chatroom_name = request.args.get('chatroom_name')
        sender_name = request.args.get('sender_name')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # 构建查询
        query = ChatMessage.query
        
        # 添加过滤条件
        if chatroom_name:
            query = query.filter(ChatMessage.talker_name.like(f'%{chatroom_name}%'))
        if sender_name:
            query = query.filter(ChatMessage.sender_name.like(f'%{sender_name}%'))
        
        # 日期过滤
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(ChatMessage.timestamp >= start_dt)
            except ValueError:
                return jsonify({'success': False, 'error': '开始日期格式错误'}), 400
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(ChatMessage.timestamp <= end_dt)
            except ValueError:
                return jsonify({'success': False, 'error': '结束日期格式错误'}), 400
        
        # 按时间倒序排列
        query = query.order_by(desc(ChatMessage.timestamp))
        
        # 分页
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        messages_list = []
        for message in pagination.items:
            messages_list.append({
                'id': message.id,
                'talker_name': message.talker_name,
                'sender_name': message.sender_name,
                'type': message.type,
                'content': message.content,
                'timestamp': message.timestamp.isoformat() if message.timestamp else None,
                'created_at': message.created_at.isoformat() if message.created_at else None
            })
        
        return jsonify({
            'success': True,
            'data': {
                'messages': messages_list,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                }
            }
        })
    except Exception as e:
        logger.error(f"获取聊天消息失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@chatlog_bp.route('/stats', methods=['GET'])
def get_chat_stats():
    """
    获取聊天统计信息
    查询参数: chatroom_name, start_date, end_date (可选)
    返回: 聊天统计数据
    """
    try:
        # 获取查询参数
        chatroom_name = request.args.get('chatroom_name')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 构建查询条件
        conditions = []
        if chatroom_name:
            conditions.append(ChatMessage.talker_name.like(f'%{chatroom_name}%'))
        
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
        total_query = ChatMessage.query
        if conditions:
            total_query = total_query.filter(and_(*conditions))
        total_messages = total_query.count()
        
        # 按聊天室统计
        chatroom_stats = db.session.query(
            ChatMessage.talker_name,
            func.count(ChatMessage.id).label('message_count')
        )
        if conditions:
            chatroom_stats = chatroom_stats.filter(and_(*conditions))
        chatroom_stats = chatroom_stats.group_by(
            ChatMessage.talker_name
        ).order_by(
            desc(func.count(ChatMessage.id))
        ).limit(10).all()
        
        chatroom_data = [
            {
                'chatroom_name': stat.talker_name,
                'message_count': stat.message_count
            }
            for stat in chatroom_stats
        ]
        
        # 按发送者统计
        sender_stats = db.session.query(
            ChatMessage.sender_name,
            func.count(ChatMessage.id).label('message_count')
        )
        if conditions:
            sender_stats = sender_stats.filter(and_(*conditions))
        sender_stats = sender_stats.group_by(
            ChatMessage.sender_name
        ).order_by(
            desc(func.count(ChatMessage.id))
        ).limit(10).all()
        
        sender_data = [
            {
                'sender_name': stat.sender_name,
                'message_count': stat.message_count
            }
            for stat in sender_stats
        ]
        
        # 按消息类型统计
        type_stats = db.session.query(
            ChatMessage.type,
            func.count(ChatMessage.id).label('message_count')
        )
        if conditions:
            type_stats = type_stats.filter(and_(*conditions))
        type_stats = type_stats.group_by(
            ChatMessage.type
        ).all()
        
        type_data = [
            {
                'type': stat.type,
                'message_count': stat.message_count
            }
            for stat in type_stats
        ]
        
        # 按日期统计
        daily_stats = db.session.query(
            func.date(ChatMessage.timestamp).label('date'),
            func.count(ChatMessage.id).label('message_count')
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
                'total_messages': total_messages,
                'chatroom_distribution': chatroom_data,
                'sender_distribution': sender_data,
                'type_distribution': type_data,
                'daily_message_stats': daily_data,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'chatroom_name': chatroom_name
                }
            }
        })
    except Exception as e:
        logger.error(f"获取聊天统计失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@chatlog_bp.route('/chatrooms', methods=['GET'])
def get_chatrooms():
    """
    获取聊天室列表
    返回: 聊天室列表
    """
    try:
        # 获取所有聊天室
        chatrooms = db.session.query(
            ChatMessage.talker_name,
            func.count(ChatMessage.id).label('message_count'),
            func.max(ChatMessage.timestamp).label('last_message_time')
        ).group_by(
            ChatMessage.talker_name
        ).order_by(
            desc(func.count(ChatMessage.id))
        ).all()
        
        chatroom_list = []
        for chatroom in chatrooms:
            chatroom_list.append({
                'name': chatroom.talker_name,
                'message_count': chatroom.message_count,
                'last_message_time': chatroom.last_message_time.isoformat() if chatroom.last_message_time else None
            })
        
        return jsonify({
            'success': True,
            'data': chatroom_list
        })
    except Exception as e:
        logger.error(f"获取聊天室列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@chatlog_bp.route('/senders', methods=['GET'])
def get_senders():
    """
    获取发送者列表
    返回: 发送者列表
    """
    try:
        # 获取所有发送者
        senders = db.session.query(
            ChatMessage.sender_name,
            func.count(ChatMessage.id).label('message_count'),
            func.max(ChatMessage.timestamp).label('last_message_time')
        ).group_by(
            ChatMessage.sender_name
        ).order_by(
            desc(func.count(ChatMessage.id))
        ).all()
        
        sender_list = []
        for sender in senders:
            sender_list.append({
                'name': sender.sender_name,
                'message_count': sender.message_count,
                'last_message_time': sender.last_message_time.isoformat() if sender.last_message_time else None
            })
        
        return jsonify({
            'success': True,
            'data': sender_list
        })
    except Exception as e:
        logger.error(f"获取发送者列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500