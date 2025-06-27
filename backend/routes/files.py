# 文件管理相关的API路由
# 这个文件包含所有与文件管理相关的API端点，包括文件列表、统计、验证等功能

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
from sqlalchemy import func, and_, desc
import logging
from backend.db import db
from models import FileRecord  # 添加 FileRecord 模型导入

# 创建文件管理蓝图
files_bp = Blueprint('files', __name__, url_prefix='/api/v1/files')

# 配置日志
logger = logging.getLogger(__name__)

@files_bp.route('/list', methods=['GET'])
def get_files():
    """
    获取文件列表
    查询参数: page, per_page, project_name, author_abbreviation, status (可选)
    返回: 文件数据列表
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        project_name = request.args.get('project_name')
        author_abbreviation = request.args.get('author_abbreviation')
        status = request.args.get('status')
        
        # 构建查询
        query = FileRecord.query
        
        # 添加过滤条件
        if project_name:
            query = query.filter(FileRecord.project_name.like(f'%{project_name}%'))
        if author_abbreviation:
            query = query.filter(FileRecord.author_abbreviation == author_abbreviation)
        if status:
            query = query.filter(FileRecord.status == status)
        
        # 按上传时间倒序排列
        query = query.order_by(desc(FileRecord.upload_time))
        
        # 分页
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        files_list = []
        for file_record in pagination.items:
            files_list.append({
                'id': file_record.id,
                'original_name': file_record.original_name,
                'standardized_name': file_record.standardized_name,
                'project_name': file_record.project_name,
                'work_order': file_record.work_order,
                'workload': file_record.workload,
                'author_abbreviation': file_record.author_abbreviation,
                'version': file_record.version,
                'file_extension': file_record.file_extension,
                'upload_time': file_record.upload_time.isoformat() if file_record.upload_time else None,
                'uploader': file_record.uploader,
                'file_size': file_record.file_size,
                'status': file_record.status
            })
        
        files_list = files_list if isinstance(files_list, list) else []
        return jsonify({
            'success': True,
            'data': {
                'items': files_list,
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
        logger.error(f"获取文件列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@files_bp.route('/stats', methods=['GET'])
def get_files_stats():
    """
    获取文件统计信息
    查询参数: start_date, end_date, project_name (可选)
    返回: 文件统计数据
    """
    try:
        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        project_name = request.args.get('project_name')
        
        # 构建查询条件
        conditions = []
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                conditions.append(FileRecord.upload_time >= start_dt)
            except ValueError:
                return jsonify({'success': False, 'error': '开始日期格式错误'}), 400
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                conditions.append(FileRecord.upload_time <= end_dt)
            except ValueError:
                return jsonify({'success': False, 'error': '结束日期格式错误'}), 400
        
        if project_name:
            conditions.append(FileRecord.project_name.like(f'%{project_name}%'))
        
        # 统计总文件数
        total_query = FileRecord.query
        if conditions:
            total_query = total_query.filter(and_(*conditions))
        total_files = total_query.count()
        
        # 按状态统计
        status_stats = db.session.query(
            FileRecord.status,
            func.count(FileRecord.id).label('count')
        )
        if conditions:
            status_stats = status_stats.filter(and_(*conditions))
        status_stats = status_stats.group_by(FileRecord.status).all()
        
        status_data = [
            {
                'status': stat.status,
                'count': stat.count
            }
            for stat in status_stats
        ]
        
        # 按项目统计
        project_stats = db.session.query(
            FileRecord.project_name,
            func.count(FileRecord.id).label('count')
        )
        if conditions:
            project_stats = project_stats.filter(and_(*conditions))
        project_stats = project_stats.group_by(FileRecord.project_name).order_by(
            desc(func.count(FileRecord.id))
        ).limit(10).all()
        
        project_data = [
            {
                'project_name': stat.project_name,
                'count': stat.count
            }
            for stat in project_stats
        ]
        
        # 按作者统计
        author_stats = db.session.query(
            FileRecord.author_abbreviation,
            func.count(FileRecord.id).label('count')
        )
        if conditions:
            author_stats = author_stats.filter(and_(*conditions))
        author_stats = author_stats.group_by(FileRecord.author_abbreviation).order_by(
            desc(func.count(FileRecord.id))
        ).limit(10).all()
        
        author_data = [
            {
                'author_abbreviation': stat.author_abbreviation,
                'count': stat.count
            }
            for stat in author_stats
        ]
        
        # 按日期统计
        daily_stats = db.session.query(
            func.date(FileRecord.upload_time).label('date'),
            func.count(FileRecord.id).label('count')
        )
        if conditions:
            daily_stats = daily_stats.filter(and_(*conditions))
        daily_stats = daily_stats.group_by(
            func.date(FileRecord.upload_time)
        ).order_by(
            func.date(FileRecord.upload_time)
        ).all()
        
        daily_data = [
            {
                'date': str(stat.date),
                'count': stat.count
            }
            for stat in daily_stats
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'total_files': total_files,
                'status_distribution': status_data,
                'project_distribution': project_data,
                'author_distribution': author_data,
                'daily_upload_stats': daily_data,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'project_name': project_name
                }
            }
        })
    except Exception as e:
        logger.error(f"获取文件统计失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@files_bp.route('/<int:file_id>', methods=['GET'])
def get_file_detail(file_id):
    """
    获取单个文件详情
    参数: file_id - 文件ID
    返回: 文件详细信息
    """
    try:
        file_record = FileRecord.query.get(file_id)
        if not file_record:
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        return jsonify({
            'success': True,
            'data': {
                'id': file_record.id,
                'original_name': file_record.original_name,
                'standardized_name': file_record.standardized_name,
                'project_name': file_record.project_name,
                'work_order': file_record.work_order,
                'workload': file_record.workload,
                'author_abbreviation': file_record.author_abbreviation,
                'version': file_record.version,
                'file_extension': file_record.file_extension,
                'upload_time': file_record.upload_time.isoformat() if file_record.upload_time else None,
                'uploader': file_record.uploader,
                'file_size': file_record.file_size,
                'status': file_record.status
            }
        })
    except Exception as e:
        logger.error(f"获取文件详情失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@files_bp.route('/<int:file_id>', methods=['PUT'])
def update_file(file_id):
    """
    更新文件信息
    参数: file_id - 文件ID
    请求体: JSON格式，包含要更新的字段
    返回: 更新结果
    """
    try:
        file_record = FileRecord.query.get(file_id)
        if not file_record:
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '缺少请求数据'}), 400
        
        # 更新字段
        if 'project_name' in data:
            file_record.project_name = data['project_name']
        if 'work_order' in data:
            file_record.work_order = data['work_order']
        if 'workload' in data:
            file_record.workload = data['workload']
        if 'author_abbreviation' in data:
            file_record.author_abbreviation = data['author_abbreviation']
        if 'version' in data:
            file_record.version = data['version']
        if 'status' in data:
            file_record.status = data['status']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': file_record.id,
                'original_name': file_record.original_name,
                'standardized_name': file_record.standardized_name,
                'project_name': file_record.project_name,
                'work_order': file_record.work_order,
                'workload': file_record.workload,
                'author_abbreviation': file_record.author_abbreviation,
                'version': file_record.version,
                'file_extension': file_record.file_extension,
                'upload_time': file_record.upload_time.isoformat() if file_record.upload_time else None,
                'uploader': file_record.uploader,
                'file_size': file_record.file_size,
                'status': file_record.status
            },
            'message': '文件信息更新成功'
        })
    except Exception as e:
        logger.error(f"更新文件信息失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@files_bp.route('/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    """
    删除文件记录
    参数: file_id - 文件ID
    返回: 删除结果
    """
    try:
        file_record = FileRecord.query.get(file_id)
        if not file_record:
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        db.session.delete(file_record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '文件记录删除成功'
        })
    except Exception as e:
        logger.error(f"删除文件记录失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 兼容 RESTful 风格，增加 /api/v1/files/ GET 路由，行为与 /list 一致
@files_bp.route('/', methods=['GET'])
def get_files_root():
    """
    获取文件列表（RESTful风格，等价于 /api/v1/files/list）
    查询参数: page, per_page, project_name, author_abbreviation, status (可选)
    返回: 文件数据列表
    """
    return get_files() 