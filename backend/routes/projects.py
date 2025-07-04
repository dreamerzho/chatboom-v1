# 项目管理相关的API路由
# 这个文件包含所有与项目管理相关的API端点，包括项目创建、查询、统计等功能

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import logging
from sqlalchemy import func, and_
from backend.db import db
from backend.models import Project, ProjectChatroom, ChatMessage, FileRecord, EmployeeMapping
from backend.models.workload import WorkloadRecord
from backend.models.project_health import ProjectHealthStats
from backend.models.risk_event import RiskEvent
from itertools import groupby
from backend.analysis_service import AnalysisService, update_all_project_summaries
from backend.models.keyword import KeywordAnalysis
from backend.models.asset import Asset
from backend.models.project_summary import ProjectSummary

# 创建蓝图
projects_bp = Blueprint('projects', __name__, url_prefix='/api/v1/projects')

# 配置日志
logger = logging.getLogger(__name__)

@projects_bp.route('/', methods=['GET'])
def get_projects():
    """
    获取所有项目列表，直接从ProjectSummary表读取
    """
    try:
        summaries = ProjectSummary.query.all()
        project_list = []
        for s in summaries:
            d = s.to_dict()
            # 兼容前端ProjectCard结构，补充status字段
            project_list.append({
                'id': d['project_id'],
                'project_name': d['project_name'],
                'status': d.get('status', 'active'),
                'total_files': d['total_files'],
                'total_workload_we': d['total_workload_we'],
                'health_score': d['health_score'],
                'rework_rate': d['rework_rate'],
                'avg_internal_revisions': d['avg_internal_revisions'],
                'avg_customer_revisions': d['avg_customer_revisions'],
                'risk_events_count': d['risk_events_count'],
                'positive_feedback_count': d['positive_feedback_count'],
                'negative_feedback_count': d['negative_feedback_count'],
                'last_updated': d['last_updated']
            })
        return jsonify({'success': True, 'data': project_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@projects_bp.route('/', methods=['POST'])
def create_project():
    """
    创建新项目
    请求体: JSON格式，包含项目信息
    返回: 创建结果
    """
    try:
        data = request.get_json(silent=True) or request.form.to_dict() or {}
        logger.info(f"[create_project] 收到原始数据: {data}, 类型: {type(data)}")
        if not data:
            logger.error(f"[create_project] data为空，request.data={request.data}, request.form={request.form}, request.content_type={request.content_type}")
            return jsonify({'success': False, 'error': '缺少请求数据'}), 400
        
        # 验证必填字段
        if 'project_name' not in data or not data['project_name']:
            return jsonify({'success': False, 'error': '缺少项目名称'}), 400
        
        # 检查是否已存在相同名称的项目
        existing_project = Project.query.filter_by(project_name=data['project_name']).first()
        logger.info(f"[create_project] 唯一性校验: project_name={data['project_name']}，existing_project={existing_project}")
        if existing_project:
            return jsonify({'success': False, 'error': '项目名称已存在'}), 400
        
        # 兼容前端多余字段，保证description/status有默认值
        description = data.get('description', '')
        status = data.get('status', 'active')
        # 创建新项目
        new_project = Project(
            project_name=data['project_name'],
            description=description,
            status=status,
            start_date=datetime.fromisoformat(data['start_date']) if data.get('start_date') else None,
            end_date=datetime.fromisoformat(data['end_date']) if data.get('end_date') else None,
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_project)
        db.session.commit()
        # 新增：每次新建项目后立即刷新聚合表
        update_all_project_summaries()
        
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
        import traceback
        tb = traceback.format_exc()
        logger.error(f"创建项目失败: {str(e)}\n{tb}")
        return jsonify({'success': False, 'error': str(e), 'traceback': tb}), 500

@projects_bp.route('/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """
    获取单个项目详情（补全聚合统计字段）
    参数: project_id - 项目ID
    返回: 项目详情，包含统计卡片、健康分、风险、关键词分析等
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
        # 自动聚合weData，直接用workload_records表
        records = WorkloadRecord.query.filter_by(project_id=project.id).all()
        color_list = ['#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#8dd1e1', '#a4de6c']
        employee_map = {e.id: e.real_name for e in EmployeeMapping.query.all()}
        we_data = []
        if records:
            for idx, (emp_id, group) in enumerate(groupby(sorted(records, key=lambda r: r.employee_id), key=lambda r: r.employee_id)):
                total_we = sum(r.we_value or 0 for r in group)
                we_data.append({
                    'name': employee_map.get(emp_id, f'员工{emp_id}'),
                    'value': total_we,
                    'color': color_list[idx % len(color_list)]
                })
        # 如果聚合后we_data为空，直接输出原始记录以便前端调试
        if not we_data:
            we_data = [
                {
                    'name': employee_map.get(r.employee_id, f'员工{r.employee_id}'),
                    'value': r.we_value or 0,
                    'color': color_list[i % len(color_list)]
                } for i, r in enumerate(records)
            ]
        print('DEBUG weData:', we_data)
        # ========== 新增：项目统计卡片数据 ==========
        # 统计项目相关的文件
        total_files = FileRecord.query.filter_by(project_id=project.id).count()
        compliant_files = FileRecord.query.filter_by(project_id=project.id, status='compliant').count()
        # 统计项目相关的消息
        chatroom_names = [c.chatroom_name for c in chatrooms]
        total_messages = ChatMessage.query.filter(ChatMessage.talker_name.in_(chatroom_names)).count()
        # 合规率
        compliance_rate = round((compliant_files / total_files) * 100, 2) if total_files else 0.0
        # 参与员工列表
        employee_ids = set([r.employee_id for r in records])
        employees = [employee_map.get(eid, '未知') for eid in employee_ids]
        # ========== 新增：健康分、风险、关键词分析 ==========
        # 健康分（统一新版逻辑）
        service = AnalysisService()
        health = service.calculate_project_health_score(project_id)
        health_score = health.get('health_score') if health else None
        risk_level = health.get('risk_level') if health else None
        # 风险事件
        recent_risks = RiskEvent.query.filter_by(project_id=project.id).order_by(RiskEvent.event_time.desc()).limit(5).all()
        risks = [r.to_dict() for r in recent_risks]
        # 关键词分析（如有关键词分析表/服务，可补充）
        keyword_analysis = KeywordAnalysis.query.filter_by(project_id=project.id).order_by(KeywordAnalysis.created_at.desc()).first()
        keywords = {}
        if keyword_analysis:
            keywords = {
                'positive_score': keyword_analysis.positive_score,
                'negative_score': keyword_analysis.negative_score,
                'neutral_score': keyword_analysis.neutral_score,
                'top_keywords': keyword_analysis.top_keywords,
                'overall_sentiment': keyword_analysis.overall_sentiment
            }
        # 近期动态（最近10条文件或消息）
        recent_files = FileRecord.query.filter_by(project_id=project.id).order_by(FileRecord.upload_time.desc()).limit(5).all()
        recent_msgs = ChatMessage.query.filter(ChatMessage.talker_name.in_(chatroom_names)).order_by(ChatMessage.timestamp.desc()).limit(5).all()
        recent_activities = [
            {
                'type': 'file_upload',
                'title': f.original_name,
                'description': f'由{f.uploader}上传',
                'time': f.upload_time.isoformat() if f.upload_time else '',
                'status': f.status
            } for f in recent_files
        ] + [
            {
                'type': 'message',
                'title': m.content[:20] if m.content else '',
                'description': f'由{m.sender_name}发送',
                'time': m.timestamp.isoformat() if m.timestamp else '',
                'status': m.message_type
            } for m in recent_msgs
        ]
        recent_activities = sorted(recent_activities, key=lambda x: x['time'], reverse=True)[:10]
        # ========== 组装返回结构 ==========
        project_data = {
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
            'external_chat_groups': external_chat_groups,
            'weData': we_data,  # 员工WE分布
            'stats': {  # 项目统计卡片
                'total_we': sum([w.get('value', w.get('we', 0)) for w in we_data]),
                'total_files': total_files,
                'total_messages': total_messages,
                'compliant_files': compliant_files,
                'compliance_rate': compliance_rate,
                'employees': employees
            },
            'health': health,  # 直接返回新版health字典
            'risks': risks,  # 近期风险事件
            'keywords': keywords,  # 关键词分析
            'recent_activities': recent_activities  # 近期动态
        }
        # ========== 组装metrics核心指标 ===========
        # 1. 总WE投入
        total_we = sum([w.get('value', w.get('we', 0)) for w in we_data])
        # 2. 文件相关统计
        total_files = FileRecord.query.filter_by(project_id=project.id).count()
        compliant_files = FileRecord.query.filter_by(project_id=project.id, status='compliant').count()
        non_compliant_files = FileRecord.query.filter_by(project_id=project.id, status='non_compliant').count()
        # 3. 返工文件数（假设返工次数>0的文件）
        rework_files = FileRecord.query.filter(FileRecord.project_id==project.id, FileRecord.status=='rework').count() if hasattr(FileRecord, 'status') else 0
        # 4. 一次通过文件数（假设status==compliant且返工次数为0）
        one_pass_files = compliant_files  # 占位，实际应统计返工次数为0的合规文件
        # 5. 内部修正文件数（假设status==internal_fix）
        internal_fix_files = FileRecord.query.filter(FileRecord.project_id==project.id, FileRecord.status=='internal_fix').count() if hasattr(FileRecord, 'status') else 0
        # 6. 合规率
        compliance_rate = round((compliant_files / total_files) * 100, 2) if total_files else 0.0
        # 7. 同比变化（占位，实际应查历史数据）
        def fake_change():
            return 5, 'increase'  # 占位，实际应查历史数据
        # 8. 组装metrics
        metrics = [
            {
                'title': '总WE投入',
                'value': total_we,
                'unit': '',
                'change': fake_change()[0],
                'changeType': fake_change()[1],
                'formula': '本期总WE/上期总WE'
            },
            {
                'title': '客户返工率',
                'value': 22,  # 占位
                'unit': '%',
                'change': -3,
                'changeType': 'decrease',
                'formula': '返工文件数/总文件数'
            },
            {
                'title': '一次通过率',
                'value': 78,  # 占位
                'unit': '%',
                'change': 5,
                'changeType': 'increase',
                'formula': '一次通过文件数/总文件数'
            },
            {
                'title': '内部修正率',
                'value': 35,  # 占位
                'unit': '%',
                'change': 2,
                'changeType': 'increase',
                'formula': '内部修正文件数/总文件数'
            },
            {
                'title': '文件合规率',
                'value': compliance_rate,
                'unit': '%',
                'change': 1,
                'changeType': 'increase',
                'formula': '合规文件数/总文件数'
            }
        ]
        project_data['metrics'] = metrics
        return jsonify({'success': True, 'data': project_data})
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
            # 只有当start_date在data中存在且不为空时，才进行转换
            project.start_date = datetime.fromisoformat(data['start_date']) if data.get('start_date') else None
        if 'end_date' in data:
            # 只有当end_date在data中存在且不为空时，才进行转换
            project.end_date = datetime.fromisoformat(data['end_date']) if data.get('end_date') else None
        
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

@projects_bp.route('/<int:project_id>/workloads', methods=['GET'])
def get_project_workloads(project_id):
    """
    获取某项目在指定时间段内的工作量明细，支持分页
    """
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))

    query = WorkloadRecord.query.filter_by(project_id=project_id)
    
    total = query.count()
    records = query.order_by(WorkloadRecord.date.desc()).offset((page-1)*size).limit(size).all()
    
    return jsonify({
        'total': total,
        'page': page,
        'size': size,
        'data': [r.to_dict() for r in records]
    })

@projects_bp.route('/<int:project_id>/health-stats', methods=['GET'])
def get_project_health_stats(project_id):
    """
    获取某项目的健康度统计历史
    """
    period = request.args.get('period', '30d')
    days = int(period.replace('d',''))
    since = datetime.now() - timedelta(days=days)

    stats = ProjectHealthStats.query.filter(
        ProjectHealthStats.project_id == project_id,
        ProjectHealthStats.created_at >= since
    ).order_by(ProjectHealthStats.created_at.desc()).all()
    
    return jsonify([s.to_dict() for s in stats])

@projects_bp.route('/<int:project_id>/risk-events', methods=['GET'])
def get_project_risk_events(project_id):
    """
    获取某项目相关的风险事件，支持分页和时间段筛选
    """
    period = request.args.get('period', '30d')
    days = int(period.replace('d',''))
    since = datetime.now() - timedelta(days=days)
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))

    query = RiskEvent.query.filter(
        RiskEvent.project_id == project_id,
        RiskEvent.event_time >= since
    )
    
    total = query.count()
    events = query.order_by(RiskEvent.event_time.desc()).offset((page-1)*size).limit(size).all()
    
    return jsonify({
        'total': total,
        'page': page,
        'size': size,
        'data': [e.to_dict() for e in events]
    })

@projects_bp.route('/<int:project_id>/health', methods=['GET'])
def get_project_health(project_id):
    """返回指定项目的健康度统计"""
    service = AnalysisService()
    health = service.calculate_project_health_score(project_id)
    if health:
        return jsonify({'success': True, 'data': health})
    else:
        return jsonify({'success': False, 'error': '项目不存在或无健康度数据'}), 404

@projects_bp.route('/<int:project_id>/files', methods=['GET'])
def get_project_files(project_id):
    """返回指定项目的文件列表，uploader 优先返回微信昵称，支持多字段匹配"""
    files = FileRecord.query.filter_by(project_id=project_id).all()
    employees = EmployeeMapping.query.all()
    emp_id_map = {e.id: e.wechat_nickname for e in employees}
    emp_realname_map = {e.real_name: e.wechat_nickname for e in employees}
    emp_abbr_map = {e.name_abbreviation: e.wechat_nickname for e in employees}
    emp_nickname_map = {e.wechat_nickname: e.wechat_nickname for e in employees}
    file_list = []
    for f in files:
        uploader = None
        if f.employee_id and f.employee_id in emp_id_map:
            uploader = emp_id_map[f.employee_id]
        elif f.uploader and f.uploader in emp_realname_map:
            uploader = emp_realname_map[f.uploader]
        elif f.uploader and f.uploader in emp_abbr_map:
            uploader = emp_abbr_map[f.uploader]
        elif f.uploader and f.uploader in emp_nickname_map:
            uploader = emp_nickname_map[f.uploader]
        else:
            uploader = f.uploader
        d = f.to_dict()
        d['uploader'] = uploader
        file_list.append(d)
    return jsonify({'success': True, 'data': file_list})

@projects_bp.route('/<int:project_id>/overview', methods=['GET'])
def get_project_overview(project_id):
    """
    聚合返回项目详情页所需全部数据，支持 period 参数（如 7d/30d/month/all）
    优化文件列表uploader为微信昵称，支持多字段匹配
    """
    try:
        period = request.args.get('period', '30d')
        # 解析 period
        if period == 'all':
            since = None
        elif period.endswith('d'):
            days = int(period.replace('d',''))
            since = datetime.now() - timedelta(days=days)
        elif period == 'month':
            since = datetime.now() - timedelta(days=30)
        else:
            since = datetime.now() - timedelta(days=30)
        # 1. 项目基本信息
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'success': False, 'error': '项目不存在'}), 404
        # 2. 群聊信息
        chatrooms = ProjectChatroom.query.filter_by(project_id=project_id).all()
        chatroom_list = [
            {
                'id': c.id,
                'chatroom_name': c.chatroom_name,
                'chatroom_type': c.chatroom_type,
                'created_at': c.created_at.isoformat() if c.created_at else None
            } for c in chatrooms
        ]
        chatroom_names = [c.chatroom_name for c in chatrooms]
        # 3. 健康趋势
        health_stats_query = ProjectHealthStats.query.filter(ProjectHealthStats.project_id == project_id)
        if since:
            health_stats_query = health_stats_query.filter(ProjectHealthStats.created_at >= since)
        health_stats = health_stats_query.order_by(ProjectHealthStats.created_at.desc()).all()
        health_stats_data = [s.to_dict() for s in health_stats] if health_stats else []
        # 4. WE分布
        records_query = WorkloadRecord.query.filter(WorkloadRecord.project_id == project_id)
        if since:
            records_query = records_query.filter(WorkloadRecord.date >= since)
        records = records_query.all()
        color_list = ['#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#8dd1e1', '#a4de6c']
        employee_map = {e.id: e.real_name for e in EmployeeMapping.query.all()}
        we_data = []
        if records:
            for idx, (emp_id, group) in enumerate(groupby(sorted(records, key=lambda r: r.employee_id), key=lambda r: r.employee_id)):
                total_we = sum(r.we_value or 0 for r in group)
                we_data.append({
                    'name': employee_map.get(emp_id, f'员工{emp_id}'),
                    'value': total_we,
                    'color': color_list[idx % len(color_list)]
                })
        if not we_data:
            we_data = []
        # 5. 成员列表
        employee_ids = set([r.employee_id for r in records])
        members = [employee_map.get(eid, '未知') for eid in employee_ids] if employee_ids else []
        # 6. 风险事件
        risk_events_query = RiskEvent.query.filter(RiskEvent.project_id == project_id)
        if since:
            risk_events_query = risk_events_query.filter(RiskEvent.event_time >= since)
        risk_events = risk_events_query.order_by(RiskEvent.event_time.desc()).limit(20).all()
        risks = [r.to_dict() for r in risk_events] if risk_events else []
        # 7. 项目健康分
        service = AnalysisService()
        health = service.calculate_project_health_score(project_id) or {}
        # 8. 近期动态
        recent_files = FileRecord.query.filter_by(project_id=project_id).order_by(FileRecord.upload_time.desc()).limit(5).all()
        recent_msgs = ChatMessage.query.filter(ChatMessage.talker_name.in_(chatroom_names)).order_by(ChatMessage.timestamp.desc()).limit(5).all() if chatroom_names else []
        recent_activities = [
            {
                'type': 'file_upload',
                'title': f.original_name,
                'description': f'由{f.uploader}上传',
                'time': f.upload_time.isoformat() if f.upload_time else '',
                'status': f.status
            } for f in recent_files
        ] + [
            {
                'type': 'message',
                'title': m.content[:20] if m.content else '',
                'description': f'由{m.sender_name}发送',
                'time': m.timestamp.isoformat() if m.timestamp else '',
                'status': m.message_type
            } for m in recent_msgs
        ]
        recent_activities = sorted(recent_activities, key=lambda x: x['time'], reverse=True)[:10] if recent_activities else []
        # 9. 组装返回
        files = FileRecord.query.filter_by(project_id=project_id).order_by(FileRecord.upload_time.desc()).limit(100).all()
        employees = EmployeeMapping.query.all()
        emp_id_map = {e.id: e.wechat_nickname for e in employees}
        emp_realname_map = {e.real_name: e.wechat_nickname for e in employees}
        emp_abbr_map = {e.name_abbreviation: e.wechat_nickname for e in employees}
        emp_nickname_map = {e.wechat_nickname: e.wechat_nickname for e in employees}
        file_list = []
        for f in files:
            uploader = None
            if f.employee_id and f.employee_id in emp_id_map:
                uploader = emp_id_map[f.employee_id]
            elif f.uploader and f.uploader in emp_realname_map:
                uploader = emp_realname_map[f.uploader]
            elif f.uploader and f.uploader in emp_abbr_map:
                uploader = emp_abbr_map[f.uploader]
            elif f.uploader and f.uploader in emp_nickname_map:
                uploader = emp_nickname_map[f.uploader]
            else:
                uploader = f.uploader
            d = f.to_dict()
            d['uploader'] = uploader
            file_list.append(d)
        overview = {
            'project': {
                'id': project.id,
                'project_name': project.project_name,
                'description': project.description,
                'status': project.status,
                'start_date': project.start_date.isoformat() if project.start_date else None,
                'end_date': project.end_date.isoformat() if project.end_date else None,
                'created_at': project.created_at.isoformat() if project.created_at else None,
                'updated_at': project.updated_at.isoformat() if project.updated_at else None,
            },
            'chatrooms': chatroom_list,
            'healthStats': health_stats_data,
            'weData': we_data,
            'members': members,
            'risks': risks,
            'health': health,
            'recent_activities': recent_activities,
            'files': file_list,
            'period': period
        }
        return jsonify({'success': True, 'data': overview})
    except Exception as e:
        logger.error(f"获取项目聚合视图失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def get_risk_level(health_score):
    if health_score is None:
        return None
    if health_score >= 85:
        return 'low'
    elif health_score >= 70:
        return 'medium'
    elif health_score >= 50:
        return 'risk'
    else:
        return 'critical' 

@projects_bp.route('/<int:project_id>/archive', methods=['POST'])
def archive_project(project_id):
    """
    归档项目（状态设为archived），并自动刷新聚合表
    """
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'success': False, 'error': '项目不存在'}), 404
    project.status = 'archived'
    db.session.commit()
    update_all_project_summaries()
    return jsonify({'success': True, 'message': '项目已归档'})

@projects_bp.route('/<int:project_id>/restore', methods=['POST'])
def restore_project(project_id):
    """
    恢复项目为active，并自动刷新聚合表
    """
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'success': False, 'error': '项目不存在'}), 404
    project.status = 'active'
    db.session.commit()
    update_all_project_summaries()
    return jsonify({'success': True, 'message': '项目已恢复为执行中'}) 