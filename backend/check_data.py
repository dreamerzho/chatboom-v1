#!/usr/bin/env python3
# 检查数据库中的数据

from flask import Flask
from config import Config
from db import db
from models.chat import ChatMessage
from models.file import FileRecord
from models.project import Project
from models.employee import EmployeeMapping

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    print("=== 数据库数据检查 ===")
    
    # 检查ChatMessage表的数据
    message_count = ChatMessage.query.count()
    print(f'聊天消息数量: {message_count}')
    
    # 检查FileRecord表的数据
    file_count = FileRecord.query.count()
    print(f'文件记录数量: {file_count}')
    
    # 检查Project表的数据
    project_count = Project.query.count()
    print(f'项目数量: {project_count}')
    
    # 检查EmployeeMapping表的数据
    employee_count = EmployeeMapping.query.count()
    print(f'员工映射数量: {employee_count}')
    
    if message_count > 0:
        msg = ChatMessage.query.first()
        print(f'\n第一条消息: {msg.sender_name}, {msg.content[:50] if msg.content else "No content"}...')
        
        # 检查最近的几条消息
        recent_msgs = ChatMessage.query.order_by(ChatMessage.timestamp.desc()).limit(5).all()
        print(f'\n最近的消息:')
        for msg in recent_msgs:
            print(f'- {msg.sender_name}: {msg.content[:30] if msg.content else "No content"}...')
    else:
        print('\n数据库中没有聊天消息')
    
    if file_count > 0:
        print(f'\n文件记录详情:')
        files = FileRecord.query.limit(5).all()
        for file in files:
            print(f'- {file.original_name} (项目: {file.project_name}, 状态: {file.status})')
    else:
        print('\n数据库中没有文件记录')
    
    if project_count > 0:
        print(f'\n项目详情:')
        projects = Project.query.all()
        for project in projects:
            print(f'- {project.project_name} (状态: {project.status}, 消息数: {project.total_messages}, 文件数: {project.total_files})') 