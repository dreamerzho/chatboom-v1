# 数据库初始化脚本
# 用于创建所有数据库表结构，解决当前数据库表不存在的问题

import sys
import os

# 确保能导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config
from backend.db import db

# 导入所有模型以确保它们被注册
from models.employee import EmployeeMapping
from models.project import Project, ProjectChatroom
from models.file import FileRecord, FileVersion
from models.chat import ChatMessage
from models.keyword import KeywordCategory

def create_database():
    """
    创建数据库表结构
    解决当前数据库表不存在的问题
    """
    try:
        # 创建Flask应用实例
        app = Flask(__name__)
        app.config.from_object(Config)
        
        # 初始化数据库
        db.init_app(app)
        
        with app.app_context():
            print("正在连接PostgreSQL数据库...")
            print(f"数据库URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
            
            # 删除所有表（如果需要重新创建）
            print("正在删除现有表...")
            db.drop_all()
            
            # 创建所有表
            print("正在创建数据库表...")
            db.create_all()
            
            # 验证表是否创建成功
            print("验证表创建情况...")
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"已创建的表: {tables}")
            
            # 检查每个模型对应的表
            expected_tables = [
                'employee_mappings',
                'projects', 
                'project_chatrooms',
                'file_records',
                'file_versions',
                'chat_messages',
                'keyword_categories'
            ]
            
            missing_tables = []
            for table in expected_tables:
                if table in tables:
                    print(f"✓ 表 {table} 创建成功")
                else:
                    print(f"✗ 表 {table} 创建失败")
                    missing_tables.append(table)
            
            if missing_tables:
                print(f"警告: 以下表未成功创建: {missing_tables}")
                return False
            else:
                print("✓ 所有数据库表创建成功！")
                return True
                
    except Exception as e:
        print(f"数据库初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def insert_sample_data():
    """
    插入一些示例数据用于测试
    """
    try:
        # 创建Flask应用实例
        app = Flask(__name__)
        app.config.from_object(Config)
        db.init_app(app)
        
        with app.app_context():
            print("正在插入示例数据...")
            
            # 检查是否已有数据
            existing_employees = EmployeeMapping.query.count()
            if existing_employees > 0:
                print(f"数据库中已有 {existing_employees} 个员工记录，跳过示例数据插入")
                return True
            
            # 插入示例员工数据
            sample_employees = [
                {
                    'wechat_nickname': '张设计师',
                    'real_name': '张三',
                    'position': '视觉设计师',
                    'name_abbreviation': 'ZS',
                    'role': '内部员工'
                },
                {
                    'wechat_nickname': '李文案',
                    'real_name': '李四',
                    'position': '文案策划',
                    'name_abbreviation': 'LS',
                    'role': '内部员工'
                },
                {
                    'wechat_nickname': '王总',
                    'real_name': '王五',
                    'position': '客户',
                    'name_abbreviation': 'WW',
                    'role': '外部客户'
                }
            ]
            
            for emp_data in sample_employees:
                employee = EmployeeMapping(**emp_data)
                db.session.add(employee)
            
            # 插入示例项目数据
            sample_project = Project(
                project_name='测试项目',
                description='这是一个测试项目',
                status='active',
                project_type='standard',
                external_group_name='客户沟通群',
                internal_group_name='内部工作群'
            )
            db.session.add(sample_project)
            
            # 提交事务
            db.session.commit()
            
            print("✓ 示例数据插入成功！")
            print(f"已插入 {len(sample_employees)} 个员工记录")
            print("已插入 1 个项目记录")
            
            return True
            
    except Exception as e:
        print(f"示例数据插入失败: {str(e)}")
        db.session.rollback()
        return False

if __name__ == '__main__':
    print("=== 广告公司服务监测软件 - 数据库初始化 ===")
    print("根据新开发计划第一阶段：统一数据架构")
    print()
    
    # 创建数据库表
    if create_database():
        print()
        # 插入示例数据
        insert_sample_data()
        print()
        print("数据库初始化完成！现在可以正常使用系统了。")
    else:
        print("数据库初始化失败，请检查配置和连接。")
        sys.exit(1) 