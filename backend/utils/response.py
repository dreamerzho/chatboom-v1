# API响应工具类
# 提供统一的API响应格式，确保所有接口都遵循标准化规范

from flask import jsonify
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class APIResponse:
    """
    API响应工具类
    提供统一的成功和错误响应格式
    """
    
    @staticmethod
    def success(data=None, message="操作成功", status_code=200):
        """
        成功响应格式
        
        Args:
            data: 响应数据
            message: 成功消息
            status_code: HTTP状态码
            
        Returns:
            Flask响应对象
        """
        response = {
            "success": True,
            "data": data,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        return jsonify(response), status_code
    
    @staticmethod
    def error(error_message, error_code="UNKNOWN_ERROR", status_code=400, data=None):
        """
        错误响应格式
        
        Args:
            error_message: 错误消息
            error_code: 错误代码
            status_code: HTTP状态码
            data: 额外错误数据
            
        Returns:
            Flask响应对象
        """
        response = {
            "success": False,
            "error": error_message,
            "error_code": error_code,
            "timestamp": datetime.now().isoformat()
        }
        
        if data:
            response["data"] = data
            
        # 记录错误日志
        logger.error(f"API错误: {error_code} - {error_message}")
        
        return jsonify(response), status_code
    
    @staticmethod
    def validation_error(errors, message="数据验证失败"):
        """
        数据验证错误响应
        
        Args:
            errors: 验证错误详情
            message: 错误消息
            
        Returns:
            Flask响应对象
        """
        return APIResponse.error(
            error_message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            data={"validation_errors": errors}
        )
    
    @staticmethod
    def not_found(resource_name="资源", resource_id=None):
        """
        资源不存在错误响应
        
        Args:
            resource_name: 资源名称
            resource_id: 资源ID
            
        Returns:
            Flask响应对象
        """
        message = f"{resource_name}不存在"
        if resource_id:
            message += f" (ID: {resource_id})"
            
        return APIResponse.error(
            error_message=message,
            error_code="NOT_FOUND",
            status_code=404
        )
    
    @staticmethod
    def duplicate_entry(field_name, field_value):
        """
        重复记录错误响应
        
        Args:
            field_name: 重复字段名
            field_value: 重复字段值
            
        Returns:
            Flask响应对象
        """
        return APIResponse.error(
            error_message=f"{field_name} '{field_value}' 已存在",
            error_code="DUPLICATE_ENTRY",
            status_code=409,
            data={"field": field_name, "value": field_value}
        )
    
    @staticmethod
    def database_error(error_message="数据库操作失败"):
        """
        数据库错误响应
        
        Args:
            error_message: 错误消息
            
        Returns:
            Flask响应对象
        """
        return APIResponse.error(
            error_message=error_message,
            error_code="DATABASE_ERROR",
            status_code=500
        )
    
    @staticmethod
    def sync_error(error_message="同步操作失败"):
        """
        同步错误响应
        
        Args:
            error_message: 错误消息
            
        Returns:
            Flask响应对象
        """
        return APIResponse.error(
            error_message=error_message,
            error_code="SYNC_ERROR",
            status_code=500
        )
    
    @staticmethod
    def paginated_success(items, page, per_page, total, **kwargs):
        """
        分页成功响应
        
        Args:
            items: 数据项列表
            page: 当前页码
            per_page: 每页数量
            total: 总数量
            **kwargs: 其他响应数据
            
        Returns:
            Flask响应对象
        """
        total_pages = (total + per_page - 1) // per_page
        
        pagination = {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
        data = {
            "items": items,
            "pagination": pagination
        }
        
        # 添加其他响应数据
        data.update(kwargs)
        
        return APIResponse.success(data=data)
    
    @staticmethod
    def created(data=None, message="创建成功"):
        """
        创建成功响应（201状态码）
        
        Args:
            data: 响应数据
            message: 成功消息
            
        Returns:
            Flask响应对象
        """
        return APIResponse.success(data=data, message=message, status_code=201)
    
    @staticmethod
    def no_content(message="删除成功"):
        """
        无内容响应（204状态码）
        
        Args:
            message: 成功消息
            
        Returns:
            Flask响应对象
        """
        return APIResponse.success(data=None, message=message, status_code=204)

class ValidationHelper:
    """
    数据验证辅助工具类
    """
    
    @staticmethod
    def validate_required_fields(data, required_fields):
        """
        验证必填字段
        
        Args:
            data: 请求数据
            required_fields: 必填字段列表
            
        Returns:
            tuple: (是否验证通过, 错误信息列表)
        """
        errors = []
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == "":
                errors.append(f"字段 '{field}' 是必填的")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_string_length(value, field_name, min_length=0, max_length=None):
        """
        验证字符串长度
        
        Args:
            value: 字符串值
            field_name: 字段名
            min_length: 最小长度
            max_length: 最大长度
            
        Returns:
            tuple: (是否验证通过, 错误信息)
        """
        if not isinstance(value, str):
            return False, f"字段 '{field_name}' 必须是字符串类型"
        
        if len(value) < min_length:
            return False, f"字段 '{field_name}' 长度不能少于 {min_length} 个字符"
        
        if max_length and len(value) > max_length:
            return False, f"字段 '{field_name}' 长度不能超过 {max_length} 个字符"
        
        return True, None
    
    @staticmethod
    def validate_integer_range(value, field_name, min_value=None, max_value=None):
        """
        验证整数范围
        
        Args:
            value: 整数值
            field_name: 字段名
            min_value: 最小值
            max_value: 最大值
            
        Returns:
            tuple: (是否验证通过, 错误信息)
        """
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            return False, f"字段 '{field_name}' 必须是有效的整数"
        
        if min_value is not None and int_value < min_value:
            return False, f"字段 '{field_name}' 不能小于 {min_value}"
        
        if max_value is not None and int_value > max_value:
            return False, f"字段 '{field_name}' 不能大于 {max_value}"
        
        return True, None
    
    @staticmethod
    def validate_enum_value(value, field_name, allowed_values):
        """
        验证枚举值
        
        Args:
            value: 值
            field_name: 字段名
            allowed_values: 允许的值列表
            
        Returns:
            tuple: (是否验证通过, 错误信息)
        """
        if value not in allowed_values:
            return False, f"字段 '{field_name}' 必须是以下值之一: {', '.join(allowed_values)}"
        
        return True, None

class PaginationHelper:
    """
    分页辅助工具类
    """
    
    @staticmethod
    def get_pagination_params(request, default_per_page=20, max_per_page=100):
        """
        从请求中获取分页参数
        
        Args:
            request: Flask请求对象
            default_per_page: 默认每页数量
            max_per_page: 最大每页数量
            
        Returns:
            dict: 分页参数字典
        """
        try:
            page = max(1, int(request.args.get('page', 1)))
        except ValueError:
            page = 1
        
        try:
            per_page = int(request.args.get('per_page', default_per_page))
            per_page = min(max(1, per_page), max_per_page)
        except ValueError:
            per_page = default_per_page
        
        sort_by = request.args.get('sort_by', 'id')
        sort_order = request.args.get('sort_order', 'desc')
        
        if sort_order not in ['asc', 'desc']:
            sort_order = 'desc'
        
        return {
            'page': page,
            'per_page': per_page,
            'sort_by': sort_by,
            'sort_order': sort_order
        }
    
    @staticmethod
    def apply_pagination(query, page, per_page):
        """
        对查询应用分页
        
        Args:
            query: SQLAlchemy查询对象
            page: 页码
            per_page: 每页数量
            
        Returns:
            tuple: (分页后的查询, 总数量)
        """
        total = query.count()
        offset = (page - 1) * per_page
        paginated_query = query.offset(offset).limit(per_page)
        
        return paginated_query, total 