# 数据同步相关API路由
# 支持按时间段同步聊天记录、文件等数据，并返回同步进度和日志
# 集成 chatlog 工具，实现微信群聊数据的自动同步

from flask import Blueprint, request, jsonify, Response, stream_with_context
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any
import requests
import json
import time
import re

# 导入数据库模型和 chatlog 集成
from models.project import Project
from models.chat import ChatMessage
from models.file import FileRecord
from models.employee import EmployeeMapping
from chatlog_integration import chatlog_client
from backend.db import db
from data_manager import data_manager
from chatlog_processor import ChatLogProcessor

# 创建蓝图
sync_bp = Blueprint('sync', __name__, url_prefix='/api/v1/sync')
logger = logging.getLogger(__name__)

@sync_bp.route('/project', methods=['POST'])
def sync_project_data():
    """
    同步项目数据
    
    请求参数:
        project_name: 项目名称
        chatroom_names: 群聊名称列表
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        force_resync: 是否强制重新同步 (可选，默认false)
    
    返回:
        同步结果
    """
    try:
        data = request.get_json()
        
        # 验证必填参数
        required_fields = ['project_name', 'chatroom_names', 'start_date', 'end_date']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必填参数: {field}'
                }), 400
        
        project_name = data['project_name']
        chatroom_names = data['chatroom_names']
        start_date = data['start_date']
        end_date = data['end_date']
        force_resync = data.get('force_resync', False)
        
        # 验证参数格式
        if not isinstance(chatroom_names, list) or len(chatroom_names) == 0:
            return jsonify({
                'success': False,
                'error': 'chatroom_names 必须是非空列表'
            }), 400
        
        # 验证日期格式
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({
                'success': False,
                'error': '日期格式错误，请使用 YYYY-MM-DD 格式'
            }), 400
        
        # 验证日期范围
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        if start_dt > end_dt:
            return jsonify({
                'success': False,
                'error': '开始日期不能晚于结束日期'
            }), 400
        
        # 检查日期范围是否过大（超过90天）
        date_diff = (end_dt - start_dt).days
        if date_diff > 90:
            return jsonify({
                'success': False,
                'error': '日期范围不能超过90天'
            }), 400
        
        logger.info(f"开始同步项目数据: {project_name}, 群聊: {chatroom_names}, "
                   f"时间范围: {start_date} ~ {end_date}, 强制同步: {force_resync}")
        
        # 调用数据管理器进行同步
        result = data_manager.sync_project_data(
            project_name=project_name,
            chatroom_names=chatroom_names,
            start_date=start_date,
            end_date=end_date,
            force_resync=force_resync
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': f'项目 {project_name} 数据同步成功',
                'data': result['sync_result']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"同步项目数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@sync_bp.route('/employee-stats/<int:employee_id>', methods=['GET'])
def get_employee_stats(employee_id):
    """
    获取员工统计数据
    
    路径参数:
        employee_id: 员工ID
    
    查询参数:
        start_date: 开始日期 (可选)
        end_date: 结束日期 (可选)
    
    返回:
        员工统计数据
    """
    try:
        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 验证日期格式
        if start_date:
            try:
                datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'start_date 格式错误，请使用 YYYY-MM-DD 格式'
                }), 400
        
        if end_date:
            try:
                datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'end_date 格式错误，请使用 YYYY-MM-DD 格式'
                }), 400
        
        logger.info(f"获取员工 {employee_id} 统计数据，时间范围: {start_date} ~ {end_date}")
        
        # 调用数据管理器获取统计数据
        result = data_manager.get_employee_stats(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404
            
    except Exception as e:
        logger.error(f"获取员工统计失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@sync_bp.route('/project-stats/<int:project_id>', methods=['GET'])
def get_project_stats(project_id):
    """
    获取项目统计数据
    
    路径参数:
        project_id: 项目ID
    
    返回:
        项目统计数据
    """
    try:
        logger.info(f"获取项目 {project_id} 统计数据")
        
        # 调用数据管理器获取统计数据
        result = data_manager.get_project_stats(project_id=project_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404
            
    except Exception as e:
        logger.error(f"获取项目统计失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@sync_bp.route('/unmapped-senders', methods=['GET'])
def get_unmapped_senders():
    """
    获取未映射的微信用户列表
    
    返回:
        未映射用户列表
    """
    try:
        logger.info("获取未映射的微信用户列表")
        
        # 调用数据管理器获取未映射用户
        result = data_manager.get_unmapped_senders()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"获取未映射用户列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@sync_bp.route('/employee-mappings', methods=['POST'])
def batch_add_employee_mappings():
    """
    批量添加员工映射
    
    请求参数:
        mappings: 员工映射列表
            - wechat_nickname: 微信昵称
            - real_name: 真实姓名
            - position: 职位
            - name_abbreviation: 姓名缩写
            - role: 角色 (可选，默认"内部员工")
    
    返回:
        批量添加结果
    """
    try:
        data = request.get_json()
        
        # 验证必填参数
        if 'mappings' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必填参数: mappings'
            }), 400
        
        mappings = data['mappings']
        
        if not isinstance(mappings, list) or len(mappings) == 0:
            return jsonify({
                'success': False,
                'error': 'mappings 必须是非空列表'
            }), 400
        
        logger.info(f"批量添加员工映射，数量: {len(mappings)}")
        
        # 调用数据管理器批量添加
        result = data_manager.batch_add_employee_mappings(mappings)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        logger.error(f"批量添加员工映射失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@sync_bp.route('/status', methods=['GET'])
def get_sync_status():
    """
    获取同步状态
    
    返回:
        系统同步状态信息
    """
    try:
        # 获取基本统计信息
        project_count = Project.query.count()
        employee_count = EmployeeMapping.query.count()
        file_count = FileRecord.query.count()
        message_count = ChatMessage.query.count()
        
        # 获取最近同步的项目
        recent_projects = Project.query.order_by(Project.updated_at.desc()).limit(5).all()
        
        # 获取活跃员工
        from sqlalchemy import func
        active_employees = db.session.query(
            ChatMessage.sender_name,
            func.count(ChatMessage.id).label('message_count')
        ).group_by(ChatMessage.sender_name).order_by(
            func.count(ChatMessage.id).desc()
        ).limit(10).all()
        
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'project_count': project_count,
                    'employee_count': employee_count,
                    'file_count': file_count,
                    'message_count': message_count
                },
                'recent_projects': [
                    {
                        'id': project.id,
                        'name': project.project_name,
                        'status': project.status,
                        'updated_at': project.updated_at.isoformat() if project.updated_at else None
                    } for project in recent_projects
                ],
                'active_employees': [
                    {
                        'sender_name': sender_name,
                        'message_count': message_count
                    } for sender_name, message_count in active_employees
                ],
                'last_updated': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"获取同步状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@sync_bp.route('/chatrooms', methods=['GET'], strict_slashes=False)
def get_chatrooms():
    """
    获取所有可用的微信群聊列表
    from chatlog 服务获取群聊信息
    """
    try:
        chatrooms = chatlog_client.get_chatrooms()
        logger.info(f'chatlog_client.get_chatrooms() 返回: {chatrooms}')
        return jsonify({
            'success': True,
            'data': chatrooms
        })
    except Exception as e:
        import traceback
        logger.error(f"获取群聊列表失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500  # 返回500，避免CORS问题

@sync_bp.route('/project/<int:project_id>/stream', methods=['POST'])
def sync_project_data_stream(project_id: int):
    """
    通过流式响应，实时同步指定项目的数据
    """
    # 从请求体获取参数
    data = request.get_json() or {}
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    sync_type = data.get('sync_type', 'all')
    chatroom_names = data.get('chatroom_names', [])
    force_resync = data.get('force_resync', False)
    
    # 参数校验
    if not start_date or not end_date:
        def generate_error_response():
            error_entry = {
                "type": "error",
                "timestamp": datetime.now().isoformat(),
                "message": "必须指定起止日期"
            }
            yield f"data: {json.dumps(error_entry, ensure_ascii=False)}\n\n"
        return Response(stream_with_context(generate_error_response()), mimetype='text/event-stream')

    def generate_sync_data():
        # 发送日志的辅助函数
        def yield_log(message: str):
            log_entry = {
                "type": "log",
                "timestamp": datetime.now().isoformat(),
                "message": message
            }
            # 使用\n\n作为分隔符
            yield f"data: {json.dumps(log_entry, ensure_ascii=False)}\n\n"

        try:
            yield_log(f"✅ 开始为项目ID {project_id} 同步数据...")
            yield_log(f"📅 时间范围: {start_date} ~ {end_date}")
            yield_log(f"🔄 同步类型: {sync_type}")

            time.sleep(1) # 暂停一下，让前端能渲染出第一条日志

            # 1. 获取项目信息
            project = Project.query.get(project_id)
            if not project:
                yield_log(f"❌ 项目ID {project_id} 不存在")
                return
            
            yield_log(f"📋 项目名称: {project.project_name}")

            # 2. 确定要同步的群聊列表
            if chatroom_names:
                target_chatrooms = chatroom_names
                yield_log(f"🎯 指定群聊: {', '.join(target_chatrooms)}")
            else:
                target_chatrooms = []
                project_chatrooms = project.chatrooms.all()
                for chatroom in project_chatrooms:
                    target_chatrooms.append(chatroom.chatroom_name)
                yield_log(f"🎯 项目群聊: {', '.join(target_chatrooms)}")
            
            if not target_chatrooms:
                yield_log("❌ 项目未配置群聊，请先配置群聊信息")
                return

            # 3. 初始化处理器并执行同步
            processor = ChatLogProcessor(project_id=project_id, yield_log=yield_log)
            
            # 4. 执行核心处理逻辑
            result = processor.process_chatlogs(start_date=start_date, end_date=end_date)

            # 5. 准备最终的同步结果报告
            final_report = {
                "project_id": project_id,
                "project_name": project.project_name,
                "start_date": start_date,
                "end_date": end_date,
                "sync_type": sync_type,
                "total_chatrooms": len(target_chatrooms),
                "total_messages": result.get("total_messages", 0),
                "total_files": result.get("total_files", 0),
                "success": result.get("success", False),
                "message": result.get("message", ""),
                "timestamp": datetime.now().isoformat()
            }

            yield_log("✅ 数据同步流程完成。")

            # 6. 发送最终结果
            result_entry = {
                "type": "result",
                "data": final_report
            }
            yield f"data: {json.dumps(result_entry, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"流式同步过程中发生严重错误: {e}", exc_info=True)
            error_entry = {
                "type": "error",
                "timestamp": datetime.now().isoformat(),
                "message": f"处理失败: {str(e)}"
            }
            yield f"data: {json.dumps(error_entry, ensure_ascii=False)}\n\n"

    # 使用 stream_with_context 确保在流式传输期间应用上下文仍然可用
    return Response(stream_with_context(generate_sync_data()), mimetype='text/event-stream')

@sync_bp.route('/project/<int:project_id>', methods=['POST'])
def sync_project_data_by_id(project_id: int):
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
            # 使用指定的群聊昵称
            target_chatrooms = chatroom_names
        else:
            # 使用项目配置的群聊昵称
            target_chatrooms = []
            project_chatrooms = project.chatrooms.all()
            for chatroom in project_chatrooms:
                # 只用 chatroom_name（群昵称）做匹配
                target_chatrooms.append(chatroom.chatroom_name)
        
        if not target_chatrooms:
            return jsonify({
                'success': False, 
                'error': '项目未配置群聊，请先配置群聊信息'
            }), 400
        
        # 获取员工列表（用于人员匹配）
        employees = []
        try:
            employee_list = EmployeeMapping.query.all()
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
                            # 检查是否已存在（基于message_id去重）
                            existing_msg = ChatMessage.query.filter_by(
                                message_id=msg_data.get('seq'),
                                project_id=project_id
                            ).first()
                            if not existing_msg:
                                chat_msg = ChatMessage(
                                    message_id=msg_data.get('seq'),  # 使用 seq 作为 message_id
                                    talker_name=msg_data.get('talker_name'),
                                    sender_name=msg_data.get('sender_name'),
                                    message_type=str(msg_data.get('type', '文本')),
                                    content=msg_data.get('content'),
                                    timestamp=datetime.fromtimestamp(msg_data.get('time', 0)) if msg_data.get('time') else datetime.utcnow(),
                                    project_id=project_id,
                                    created_at=datetime.utcnow()
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
            return sync_project_data_by_id(project_id)
        
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

@sync_bp.route('/chatlog-health', methods=['GET'])
def chatlog_health():
    """
    代理chatlog健康检查，前端可用此接口判断服务状态
    只要 /api/v1/chatroom 返回200且内容非空即为"正常"
    """
    try:
        resp = requests.get("http://127.0.0.1:5030/api/v1/chatroom", params={"format": "json"}, timeout=5)
        if resp.status_code == 200 and resp.text and resp.text.strip() not in ('', '{}', '[]'):
            return jsonify({"status": "ok", "message": "chatlog服务正常"}), 200
        else:
            return jsonify({"status": "error", "message": "chatlog服务无数据或异常"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"无法连接chatlog服务: {str(e)}"}), 500 