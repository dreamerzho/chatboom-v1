#!/usr/bin/env python3
# 数据库结构重构脚本
# 该脚本用于修正数据库表结构与后端模型定义的不一致问题

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from sqlalchemy import text, inspect
from config import SQLALCHEMY_DATABASE_URI
from app import db, EmployeeMapping, Project, FileRecord, ChatMessage

# 创建Flask应用
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def backup_existing_data():
    """备份现有数据"""
    print("=== 备份现有数据 ===")
    
    with app.app_context():
        # 备份员工映射数据
        employees = EmployeeMapping.query.all()
        employee_data = []
        for emp in employees:
            employee_data.append({
                'wechat_nickname': emp.wechat_nickname,
                'real_name': emp.real_name,
                'position': emp.position,
                'name_abbreviation': emp.name_abbreviation,
                'created_at': emp.created_at,
                'updated_at': emp.updated_at
            })
        
        # 备份项目数据
        projects = Project.query.all()
        project_data = []
        for proj in projects:
            project_data.append({
                'project_name': proj.project_name,
                'description': proj.description,
                'status': proj.status,
                'external_group_name': getattr(proj, 'external_group_name', None),
                'internal_group_name': getattr(proj, 'internal_group_name', None),
                'start_date': getattr(proj, 'start_date', None),
                'end_date': getattr(proj, 'end_date', None),
                'created_at': proj.created_at,
                'updated_at': proj.updated_at
            })
        
        # 备份文件记录数据
        files = FileRecord.query.all()
        file_data = []
        for file_rec in files:
            file_data.append({
                'original_name': file_rec.original_name,
                'standardized_name': file_rec.standardized_name,
                'project_name': file_rec.project_name,
                'work_order': file_rec.work_order,
                'workload': file_rec.workload,
                'author_abbreviation': file_rec.author_abbreviation,
                'version': file_rec.version,
                'file_extension': file_rec.file_extension,
                'upload_time': file_rec.upload_time,
                'uploader': file_rec.uploader,
                'file_size': file_rec.file_size,
                'file_path': file_rec.file_path,
                'status': file_rec.status,
                'created_at': file_rec.created_at
            })
        
        # 备份聊天消息数据
        messages = ChatMessage.query.all()
        message_data = []
        for msg in messages:
            message_data.append({
                'message_id': msg.message_id,
                'sender_name': msg.sender_name,
                'message_type': msg.message_type,
                'message_content': msg.message_content,
                'file_name': msg.file_name,
                'timestamp': msg.timestamp,
                'project_id': msg.project_id,
                'message_subtype': msg.message_subtype,
                'created_at': msg.created_at
            })
        
        print(f"备份完成：员工 {len(employee_data)} 条，项目 {len(project_data)} 条，文件 {len(file_data)} 条，消息 {len(message_data)} 条")
        
        return {
            'employees': employee_data,
            'projects': project_data,
            'files': file_data,
            'messages': message_data
        }

def drop_and_recreate_tables():
    """删除并重新创建所有表"""
    print("=== 删除并重新创建表 ===")
    
    with app.app_context():
        # 删除所有表
        db.drop_all()
        print("所有表已删除")
        
        # 重新创建所有表
        db.create_all()
        print("所有表已重新创建")

def restore_data(backup_data):
    """恢复备份的数据"""
    print("=== 恢复数据 ===")
    
    with app.app_context():
        # 1. 先恢复员工映射数据
        for emp_data in backup_data['employees']:
            emp = EmployeeMapping(**emp_data)
            db.session.add(emp)
        print(f"恢复员工数据：{len(backup_data['employees'])} 条")
        
        # 2. 恢复项目数据（必须在聊天消息之前）
        for proj_data in backup_data['projects']:
            proj = Project(**proj_data)
            db.session.add(proj)
        print(f"恢复项目数据：{len(backup_data['projects'])} 条")
        
        # 提交员工和项目数据，确保外键约束满足
        db.session.commit()
        print("员工和项目数据已提交")
        
        # 3. 恢复文件记录数据
        for file_data in backup_data['files']:
            file_rec = FileRecord(**file_data)
            db.session.add(file_rec)
        print(f"恢复文件数据：{len(backup_data['files'])} 条")
        
        # 4. 恢复聊天消息数据（处理外键约束）
        for msg_data in backup_data['messages']:
            # 检查project_id是否存在，如果不存在则设为None
            if msg_data.get('project_id') is not None:
                # 检查项目是否存在
                project_exists = db.session.query(Project.id).filter_by(id=msg_data['project_id']).first()
                if not project_exists:
                    print(f"警告：项目ID {msg_data['project_id']} 不存在，将设为None")
                    msg_data['project_id'] = None
            
            msg = ChatMessage(**msg_data)
            db.session.add(msg)
        print(f"恢复消息数据：{len(backup_data['messages'])} 条")
        
        # 提交所有更改
        db.session.commit()
        print("数据恢复完成")

def verify_table_structure():
    """验证表结构是否正确"""
    print("=== 验证表结构 ===")
    
    with app.app_context():
        inspector = inspect(db.engine)
        
        # 检查ChatMessage表结构
        chat_columns = inspector.get_columns('chat_messages')
        print("ChatMessage表字段：")
        for col in chat_columns:
            print(f"  - {col['name']}: {col['type']}")
        
        # 检查EmployeeMapping表结构
        emp_columns = inspector.get_columns('employee_mappings')
        print("EmployeeMapping表字段：")
        for col in emp_columns:
            print(f"  - {col['name']}: {col['type']}")
        
        # 检查Project表结构
        proj_columns = inspector.get_columns('projects')
        print("Project表字段：")
        for col in proj_columns:
            print(f"  - {col['name']}: {col['type']}")
        
        # 检查FileRecord表结构
        file_columns = inspector.get_columns('file_records')
        print("FileRecord表字段：")
        for col in file_columns:
            print(f"  - {col['name']}: {col['type']}")

def test_api_endpoints():
    """测试API端点是否正常工作"""
    print("=== 测试API端点 ===")
    
    with app.app_context():
        try:
            # 测试员工API
            employees = EmployeeMapping.query.all()
            print(f"员工API测试：{len(employees)} 条记录")
            
            # 测试项目API
            projects = Project.query.all()
            print(f"项目API测试：{len(projects)} 条记录")
            
            # 测试文件API
            files = FileRecord.query.all()
            print(f"文件API测试：{len(files)} 条记录")
            
            # 测试聊天消息API
            messages = ChatMessage.query.all()
            print(f"聊天消息API测试：{len(messages)} 条记录")
            
            # 测试仪表盘统计API
            from sqlalchemy import func
            total_employees = db.session.query(func.count(EmployeeMapping.id)).scalar()
            total_projects = db.session.query(func.count(Project.id)).scalar()
            total_files = db.session.query(func.count(FileRecord.id)).scalar()
            total_messages = db.session.query(func.count(ChatMessage.id)).scalar()
            
            print(f"仪表盘统计测试：员工 {total_employees}，项目 {total_projects}，文件 {total_files}，消息 {total_messages}")
            
            return True
        except Exception as e:
            print(f"API测试失败：{str(e)}")
            return False

def main():
    """主函数"""
    print("开始数据库结构重构...")
    
    try:
        # 1. 备份现有数据
        backup_data = backup_existing_data()
        
        # 2. 删除并重新创建表
        drop_and_recreate_tables()
        
        # 3. 恢复数据
        restore_data(backup_data)
        
        # 4. 验证表结构
        verify_table_structure()
        
        # 5. 测试API端点
        if test_api_endpoints():
            print("\n=== 数据库重构成功！ ===")
            print("所有表结构已与模型定义保持一致")
            print("API端点测试通过")
            print("可以继续进行chatlog数据导入和前端开发")
        else:
            print("\n=== 数据库重构失败！ ===")
            print("请检查错误信息并手动修复")
            
    except Exception as e:
        print(f"数据库重构过程中发生错误：{str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 