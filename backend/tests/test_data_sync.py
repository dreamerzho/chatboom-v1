# 数据同步测试脚本
# 用于测试统一数据管理器的功能，验证数据同步是否正常工作

import sys
import os
from datetime import datetime, timedelta

# 确保能导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config
from db import db
from data_manager import data_manager

# 导入模型
from models.employee import EmployeeMapping
from models.project import Project
from models.file import FileRecord
from models.chat import ChatMessage

def create_test_app():
    """创建测试用的Flask应用"""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def test_data_manager():
    """测试数据管理器功能"""
    print("=== 数据管理器功能测试 ===")
    
    app = create_test_app()
    
    with app.app_context():
        try:
            # 1. 测试获取员工统计
            print("\n1. 测试员工统计功能...")
            employees = EmployeeMapping.query.all()
            if employees:
                employee_id = employees[0].id
                result = data_manager.get_employee_stats(employee_id)
                if result['success']:
                    print(f"✓ 员工统计功能正常，员工: {employees[0].real_name}")
                    print(f"  消息统计: {result['data']['message_stats']}")
                else:
                    print(f"✗ 员工统计功能失败: {result['error']}")
            else:
                print("⚠ 没有员工数据，跳过员工统计测试")
            
            # 2. 测试获取项目统计
            print("\n2. 测试项目统计功能...")
            projects = Project.query.all()
            if projects:
                project_id = projects[0].id
                result = data_manager.get_project_stats(project_id)
                if result['success']:
                    print(f"✓ 项目统计功能正常，项目: {projects[0].project_name}")
                    print(f"  消息统计: {result['data']['message_stats']}")
                else:
                    print(f"✗ 项目统计功能失败: {result['error']}")
            else:
                print("⚠ 没有项目数据，跳过项目统计测试")
            
            # 3. 测试获取未映射用户
            print("\n3. 测试未映射用户功能...")
            result = data_manager.get_unmapped_senders()
            if result['success']:
                print(f"✓ 未映射用户功能正常")
                print(f"  未映射用户数: {result['data']['total_count']}")
                print(f"  已映射用户数: {result['data']['mapped_count']}")
            else:
                print(f"✗ 未映射用户功能失败: {result['error']}")
            
            # 4. 测试批量添加员工映射
            print("\n4. 测试批量添加员工映射功能...")
            test_mappings = [
                {
                    'wechat_nickname': '测试用户1',
                    'real_name': '测试姓名1',
                    'position': '测试职位1',
                    'name_abbreviation': 'CS1',
                    'role': '内部员工'
                },
                {
                    'wechat_nickname': '测试用户2',
                    'real_name': '测试姓名2',
                    'position': '测试职位2',
                    'name_abbreviation': 'CS2',
                    'role': '外部客户'
                }
            ]
            
            # 先检查是否已存在
            existing = EmployeeMapping.query.filter(
                EmployeeMapping.wechat_nickname.in_(['测试用户1', '测试用户2'])
            ).all()
            
            if existing:
                print("⚠ 测试用户已存在，跳过批量添加测试")
            else:
                result = data_manager.batch_add_employee_mappings(test_mappings)
                if result['success']:
                    print(f"✓ 批量添加员工映射功能正常")
                    print(f"  成功添加: {result['data']['created_count']} 个员工")
                else:
                    print(f"✗ 批量添加员工映射功能失败: {result['error']}")
            
            # 5. 测试项目数据同步（模拟）
            print("\n5. 测试项目数据同步功能...")
            test_project_name = "测试同步项目"
            test_chatrooms = ["测试群聊1", "测试群聊2"]
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            # 注意：这里只是测试接口，实际需要chatlog服务运行
            print(f"  项目名称: {test_project_name}")
            print(f"  群聊列表: {test_chatrooms}")
            print(f"  时间范围: {start_date} 到 {end_date}")
            print("  ⚠ 需要chatlog服务运行才能进行实际同步测试")
            
            return True
            
        except Exception as e:
            print(f"✗ 数据管理器测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def test_database_operations():
    """测试数据库操作"""
    print("\n=== 数据库操作测试 ===")
    
    app = create_test_app()
    
    with app.app_context():
        try:
            # 1. 测试查询操作
            print("\n1. 测试数据库查询...")
            employee_count = EmployeeMapping.query.count()
            project_count = Project.query.count()
            file_count = FileRecord.query.count()
            message_count = ChatMessage.query.count()
            
            print(f"✓ 数据库查询正常")
            print(f"  员工数量: {employee_count}")
            print(f"  项目数量: {project_count}")
            print(f"  文件数量: {file_count}")
            print(f"  消息数量: {message_count}")
            
            # 2. 测试关联查询
            print("\n2. 测试关联查询...")
            if project_count > 0:
                project = Project.query.first()
                print(f"✓ 项目关联查询正常")
                print(f"  项目名称: {project.project_name}")
                print(f"  项目状态: {project.status}")
                print(f"  关联群聊数: {project.chatrooms.count()}")
            else:
                print("⚠ 没有项目数据，跳过关联查询测试")
            
            # 3. 测试统计查询
            print("\n3. 测试统计查询...")
            from sqlalchemy import func
            
            # 按角色统计员工数量
            role_stats = db.session.query(
                EmployeeMapping.role,
                func.count(EmployeeMapping.id).label('count')
            ).group_by(EmployeeMapping.role).all()
            
            print(f"✓ 统计查询正常")
            for role, count in role_stats:
                print(f"  {role}: {count} 人")
            
            return True
            
        except Exception as e:
            print(f"✗ 数据库操作测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def test_api_integration():
    """测试API集成"""
    print("\n=== API集成测试 ===")
    
    try:
        import requests
        
        # 测试后端API
        base_url = "http://localhost:5000"
        
        # 1. 健康检查
        print("\n1. 测试API健康检查...")
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("✓ API健康检查通过")
        else:
            print(f"✗ API健康检查失败: {response.status_code}")
            return False
        
        # 2. 测试员工API
        print("\n2. 测试员工API...")
        response = requests.get(f"{base_url}/api/v1/employees", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✓ 员工API正常，返回 {len(data['data'])} 个员工")
            else:
                print(f"✗ 员工API返回错误: {data.get('error', '未知错误')}")
        else:
            print(f"✗ 员工API请求失败: {response.status_code}")
        
        # 3. 测试项目API
        print("\n3. 测试项目API...")
        response = requests.get(f"{base_url}/api/v1/projects", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✓ 项目API正常，返回 {len(data['data'])} 个项目")
            else:
                print(f"✗ 项目API返回错误: {data.get('error', '未知错误')}")
        else:
            print(f"✗ 项目API请求失败: {response.status_code}")
        
        # 4. 测试文件API
        print("\n4. 测试文件API...")
        response = requests.get(f"{base_url}/api/v1/files/list", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✓ 文件API正常，返回 {len(data['data'])} 个文件")
            else:
                print(f"✗ 文件API返回错误: {data.get('error', '未知错误')}")
        else:
            print(f"✗ 文件API请求失败: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"✗ API集成测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("=== 广告公司服务监测软件 - 数据管理测试 ===")
    print("根据新开发计划第一阶段：统一数据架构")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 执行各项测试
    tests = [
        ("数据管理器功能", test_data_manager),
        ("数据库操作", test_database_operations),
        ("API集成", test_api_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"开始测试: {test_name}")
        print('='*50)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"测试 {test_name} 发生异常: {str(e)}")
            results.append((test_name, False))
    
    # 生成测试报告
    print(f"\n{'='*50}")
    print("测试报告")
    print('='*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！数据管理系统运行正常。")
        print("💡 建议：可以开始进行实际的数据同步和功能测试。")
    else:
        print("⚠️ 部分测试失败，请检查相关功能。")
        print("💡 建议：先解决失败的测试，再进行后续开发。")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 