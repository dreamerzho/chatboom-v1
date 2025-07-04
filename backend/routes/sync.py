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
from backend.models.project import Project
from backend.models.chat import ChatMessage
from backend.models.file import FileRecord
from backend.models.employee import EmployeeMapping
from backend.chatlog_integration import chatlog_client
from backend.db import db
from backend.data_manager import data_manager
from backend.chatlog_processor import ChatLogProcessor

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
    data = request.get_json() or {}
    start_time = data.get('start_time') or data.get('start_date')
    end_time = data.get('end_time') or data.get('end_date')
    force_resync = data.get('force_resync', False)
    chatroom_names = data.get('chatroom_names', [])
    sync_type = data.get('sync_type', 'all')

    if not start_time or not end_time:
        def generate_error_response():
            error_entry = {
                "type": "error",
                "timestamp": datetime.now().isoformat(),
                "message": "必须指定起止日期"
            }
            yield f"data: {json.dumps(error_entry, ensure_ascii=False)}\n\n"
        return Response(stream_with_context(generate_error_response()), mimetype='text/event-stream')

    def generate_sync_data():
        def yield_log(message: str):
            log_entry = {
                "type": "log",
                "timestamp": datetime.now().isoformat(),
                "message": message
            }
            yield f"data: {json.dumps(log_entry, ensure_ascii=False)}\n\n"
        try:
            yield_log(f"✅ 开始为项目ID {project_id} 同步数据...")
            yield_log(f"📅 时间范围: {start_time} ~ {end_time}")
            yield_log(f"🔄 同步类型: {sync_type}")
            time.sleep(1)
            # 统一调用 data_manager.sync_project_data
            result = data_manager.sync_project_data(
                project_id=project_id,
                start_time=start_time,
                end_time=end_time,
                force=force_resync,
                chatroom_names=chatroom_names,
                sync_type=sync_type
            )
            if result.get('success'):
                yield_log("✅ 数据同步流程完成。")
            else:
                yield_log(f"❌ 同步失败: {result.get('error')}")
            final_report = {
                "project_id": project_id,
                "start_time": start_time,
                "end_time": end_time,
                "sync_type": sync_type,
                "success": result.get('success', False),
                "message": result.get('error', ''),
                "timestamp": datetime.now().isoformat()
            }
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
    return Response(stream_with_context(generate_sync_data()), mimetype='text/event-stream')

@sync_bp.route('/project/<int:project_id>', methods=['POST'])
def sync_project_data_by_id(project_id: int):
    """
    同步指定项目的聊天记录和文件数据（增强版）
    """
    try:
        data = request.get_json() or {}
        start_time = data.get('start_time') or data.get('start_date')
        end_time = data.get('end_time') or data.get('end_date')
        force_resync = data.get('force_resync', False)
        chatroom_names = data.get('chatroom_names', [])
        sync_type = data.get('sync_type', 'all')
        if not start_time or not end_time:
            return jsonify({'success': False, 'error': '必须指定起止日期'}), 400
        # 统一调用 data_manager.sync_project_data
        result = data_manager.sync_project_data(
            project_id=project_id,
            start_time=start_time,
            end_time=end_time,
            force=force_resync,
            chatroom_names=chatroom_names,
            sync_type=sync_type
        )
        if result.get('success'):
            return jsonify({'success': True, 'message': '同步成功', 'data': result.get('sync_result', {})})
        else:
            return jsonify({'success': False, 'error': result.get('error', '同步失败')}), 500
    except Exception as e:
        logger.error(f"同步项目数据失败: {str(e)}")
        return jsonify({'success': False, 'error': f'服务器内部错误: {str(e)}'}), 500

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