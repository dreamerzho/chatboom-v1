# 数据同步相关API路由
# 支持按时间段同步聊天记录、文件等数据，并返回同步进度和日志
# 集成 chatlog 工具，实现微信群聊数据的自动同步

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any

# 导入数据库模型和 chatlog 集成
from models.project import Project
from models.chat import ChatMessage
from models.file import FileRecord
from models.employee import Employee
from chatlog_integration import chatlog_client
from db import db

sync_bp = Blueprint('sync', __name__, url_prefix='/api/v1/sync')
logger = logging.getLogger(__name__)

@sync_bp.route('/status', methods=['GET'])
def get_sync_status():
    """
    获取 chatlog 服务状态
    用于检查 chatlog 服务是否正常运行
    """
    try:
        status = chatlog_client.check_service_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        logger.error(f"获取同步状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sync_bp.route('/chatrooms', methods=['GET'])
def get_chatrooms():
    """
    获取所有可用的微信群聊列表
    从 chatlog 服务获取群聊信息
    """
    try:
        chatrooms = chatlog_client.get_chatrooms()
        return jsonify({
            'success': True,
            'data': chatrooms
        })
    except Exception as e:
        logger.error(f"获取群聊列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sync_bp.route('/project/<int:project_id>', methods=['POST'])
def sync_project_data(project_id: int):
    """
    同步指定项目的聊天记录和文件数据（增强版）
    
    参数:
        project_id: 项目ID
    请求体:
        - start_date: 同步起始日期（必填，格式：YYYY-MM-DD）
        - end_date: 同步结束日期（必填，格式：YYYY-MM-DD）
        - sync_type: 同步类型，可选 all/chat/files，默认 all
        - chatroom_names: 指定群聊名称列表（可选，不指定则同步项目所有群聊）
        - force_resync: 是否强制重新同步（可选，默认false）
    
    返回:
        同步进度、日志和结果统计
    """
    try:
        # 获取请求参数
        data = request.get_json() or {}
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        sync_type = data.get('sync_type', 'all')
        chatroom_names = data.get('chatroom_names', [])
        force_resync = data.get('force_resync', False)
        
        # 参数校验
        if not start_date or not end_date:
            return jsonify({
                'success': False, 
                'error': '必须指定起止日期'
            }), 400
        
        # 验证日期格式
        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            if start_dt > end_dt:
                return jsonify({
                    'success': False, 
                    'error': '起始日期不能晚于结束日期'
                }), 400
        except Exception:
            return jsonify({
                'success': False, 
                'error': '日期格式错误，应为YYYY-MM-DD'
            }), 400
        
        # 获取项目信息
        project = Project.query.get(project_id)
        if not project:
            return jsonify({
                'success': False, 
                'error': '项目不存在'
            }), 404
        
        # 确定要同步的群聊列表
        if chatroom_names:
            # 使用指定的群聊名称
            target_chatrooms = chatroom_names
        else:
            # 使用项目配置的群聊
            target_chatrooms = []
            # 从 ProjectChatroom 关联表获取群聊信息
            project_chatrooms = project.chatrooms.all()
            for chatroom in project_chatrooms:
                target_chatrooms.append(chatroom.chatroom_name)
        
        if not target_chatrooms:
            return jsonify({
                'success': False, 
                'error': '项目未配置群聊，请先配置群聊信息'
            }), 400
        
        # 获取员工列表（用于人员匹配）
        employees = []
        try:
            employee_list = Employee.query.all()
            for emp in employee_list:
                employees.append({
                    'id': emp.id,
                    'real_name': emp.real_name,
                    'wechat_nickname': emp.wechat_nickname,
                    'name_abbreviation': emp.name_abbreviation,
                    'position': emp.position
                })
            logger.info(f"获取到 {len(employees)} 个员工信息用于匹配")
        except Exception as e:
            logger.warning(f"获取员工信息失败: {str(e)}，将跳过人员匹配")
        
        # 开始同步
        sync_log = []
        sync_results = {
            'project_id': project_id,
            'project_name': project.project_name,
            'start_date': start_date,
            'end_date': end_date,
            'sync_type': sync_type,
            'force_resync': force_resync,
            'total_chatrooms': len(target_chatrooms),
            'success_count': 0,
            'failed_count': 0,
            'total_messages': 0,
            'processed_messages': 0,
            'duplicate_messages': 0,
            'file_messages': 0,
            'text_messages': 0,
            'matched_employees': 0,
            'unmatched_employees': 0,
            'total_files': 0,
            'details': [],
            'employee_stats': {},
            'timestamp': datetime.now().isoformat()
        }
        
        sync_log.append(f"开始同步项目：{project.project_name}")
        sync_log.append(f"时间范围：{start_date} ~ {end_date}")
        sync_log.append(f"同步类型：{sync_type}")
        sync_log.append(f"强制重新同步：{force_resync}")
        sync_log.append(f"目标群聊数量：{len(target_chatrooms)}")
        sync_log.append(f"员工匹配数量：{len(employees)}")
        
        # 同步聊天记录
        if sync_type in ('all', 'chat'):
            sync_log.append("开始同步聊天记录...")
            
            # 调用 chatlog 集成进行同步（增强版）
            chatlog_results = chatlog_client.sync_project_chatlogs(
                project_name=project.project_name,
                chatroom_names=target_chatrooms,
                start_date=start_date,
                end_date=end_date,
                employees=employees,
                force_resync=force_resync
            )
            
            # 处理聊天记录同步结果
            if chatlog_results.get('status') == 'error':
                sync_log.append(f"聊天记录同步失败：{chatlog_results.get('message')}")
                sync_results['failed_count'] = len(target_chatrooms)
            else:
                # 更新统计信息
                sync_results['success_count'] = chatlog_results.get('success_count', 0)
                sync_results['failed_count'] = chatlog_results.get('failed_count', 0)
                sync_results['total_messages'] = chatlog_results.get('total_messages', 0)
                sync_results['processed_messages'] = chatlog_results.get('processed_messages', 0)
                sync_results['duplicate_messages'] = chatlog_results.get('duplicate_messages', 0)
                sync_results['file_messages'] = chatlog_results.get('file_messages', 0)
                sync_results['text_messages'] = chatlog_results.get('text_messages', 0)
                sync_results['matched_employees'] = chatlog_results.get('matched_employees', 0)
                sync_results['unmatched_employees'] = chatlog_results.get('unmatched_employees', 0)
                sync_results['employee_stats'] = chatlog_results.get('employee_stats', {})
                sync_results['details'].extend(chatlog_results.get('details', []))
                
                sync_log.append(f"聊天记录同步完成：成功 {sync_results['success_count']} 个群聊，失败 {sync_results['failed_count']} 个群聊")
                sync_log.append(f"总计获取 {sync_results['total_messages']} 条消息，处理 {sync_results['processed_messages']} 条，去重 {sync_results['duplicate_messages']} 条")
                sync_log.append(f"文件消息 {sync_results['file_messages']} 个，文本消息 {sync_results['text_messages']} 个")
                sync_log.append(f"人员匹配成功 {sync_results['matched_employees']} 个，未匹配 {sync_results['unmatched_employees']} 个")
                
                # 保存聊天记录到数据库
                try:
                    chat_messages = chatlog_results.get('chat_messages', [])
                    if chat_messages:
                        for msg_data in chat_messages:
                            # 检查是否已存在（基于seq去重）
                            existing_msg = ChatMessage.query.filter_by(seq=msg_data['seq']).first()
                            if not existing_msg:
                                chat_msg = ChatMessage(
                                    seq=msg_data['seq'],
                                    time=msg_data['time'],
                                    talker=msg_data['talker'],
                                    talker_name=msg_data['talker_name'],
                                    sender=msg_data['sender'],
                                    sender_name=msg_data['sender_name'],
                                    is_self=msg_data['is_self'],
                                    type=msg_data['type'],
                                    sub_type=msg_data['sub_type'],
                                    content=msg_data['content'],
                                    employee_id=msg_data.get('employee_id')
                                )
                                db.session.add(chat_msg)
                        
                        db.session.commit()
                        sync_log.append(f"成功保存 {len(chat_messages)} 条聊天记录到数据库")
                    else:
                        sync_log.append("无聊天记录需要保存")
                except Exception as e:
                    logger.error(f"保存聊天记录失败: {str(e)}")
                    sync_log.append(f"保存聊天记录失败: {str(e)}")
                
                # 保存文件记录到数据库
                try:
                    file_records = chatlog_results.get('file_records', [])
                    if file_records:
                        for file_data in file_records:
                            # 检查是否已存在（基于文件名和上传时间）
                            existing_file = FileRecord.query.filter_by(
                                original_name=file_data['original_name'],
                                upload_time=file_data['upload_time']
                            ).first()
                            if not existing_file:
                                file_record = FileRecord(
                                    original_name=file_data['original_name'],
                                    standardized_name=file_data['standardized_name'],
                                    project_name=file_data['project_name'],
                                    work_order=file_data['work_order'],
                                    workload=file_data['workload'],
                                    author_abbreviation=file_data['author_abbreviation'],
                                    version=file_data['version'],
                                    file_extension=file_data['file_extension'],
                                    upload_time=file_data['upload_time'],
                                    uploader=file_data['uploader'],
                                    file_size=file_data['file_size'],
                                    status=file_data['status']
                                )
                                db.session.add(file_record)
                        
                        db.session.commit()
                        sync_log.append(f"成功保存 {len(file_records)} 个文件记录到数据库")
                    else:
                        sync_log.append("无文件记录需要保存")
                except Exception as e:
                    logger.error(f"保存文件记录失败: {str(e)}")
                    sync_log.append(f"保存文件记录失败: {str(e)}")
        
        # 同步文件数据
        if sync_type in ('all', 'files'):
            sync_log.append("开始同步文件数据...")
            
            # 统计指定时间段内的文件数量
            file_count = FileRecord.query.filter(
                FileRecord.project_name == project.project_name,
                FileRecord.created_at >= start_dt,
                FileRecord.created_at <= end_dt
            ).count()
            
            sync_results['total_files'] = file_count
            sync_log.append(f"文件数据同步完成：找到 {file_count} 个文件")
        
        sync_log.append("同步完成！")
        
        return jsonify({
            'success': True,
            'data': {
                'results': sync_results,
                'log': sync_log
            }
        })
        
    except Exception as e:
        logger.error(f"同步项目数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sync_bp.route('/', methods=['POST'])
def sync_data():
    """
    通用数据同步接口
    支持按时间段、类型同步聊天记录/文件等
    
    请求体: JSON，参数如下：
      - start_date: 同步起始日期（必填，格式：YYYY-MM-DD）
      - end_date: 同步结束日期（必填，格式：YYYY-MM-DD）
      - sync_type: 同步类型，可选 all/chat/files，默认 all
      - project_id: 可选，指定项目ID
      - chatroom_names: 可选，指定群聊名称列表
    
    返回：同步进度、日志
    """
    try:
        data = request.get_json()
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        sync_type = data.get('sync_type', 'all')
        project_id = data.get('project_id')
        chatroom_names = data.get('chatroom_names', [])
        
        # 参数校验
        if not start_date or not end_date:
            return jsonify({
                'success': False, 
                'error': '必须指定起止日期'
            }), 400
        
        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
        except Exception:
            return jsonify({
                'success': False, 
                'error': '日期格式错误，应为YYYY-MM-DD'
            }), 400
        
        # 如果有指定项目ID，调用项目同步接口
        if project_id:
            return sync_project_data(project_id)
        
        # 否则进行全局同步
        sync_log = []
        progress = 0
        total = 1
        
        sync_log.append(f"开始全局同步，类型: {sync_type}，范围: {start_date} ~ {end_date}")
        
        if sync_type in ('all', 'chat'):
            sync_log.append("同步聊天记录...")
            
            # 获取所有群聊
            all_chatrooms = chatlog_client.get_chatrooms()
            if all_chatrooms:
                # 如果指定了群聊名称，则只同步指定的群聊
                if chatroom_names:
                    target_chatrooms = [room for room in all_chatrooms if room.get('name') in chatroom_names]
                else:
                    target_chatrooms = all_chatrooms
                
                chatroom_names_list = [room.get('name') for room in target_chatrooms]
                
                # 执行同步
                chatlog_results = chatlog_client.sync_project_chatlogs(
                    project_name="全局同步",
                    chatroom_names=chatroom_names_list,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if chatlog_results.get('status') == 'error':
                    sync_log.append(f"聊天记录同步失败：{chatlog_results.get('message')}")
                else:
                    sync_log.append(f"聊天记录同步完成：成功 {chatlog_results.get('success_count', 0)} 个群聊，获取 {chatlog_results.get('total_messages', 0)} 条消息")
            else:
                sync_log.append("未找到可用的群聊")
            
            progress += 1
        
        if sync_type in ('all', 'files'):
            sync_log.append("同步文件数据...")
            # TODO: 实现文件数据同步逻辑
            progress += 1
        
        sync_log.append("同步完成！")
        
        return jsonify({
            'success': True,
            'data': {
                'progress': progress,
                'total': total,
                'log': sync_log
            }
        })
        
    except Exception as e:
        logger.error(f"数据同步失败: {str(e)}")
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@sync_bp.route('/test', methods=['GET'])
def test_chatlog_connection():
    """
    测试 chatlog 连接
    用于验证 chatlog 服务是否可用
    """
    try:
        # 检查服务状态
        status = chatlog_client.check_service_status()
        
        # 获取群聊列表
        chatrooms = chatlog_client.get_chatrooms()
        
        return jsonify({
            'success': True,
            'data': {
                'status': status,
                'chatrooms_count': len(chatrooms),
                'chatrooms_sample': chatrooms[:5] if chatrooms else []  # 返回前5个群聊作为示例
            }
        })
    except Exception as e:
        logger.error(f"测试 chatlog 连接失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 