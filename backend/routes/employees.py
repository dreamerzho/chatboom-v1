# 员工管理相关的API路由
# 这个文件包含所有与员工管理相关的API端点，包括员工映射、统计等功能
# 更新为使用统一的数据管理器

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
from sqlalchemy import func, and_
import logging
from db import db

# 导入统一数据管理器
from data_manager import data_manager
from utils import APIResponse, ValidationHelper, PaginationHelper
from models.employee import EmployeeMapping
from models.workload import WorkloadRecord
from models.risk_event import RiskEvent

# 创建员工管理蓝图
employees_bp = Blueprint('employees', __name__, url_prefix='/api/v1/employees')

# 配置日志
logger = logging.getLogger(__name__)

@employees_bp.route('/', methods=['GET'])
def get_employees():
    """
    获取所有员工映射列表（支持分页）
    查询参数：
        - page: 页码（可选，默认1）
        - per_page: 每页数量（可选，默认20）
        - q: 搜索关键词（可选，模糊匹配微信昵称/真实姓名）
    返回: 标准化分页响应，包含员工映射数据列表
    """
    try:
        # 获取分页参数
        params = PaginationHelper.get_pagination_params(request)
        page = params['page']
        per_page = params['per_page']
        q = request.args.get('q', '').strip()

        # 构建查询
        query = EmployeeMapping.query
        if q:
            query = query.filter(
                (EmployeeMapping.wechat_nickname.ilike(f'%{q}%')) |
                (EmployeeMapping.real_name.ilike(f'%{q}%'))
            )
        query = query.order_by(EmployeeMapping.id.desc())

        # 分页
        paginated_query, total = PaginationHelper.apply_pagination(query, page, per_page)
        employees = paginated_query.all()
        employee_list = [emp.to_dict() for emp in employees]

        return APIResponse.paginated_success(employee_list, page, per_page, total)
    except Exception as e:
        logger.error(f"获取员工列表失败: {str(e)}")
        return APIResponse.database_error(str(e))

@employees_bp.route('/', methods=['POST'])
def create_employee():
    """
    创建新的员工映射
    请求体: JSON格式，包含员工信息
        - wechat_nickname: 微信昵称（必填）
        - real_name: 真实姓名（必填）
        - position: 职位（必填）
        - name_abbreviation: 姓名缩写（必填）
        - role: 员工角色（可选，默认'员工'）
    返回: 创建结果，标准化响应格式
    """
    try:
        data = request.get_json()
        if not data:
            return APIResponse.validation_error(["缺少请求数据"])
        # 校验必填字段
        required_fields = ['wechat_nickname', 'real_name', 'position', 'name_abbreviation']
        is_valid, errors = ValidationHelper.validate_required_fields(data, required_fields)
        if not is_valid:
            return APIResponse.validation_error(errors)
        # 检查微信昵称唯一性
        existing_employee = EmployeeMapping.query.filter_by(
            wechat_nickname=data['wechat_nickname']
        ).first()
        if existing_employee:
            return APIResponse.duplicate_entry('wechat_nickname', data['wechat_nickname'])
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
        return APIResponse.created(
            data=new_employee.to_dict(),
            message='员工映射创建成功'
        )
    except Exception as e:
        logger.error(f"创建员工映射失败: {str(e)}")
        return APIResponse.database_error(str(e))

@employees_bp.route('/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    """
    更新员工映射信息
    参数: employee_id - 员工ID
    请求体: JSON格式，包含要更新的字段
        - wechat_nickname: 微信昵称（可选）
        - real_name: 真实姓名（可选）
        - position: 职位（可选）
        - name_abbreviation: 姓名缩写（可选）
        - role: 员工角色（可选）
    返回: 更新结果，标准化响应格式
    """
    try:
        data = request.get_json()
        if not data:
            return APIResponse.validation_error(["缺少请求数据"])
        employee = EmployeeMapping.query.get(employee_id)
        if not employee:
            return APIResponse.not_found("员工", employee_id)
        # 检查微信昵称唯一性（如有修改）
        if 'wechat_nickname' in data and data['wechat_nickname'] != employee.wechat_nickname:
            exists = EmployeeMapping.query.filter_by(wechat_nickname=data['wechat_nickname']).first()
            if exists:
                return APIResponse.duplicate_entry('wechat_nickname', data['wechat_nickname'])
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
        return APIResponse.success(
            data=employee.to_dict(),
            message='员工映射更新成功'
        )
    except Exception as e:
        logger.error(f"更新员工映射失败: {str(e)}")
        return APIResponse.database_error(str(e))

@employees_bp.route('/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    """
    删除员工映射
    参数: employee_id - 员工ID
    返回: 删除结果，标准化响应格式
    """
    try:
        employee = EmployeeMapping.query.get(employee_id)
        if not employee:
            return APIResponse.not_found("员工", employee_id)
        db.session.delete(employee)
        db.session.commit()
        return APIResponse.no_content("员工映射删除成功")
    except Exception as e:
        logger.error(f"删除员工映射失败: {str(e)}")
        return APIResponse.database_error(str(e))

@employees_bp.route('/<int:employee_id>/workloads', methods=['GET'])
def get_employee_workloads(employee_id):
    """
    获取某员工在指定时间段内的工作量明细，支持分页
    参数：start, end, page, size
    """
    try:
        start = request.args.get('start')
        end = request.args.get('end')
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        query = WorkloadRecord.query.filter_by(employee_id=employee_id)
        if start:
            query = query.filter(WorkloadRecord.date >= start)
        if end:
            query = query.filter(WorkloadRecord.date <= end)
        total = query.count()
        records = query.order_by(WorkloadRecord.date.desc()).offset((page-1)*size).limit(size).all()
        return jsonify({
            'total': total,
            'page': page,
            'size': size,
            'data': [r.to_dict() for r in records]
        })
    except Exception as e:
        logger.error(f"获取员工工作量明细失败: {str(e)}")
        return APIResponse.database_error(str(e))

@employees_bp.route('/<int:employee_id>/stats', methods=['GET'])
def get_employee_stats(employee_id):
    """
    获取某员工的聚合统计（总WE、过程WE、平均迭代、参与项目数等）
    参数：period（如7d/30d/90d），默认7d
    """
    try:
        period = request.args.get('period', '7d')
        days = int(period.replace('d',''))
        since = datetime.now().date() - timedelta(days=days)
        records = WorkloadRecord.query.filter(
            WorkloadRecord.employee_id == employee_id,
            WorkloadRecord.date >= since
        ).all()
        total_we = sum([r.we_value for r in records])
        process_we = sum([r.we_value for r in records if r.is_iteration])
        final_we = sum([r.we_value for r in records if r.is_final])
        avg_iteration = sum([r.iteration_count for r in records]) / len(records) if records else 0
        project_ids = set([r.project_id for r in records])
        return jsonify({
            'employee_id': employee_id,
            'period': period,
            'total_we': total_we,
            'process_we': process_we,
            'final_we': final_we,
            'avg_iteration': avg_iteration,
            'project_count': len(project_ids)
        })
    except Exception as e:
        logger.error(f"获取员工统计失败: {str(e)}")
        return APIResponse.database_error(str(e))

@employees_bp.route('/<int:employee_id>/risk-events', methods=['GET'])
def get_employee_risk_events(employee_id):
    """
    获取某员工相关的风险事件，支持 period、分页
    """
    try:
        period = request.args.get('period', '30d')
        days = int(period.replace('d',''))
        since = datetime.now() - timedelta(days=days)
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        query = RiskEvent.query.filter(
            RiskEvent.employee_id == employee_id,
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
    except Exception as e:
        logger.error(f"获取员工风险事件失败: {str(e)}")
        return APIResponse.database_error(str(e))

@employees_bp.route('/stats/overview', methods=['GET'])
def get_employees_overview():
    """
    获取所有员工的统计总览
    查询参数: start_date, end_date (可选)
    返回: 员工统计总览数据，标准化响应格式
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        overview = data_manager.get_employees_overview(start_date, end_date)
        return APIResponse.success(data=overview, message="员工统计总览获取成功")
    except Exception as e:
        logger.error(f"获取员工统计总览失败: {str(e)}")
        return APIResponse.database_error(str(e))

@employees_bp.route('/unmapped', methods=['GET'])
def get_unmapped_senders():
    """
    获取未映射的微信昵称列表
    返回: 未映射微信昵称数据，标准化响应格式
    """
    try:
        unmapped = data_manager.get_unmapped_senders()
        return APIResponse.success(data=unmapped, message="未映射微信昵称获取成功")
    except Exception as e:
        logger.error(f"获取未映射微信昵称失败: {str(e)}")
        return APIResponse.database_error(str(e))

@employees_bp.route('/unmapped/batch-add', methods=['POST'])
def batch_add_unmapped_senders():
    """
    批量添加未映射微信昵称到员工映射表
    请求体: JSON格式，包含 senders 数组
    返回: 批量添加结果，标准化响应格式
    """
    try:
        data = request.get_json()
        if not data or 'senders' not in data:
            return APIResponse.validation_error(["缺少senders参数"])
        senders = data['senders']
        if not isinstance(senders, list):
            return APIResponse.validation_error(["senders必须为数组"])
        result = data_manager.batch_add_unmapped_senders(senders)
        return APIResponse.success(data=result, message="批量添加未映射微信昵称成功")
    except Exception as e:
        logger.error(f"批量添加未映射微信昵称失败: {str(e)}")
        return APIResponse.database_error(str(e))

@employees_bp.route('/batch-import', methods=['POST'])
def batch_import_employees():
    """
    批量导入员工映射
    请求体: JSON格式，包含 employees 数组
    返回: 批量导入结果，标准化响应格式
    """
    try:
        data = request.get_json()
        if not data or 'employees' not in data:
            return APIResponse.validation_error(["缺少employees参数"])
        employees = data['employees']
        if not isinstance(employees, list):
            return APIResponse.validation_error(["employees必须为数组"])
        result = data_manager.batch_import_employees(employees)
        return APIResponse.success(data=result, message="批量导入员工成功")
    except Exception as e:
        logger.error(f"批量导入员工失败: {str(e)}")
        return APIResponse.database_error(str(e))

@employees_bp.route('/export', methods=['GET'])
def export_employees():
    """
    导出员工映射数据
    返回: 员工映射导出数据，标准化响应格式
    """
    try:
        export_data = data_manager.export_employees()
        return APIResponse.success(data=export_data, message="员工映射导出成功")
    except Exception as e:
        logger.error(f"导出员工映射失败: {str(e)}")
        return APIResponse.database_error(str(e)) 