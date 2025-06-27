# 系统监控工具测试脚本
# 用于测试系统监控工具的各项功能

from app import create_app
from utils import system_monitor, APIResponse, ValidationHelper, PaginationHelper
import json

def test_system_monitor():
    """测试系统监控工具"""
    app = create_app()
    
    with app.app_context():
        print("=== 系统监控工具测试 ===")
        
        # 测试系统信息
        print("\n1. 系统信息:")
        system_info = system_monitor.get_system_info()
        print(f"   - 系统: {system_info.get('platform', {}).get('system', 'unknown')}")
        print(f"   - 平台: {system_info.get('platform', {}).get('platform', 'unknown')}")
        print(f"   - 运行时间: {system_info.get('uptime', {}).get('uptime_formatted', 'unknown')}")
        
        # 测试系统资源
        print("\n2. 系统资源:")
        resources = system_monitor.get_system_resources()
        print(f"   - CPU使用率: {resources.get('cpu', {}).get('cpu_percent', 0)}%")
        print(f"   - 内存使用率: {resources.get('memory', {}).get('percent', 0)}%")
        print(f"   - 磁盘使用率: {resources.get('disk', {}).get('percent', 0)}%")
        
        # 测试数据库健康状态
        print("\n3. 数据库健康状态:")
        db_health = system_monitor.check_database_health()
        print(f"   - 状态: {db_health.get('status', 'unknown')}")
        print(f"   - 响应时间: {db_health.get('response_time_ms', 0)}ms")
        print(f"   - 连接状态: {db_health.get('connection', 'unknown')}")
        
        # 测试应用程序健康状态
        print("\n4. 应用程序健康状态:")
        app_health = system_monitor.check_application_health()
        print(f"   - 状态: {app_health.get('status', 'unknown')}")
        print(f"   - 模块状态: {app_health.get('modules', {})}")
        
        # 测试综合健康状态
        print("\n5. 综合健康状态:")
        comprehensive_health = system_monitor.get_comprehensive_health_status()
        print(f"   - 整体状态: {comprehensive_health.get('status', 'unknown')}")
        print(f"   - 错误计数: {comprehensive_health.get('summary', {}).get('error_count', 0)}")
        print(f"   - 警告计数: {comprehensive_health.get('summary', {}).get('warning_count', 0)}")
        
        # 测试性能指标
        print("\n6. 性能指标:")
        performance = system_monitor.get_performance_metrics()
        print(f"   - 综合评分: {performance.get('overall_score', 0)}")
        print(f"   - 性能等级: {performance.get('performance_level', 'unknown')}")
        print(f"   - CPU评分: {performance.get('cpu_score', 0)}")
        print(f"   - 内存评分: {performance.get('memory_score', 0)}")
        print(f"   - 磁盘评分: {performance.get('disk_score', 0)}")

def test_api_response():
    """测试API响应工具"""
    app = create_app()
    
    with app.app_context():
        print("\n=== API响应工具测试 ===")
        
        # 测试成功响应
        print("\n1. 成功响应:")
        success_response = APIResponse.success(data={"test": "data"}, message="测试成功")
        print(f"   - 响应: {success_response[0].json}")
        
        # 测试错误响应
        print("\n2. 错误响应:")
        error_response = APIResponse.error("测试错误", "TEST_ERROR", 400)
        print(f"   - 响应: {error_response[0].json}")
        
        # 测试验证错误响应
        print("\n3. 验证错误响应:")
        validation_response = APIResponse.validation_error(["字段1是必填的", "字段2格式错误"])
        print(f"   - 响应: {validation_response[0].json}")
        
        # 测试分页响应
        print("\n4. 分页响应:")
        items = [{"id": 1, "name": "测试1"}, {"id": 2, "name": "测试2"}]
        paginated_response = APIResponse.paginated_success(items, 1, 20, 100)
        print(f"   - 响应: {paginated_response[0].json}")

def test_validation_helper():
    """测试验证辅助工具"""
    print("\n=== 验证辅助工具测试 ===")
    
    # 测试必填字段验证
    print("\n1. 必填字段验证:")
    data = {"name": "测试", "email": ""}
    is_valid, errors = ValidationHelper.validate_required_fields(data, ["name", "email", "phone"])
    print(f"   - 验证结果: {is_valid}")
    print(f"   - 错误信息: {errors}")
    
    # 测试字符串长度验证
    print("\n2. 字符串长度验证:")
    is_valid, error = ValidationHelper.validate_string_length("测试", "name", 1, 10)
    print(f"   - 验证结果: {is_valid}")
    print(f"   - 错误信息: {error}")
    
    # 测试整数范围验证
    print("\n3. 整数范围验证:")
    is_valid, error = ValidationHelper.validate_integer_range(5, "age", 1, 100)
    print(f"   - 验证结果: {is_valid}")
    print(f"   - 错误信息: {error}")
    
    # 测试枚举值验证
    print("\n4. 枚举值验证:")
    is_valid, error = ValidationHelper.validate_enum_value("active", "status", ["active", "inactive", "pending"])
    print(f"   - 验证结果: {is_valid}")
    print(f"   - 错误信息: {error}")

if __name__ == "__main__":
    try:
        test_system_monitor()
        test_api_response()
        test_validation_helper()
        print("\n=== 所有测试完成 ===")
    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc() 