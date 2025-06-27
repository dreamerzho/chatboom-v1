# 仪表盘相关的API路由
# 这个文件包含所有与仪表盘相关的API端点，包括总体统计、趋势分析等功能

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, desc
import logging
from backend.db import db
from models.workload import WorkloadRecord
from models.project_health import ProjectHealthStats
from models.risk_event import RiskEvent
from models import ChatMessage, FileRecord, Project, EmployeeMapping, ProjectChatroom, AnalysisConfig
from analysis_service import AnalysisService
from models.asset import Asset, AssetAnalysis

# 创建仪表盘蓝图
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/v1/dashboard')

# 配置日志
logger = logging.getLogger(__name__)

# 初始化分析服务
analysis_service = AnalysisService()

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
    获取表现最佳员工
    查询参数: period (默认30天)
    返回: 表现最佳员工列表
    """
    try:
        # 获取查询参数
        period = request.args.get('period', '30d')
        days = int(period.replace('d', ''))
        
        # 计算时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 统计每个员工的消息数量
        employee_stats = db.session.query(
            ChatMessage.sender_name,
            func.count(ChatMessage.id).label('message_count')
        ).filter(
            ChatMessage.timestamp >= start_time,
            ChatMessage.timestamp <= end_time
        ).group_by(
            ChatMessage.sender_name
        ).order_by(
            func.count(ChatMessage.id).desc()
        ).limit(10).all()
        
        # 统计每个员工的文件数量
        file_stats = db.session.query(
            FileRecord.uploader,
            func.count(FileRecord.id).label('file_count')
        ).filter(
            FileRecord.upload_time >= start_time,
            FileRecord.upload_time <= end_time
        ).group_by(
            FileRecord.uploader
        ).order_by(
            func.count(FileRecord.id).desc()
        ).limit(10).all()
        
        # 合并统计结果
        performers = []
        for stat in employee_stats:
            performers.append({
                'name': stat.sender_name,
                'message_count': stat.message_count,
                'file_count': 0,
                'total_score': stat.message_count
            })
        
        # 添加文件统计
        for stat in file_stats:
            found = False
            for performer in performers:
                if performer['name'] == stat.uploader:
                    performer['file_count'] = stat.file_count
                    performer['total_score'] += stat.file_count * 2  # 文件权重更高
                    found = True
                    break
            if not found:
                performers.append({
                    'name': stat.uploader,
                    'message_count': 0,
                    'file_count': stat.file_count,
                    'total_score': stat.file_count * 2
                })
        
        # 按总分排序
        performers.sort(key=lambda x: x['total_score'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'performers': performers[:10],
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
    获取项目风险榜，按健康分倒序
    直接从聚合后的项目健康统计表中获取，更高效稳定
    """
    summary = ProjectHealthStats.query.order_by(ProjectHealthStats.health_score.asc()).limit(20).all()
    return jsonify([s.to_dict() for s in summary])

# ========== 新增：兼容前端的仪表盘统计接口 ==========

@dashboard_bp.route('/stats', methods=['GET'])
def dashboard_stats():
    """
    兼容前端：返回仪表盘总览统计，直接返回DashboardStats结构
    """
    try:
        total_employees = EmployeeMapping.query.count()
        active_projects = Project.query.count()
        total_files = FileRecord.query.count()
        compliant_files = FileRecord.query.filter_by(status='compliant').count()
        # 近7天文件上传趋势
        today = datetime.now().date()
        recent_files = []
        for i in range(7):
            day = today - timedelta(days=6-i)
            count = FileRecord.query.filter(
                FileRecord.upload_time >= datetime.combine(day, datetime.min.time()),
                FileRecord.upload_time <= datetime.combine(day, datetime.max.time())
            ).count()
            recent_files.append({'date': str(day), 'count': count})
        return jsonify({'success': True, 'data': {
            'total_employees': total_employees,
            'active_projects': active_projects,
            'total_files': total_files,
            'compliant_files': compliant_files,
            'recent_files': recent_files
        }})
    except Exception as e:
        logger.error(f"获取仪表盘总览失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/employee-ranking', methods=['GET'])
def get_employee_ranking():
    """
    获取员工效能榜，支持按岗位、周期筛选
    数据源为 WorkloadRecord，统计 WE 值
    """
    period = request.args.get('period', '30d')
    role = request.args.get('role')
    days = int(period.replace('d',''))
    since = datetime.now().date() - timedelta(days=days)

    query = db.session.query(
        EmployeeMapping.real_name,
        func.sum(WorkloadRecord.we_value).label('total_we')
    ).join(WorkloadRecord, EmployeeMapping.id == WorkloadRecord.employee_id)\
    .filter(WorkloadRecord.date >= since)
    
    if role:
        # 注意：EmployeeMapping 中需要有 role 字段
        employee_query = EmployeeMapping.query.filter(EmployeeMapping.position.ilike(f'%{role}%')).with_entities(EmployeeMapping.id)
        employee_ids = [item[0] for item in employee_query]
        query = query.filter(WorkloadRecord.employee_id.in_(employee_ids))

    ranking = query.group_by(EmployeeMapping.real_name).order_by(func.sum(WorkloadRecord.we_value).desc()).limit(20).all()
    
    return jsonify([{'name': r.real_name, 'total_we': r.total_we} for r in ranking])

@dashboard_bp.route('/negative-feedback', methods=['GET'])
def dashboard_negative_feedback():
    """
    兼容前端：返回负面反馈，直接返回NegativeFeedback[]
    """
    try:
        negative_keywords = ['不行', '做不了', '有问题', '延误', '投诉', '失败']
        messages = ChatMessage.query.filter(
            db.or_(*[ChatMessage.content.contains(word) for word in negative_keywords])
        ).order_by(ChatMessage.timestamp.desc()).limit(20).all()
        result = []
        for msg in messages:
            found_keywords = [word for word in negative_keywords if word in (msg.content or '')]
            result.append({
                'sender_name': msg.sender_name,
                'content': msg.content,
                'message_time': msg.timestamp.isoformat() if msg.timestamp else '',
                'group_name': msg.talker_name,
                'negative_keywords': found_keywords
            })
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.error(f"获取负面反馈失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/recent-activities', methods=['GET'])
def dashboard_recent_activities():
    """
    兼容前端：返回近期动态，直接返回RecentActivity[]
    """
    try:
        # 最近10个文件上传
        files = FileRecord.query.order_by(FileRecord.upload_time.desc()).limit(10).all()
        file_acts = [{
            'type': 'file_upload',
            'title': f.original_name,
            'description': f'由{f.uploader}上传',
            'time': f.upload_time.isoformat() if f.upload_time else '',
            'status': f.status
        } for f in files]
        # 最近10个项目更新（示例，实际可扩展）
        projects = Project.query.order_by(Project.updated_at.desc()).limit(10).all()
        proj_acts = [{
            'type': 'project_update',
            'title': p.project_name,
            'description': p.description or '',
            'time': p.updated_at.isoformat() if p.updated_at else '',
            'status': p.status
        } for p in projects]
        acts = sorted(file_acts + proj_acts, key=lambda x: x['time'], reverse=True)[:10]
        return jsonify({'success': True, 'data': acts})
    except Exception as e:
        logger.error(f"获取近期动态失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== 新增：工作量明细记录API ========== 

@dashboard_bp.route('/workloads', methods=['GET'])
def get_workload_records():
    """
    获取所有工作量明细记录（支持分页、筛选）
    查询参数：page, page_size, employee_id, project_id, date_start, date_end
    返回：工作量明细记录列表及分页信息
    """
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        employee_id = request.args.get('employee_id', type=int)
        project_id = request.args.get('project_id', type=int)
        date_start = request.args.get('date_start')
        date_end = request.args.get('date_end')

        query = WorkloadRecord.query
        if employee_id:
            query = query.filter_by(employee_id=employee_id)
        if project_id:
            query = query.filter_by(project_id=project_id)
        if date_start:
            try:
                start_dt = datetime.fromisoformat(date_start)
                query = query.filter(WorkloadRecord.date >= start_dt)
            except Exception:
                pass
        if date_end:
            try:
                end_dt = datetime.fromisoformat(date_end)
                query = query.filter(WorkloadRecord.date <= end_dt)
            except Exception:
                pass
        total = query.count()
        records = query.order_by(WorkloadRecord.date.desc()).offset((page-1)*page_size).limit(page_size).all()
        return jsonify({
            'success': True,
            'data': [r.to_dict() for r in records],
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total
            }
        })
    except Exception as e:
        logger.error(f"获取工作量明细记录失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/workloads', methods=['POST'])
def create_workload_record():
    """
    新增工作量明细记录
    请求体：JSON格式，包含WorkloadRecord所有必需字段
    返回：新增记录详情
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '缺少请求数据'}), 400
        # 字段校验与赋值
        record = WorkloadRecord(
            employee_id = data.get('employee_id'),
            project_id = data.get('project_id'),
            date = datetime.fromisoformat(data.get('date')) if data.get('date') else datetime.now().date(),
            role = data.get('role', ''),
            output_type = data.get('output_type', ''),
            output_value = data.get('output_value', ''),
            we_value = data.get('we_value', 0.0),
            is_final = data.get('is_final', False),
            is_iteration = data.get('is_iteration', False),
            iteration_count = data.get('iteration_count', 0),
            related_file_id = data.get('related_file_id'),
            related_message_id = data.get('related_message_id'),
            business_unit = data.get('business_unit', ''),
            quantity = data.get('quantity', 1.0)
        )
        db.session.add(record)
        db.session.commit()
        return jsonify({'success': True, 'data': record.to_dict()})
    except Exception as e:
        logger.error(f"新增工作量明细记录失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/workloads/<int:record_id>', methods=['GET'])
def get_workload_record_detail(record_id):
    """
    获取单条工作量明细记录详情
    参数：record_id - 记录ID
    返回：记录详情
    """
    try:
        record = WorkloadRecord.query.get(record_id)
        if not record:
            return jsonify({'success': False, 'error': '记录不存在'}), 404
        return jsonify({'success': True, 'data': record.to_dict()})
    except Exception as e:
        logger.error(f"获取工作量明细记录详情失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/project-health', methods=['GET'])
def get_project_health_stats():
    """
    获取所有项目的健康度统计数据
    支持前端仪表盘项目榜单、健康趋势等区块
    """
    stats = ProjectHealthStats.query.order_by(ProjectHealthStats.created_at.desc()).all()
    return jsonify([s.to_dict() for s in stats])

@dashboard_bp.route('/risk-feed', methods=['GET'])
def get_risk_feed():
    """
    获取最新风险事件流
    支持前端仪表盘风险流、预警推送等区块
    """
    events = RiskEvent.query.order_by(RiskEvent.event_time.desc()).limit(30).all()
    return jsonify([e.to_dict() for e in events])

@dashboard_bp.route('/workload-trend', methods=['GET'])
def get_workload_trend():
    """
    获取团队/岗位的工作量趋势
    参数：period（如7d/30d/90d），role（可选）
    """
    period = request.args.get('period', '7d')
    role = request.args.get('role')
    days = int(period.replace('d',''))
    since = datetime.now().date() - timedelta(days=days)
    query = db.session.query(
        WorkloadRecord.date,
        func.sum(WorkloadRecord.we_value).label('total_we')
    ).filter(WorkloadRecord.date >= since)
    if role:
        query = query.filter(WorkloadRecord.role == role)
    trend = query.group_by(WorkloadRecord.date).order_by(WorkloadRecord.date).all()
    return jsonify([{'date': r.date.isoformat(), 'total_we': r.total_we} for r in trend])

@dashboard_bp.route('/kpis', methods=['GET'])
def get_dashboard_kpis():
    """
    获取仪表盘核心KPI指标
    一次性返回所有关键指标卡片的数据
    """
    try:
        # 获取时间范围参数
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # 默认最近7天
        if not start_date_str:
            end_date = date.today()
            start_date = end_date - timedelta(days=7)
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else date.today()
        
        # 使用分析服务获取KPI数据
        kpi_data = analysis_service.get_dashboard_kpis(start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': kpi_data,
            'time_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/workload-ranking', methods=['GET'])
def get_workload_ranking():
    """
    获取工作量排行榜
    直接返回 Top 5 工作量最高的员工列表
    """
    try:
        # 获取时间范围参数
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # 默认最近7天
        if not start_date_str:
            end_date = date.today()
            start_date = end_date - timedelta(days=7)
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else date.today()
        
        # 查询员工工作量排名
        workload_stats = db.session.query(
            EmployeeMapping.id,
            EmployeeMapping.real_name,
            EmployeeMapping.position,
            func.sum(Asset.workload_equivalent).label('total_we'),
            func.count(Asset.id).label('asset_count')
        ).join(
            Asset, Asset.author_id == EmployeeMapping.id
        ).filter(
            and_(
                Asset.submission_date >= start_date,
                Asset.submission_date <= end_date
            )
        ).group_by(
            EmployeeMapping.id,
            EmployeeMapping.real_name,
            EmployeeMapping.position
        ).order_by(
            desc(func.sum(Asset.workload_equivalent))
        ).limit(5).all()
        
        # 格式化结果
        ranking_data = []
        for emp_id, real_name, position, total_we, asset_count in workload_stats:
            # 计算负荷指数
            load_data = analysis_service.calculate_employee_load_index(emp_id, start_date, end_date)
            
            ranking_data.append({
                'employee_id': emp_id,
                'real_name': real_name,
                'position': position,
                'total_we': round(total_we or 0, 2),
                'asset_count': asset_count,
                'load_index': load_data['total_load_index'],
                'efficiency_score': load_data['efficiency_score']
            })
        
        return jsonify({
            'success': True,
            'data': ranking_data,
            'time_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/high-risk-projects', methods=['GET'])
def get_high_risk_projects():
    """
    获取高风险项目列表
    直接返回高风险项目列表
    """
    try:
        # 获取所有活跃项目
        projects = Project.query.filter(Project.status == 'active').all()
        
        risk_projects = []
        for project in projects:
            # 计算项目健康度
            health_data = analysis_service.calculate_project_health_score(project.id)
            
            if health_data and health_data['risk_level'] in ['risk', 'critical']:
                risk_projects.append({
                    'project_id': project.id,
                    'project_name': project.project_name,
                    'health_score': health_data['health_score'],
                    'risk_level': health_data['risk_level'],
                    'efficiency_score': health_data['efficiency_score'],
                    'quality_score': health_data['quality_score'],
                    'asset_count': health_data['asset_count'],
                    'risk_factors': health_data.get('risk_factors', [])
                })
        
        # 按健康度排序
        risk_projects.sort(key=lambda x: x['health_score'])
        
        return jsonify({
            'success': True,
            'data': risk_projects
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/workload-trends', methods=['GET'])
def get_workload_trends():
    """
    获取工作量趋势数据
    返回最近7天的工作量趋势
    """
    try:
        # 获取时间范围参数
        days = int(request.args.get('days', 7))
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        # 查询每日工作量数据
        daily_workload = db.session.query(
            Asset.submission_date,
            func.sum(Asset.workload_equivalent).label('total_we'),
            func.count(Asset.id).label('asset_count')
        ).filter(
            and_(
                Asset.submission_date >= start_date,
                Asset.submission_date <= end_date
            )
        ).group_by(
            Asset.submission_date
        ).order_by(
            Asset.submission_date
        ).all()
        
        # 格式化趋势数据
        trends_data = []
        for submission_date, total_we, asset_count in daily_workload:
            trends_data.append({
                'date': submission_date.strftime('%m-%d'),
                'total_we': round(total_we or 0, 2),
                'asset_count': asset_count
            })
        
        return jsonify({
            'success': True,
            'data': trends_data,
            'time_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/team-performance', methods=['GET'])
def get_team_performance():
    """
    获取团队效能榜数据
    按岗位分类展示员工效能
    """
    try:
        # 获取时间范围参数
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # 默认最近7天
        if not start_date_str:
            end_date = date.today()
            start_date = end_date - timedelta(days=7)
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else date.today()
        
        # 按岗位分组查询员工效能
        performance_data = {
            'design': [],
            'copywriting': [],
            'pm_ae': []
        }
        
        # 查询所有员工的工作量数据
        employees = EmployeeMapping.query.filter(EmployeeMapping.role == '内部员工').all()
        
        for employee in employees:
            load_data = analysis_service.calculate_employee_load_index(employee.id, start_date, end_date)
            
            # 根据岗位分类
            position = employee.position or '其他'
            if '设计' in position or '美术' in position:
                category = 'design'
            elif '文案' in position or '编辑' in position:
                category = 'copywriting'
            else:
                category = 'pm_ae'
            
            performance_data[category].append({
                'employee_id': employee.id,
                'real_name': employee.real_name,
                'position': position,
                'output_we': load_data['output_we'],
                'process_we': load_data['process_we'],
                'avg_iteration': load_data.get('avg_iterations', 0),
                'efficiency_score': load_data['efficiency_score']
            })
        
        # 按产出WE排序
        for category in performance_data:
            performance_data[category].sort(key=lambda x: x['output_we'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': performance_data,
            'time_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/project-risks', methods=['GET'])
def get_project_risks():
    """
    获取项目风险榜数据
    展示各项目健康分与风险
    """
    try:
        # 获取所有活跃项目
        projects = Project.query.filter(Project.status == 'active').all()
        
        risk_data = []
        for project in projects:
            # 计算项目健康度
            health_data = analysis_service.calculate_project_health_score(project.id)
            
            if health_data:
                risk_data.append({
                    'project_id': project.id,
                    'project_name': project.project_name,
                    'health_score': health_data['health_score'],
                    'risk_level': health_data['risk_level'],
                    'efficiency_score': health_data['efficiency_score'],
                    'quality_score': health_data['quality_score'],
                    'asset_count': health_data['asset_count'],
                    'main_risk': health_data.get('risk_factors', ['-'])[0] if health_data.get('risk_factors') else '-'
                })
        
        # 按健康度排序
        risk_data.sort(key=lambda x: x['health_score'])
        
        return jsonify({
            'success': True,
            'data': risk_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/overview', methods=['GET'])
def get_dashboard_overview():
    """
    获取仪表盘概览数据
    一次性返回所有仪表盘组件需要的数据
    """
    try:
        # 获取时间范围参数
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # 默认最近7天
        if not start_date_str:
            end_date = date.today()
            start_date = end_date - timedelta(days=7)
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else date.today()
        
        # 获取所有数据
        overview_data = {
            'kpis': analysis_service.get_dashboard_kpis(start_date, end_date),
            'workload_trends': [],
            'team_performance': {},
            'project_risks': []
        }
        
        # 获取工作量趋势
        daily_workload = db.session.query(
            Asset.submission_date,
            func.sum(Asset.workload_equivalent).label('total_we'),
            func.count(Asset.id).label('asset_count')
        ).filter(
            and_(
                Asset.submission_date >= start_date,
                Asset.submission_date <= end_date
            )
        ).group_by(
            Asset.submission_date
        ).order_by(
            Asset.submission_date
        ).all()
        
        for submission_date, total_we, asset_count in daily_workload:
            overview_data['workload_trends'].append({
                'date': submission_date.strftime('%m-%d'),
                'total_we': round(total_we or 0, 2),
                'asset_count': asset_count
            })
        
        # 获取团队效能榜
        employees = EmployeeMapping.query.filter(EmployeeMapping.role == '内部员工').all()
        performance_data = {'design': [], 'copywriting': [], 'pm_ae': []}
        
        for employee in employees:
            load_data = analysis_service.calculate_employee_load_index(employee.id, start_date, end_date)
            position = employee.position or '其他'
            
            if '设计' in position or '美术' in position:
                category = 'design'
            elif '文案' in position or '编辑' in position:
                category = 'copywriting'
            else:
                category = 'pm_ae'
            
            performance_data[category].append({
                'employee_id': employee.id,
                'real_name': employee.real_name,
                'position': position,
                'output_we': load_data['output_we'],
                'process_we': load_data['process_we'],
                'avg_iteration': load_data.get('avg_iterations', 0)
            })
        
        for category in performance_data:
            performance_data[category].sort(key=lambda x: x['output_we'], reverse=True)
        
        overview_data['team_performance'] = performance_data
        
        # 获取项目风险榜
        projects = Project.query.filter(Project.status == 'active').all()
        for project in projects:
            health_data = analysis_service.calculate_project_health_score(project.id)
            if health_data:
                overview_data['project_risks'].append({
                    'project_id': project.id,
                    'project_name': project.project_name,
                    'health_score': health_data['health_score'],
                    'risk_level': health_data['risk_level'],
                    'main_risk': health_data.get('risk_factors', ['-'])[0] if health_data.get('risk_factors') else '-'
                })
        
        overview_data['project_risks'].sort(key=lambda x: x['health_score'])
        
        return jsonify({
            'success': True,
            'data': overview_data,
            'time_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ====== 算法参数配置API ======
@dashboard_bp.route('/analysis/config', methods=['GET'])
def get_analysis_config():
    """获取所有算法参数"""
    configs = AnalysisConfig.query.all()
    return jsonify({
        'success': True,
        'data': [c.to_dict() for c in configs]
    })

@dashboard_bp.route('/analysis/config', methods=['POST'])
def set_analysis_config():
    """批量设置算法参数（参数为[{key, value, description}]）"""
    data = request.get_json(force=True)
    if not isinstance(data, list):
        return jsonify({'success': False, 'error': '参数格式错误，需为列表'}), 400
    for item in data:
        key = item.get('key')
        value = item.get('value')
        description = item.get('description')
        if not key:
            continue
        config = AnalysisConfig.query.filter_by(key=key).first()
        if config:
            config.value = value
            if description:
                config.description = description
        else:
            config = AnalysisConfig(key=key, value=value, description=description)
            db.session.add(config)
    db.session.commit()
    return jsonify({'success': True})

@dashboard_bp.route('/', methods=['GET'])
def dashboard_root():
    """兼容前端：dashboard根路由重定向到overview"""
    return get_dashboard_overview() 