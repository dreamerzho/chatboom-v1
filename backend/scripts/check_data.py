#!/usr/bin/env python3
# 检查数据库中的数据

from flask import Flask
from config import Config
from db import db
from models.chat import ChatMessage
from models.file import FileRecord
from models.project import Project
from models.employee import EmployeeMapping
from file_validator import FileNameValidator
from sqlalchemy import func
from collections import defaultdict

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

def batch_fix_file_records():
    """
    批量修正文件合规状态、项目名归类、工时统计
    """
    print("\n=== 批量修正文件合规状态、项目名归类、工时统计 ===")
    validator = FileNameValidator()
    session = db.session

    # 获取所有项目名（去除"项目"等后缀，全部小写）
    projects = Project.query.all()
    project_names = [p.project_name.lower().replace('项目', '').replace(' ', '') for p in projects]
    project_name_map = {p.project_name.lower().replace('项目', '').replace(' ', ''): p.project_name for p in projects}

    # 1. 重新校验所有文件合规性、项目名归类
    files = FileRecord.query.all()
    update_count = 0
    for file in files:
        result = validator.validate_filename(file.original_name)
        if result['is_compliant']:
            file.status = 'compliant'
            info = result['parsed_info']
            # 项目名归类
            proj = info['project_name'].lower().replace('项目', '').replace(' ', '')
            best_match = None
            for pn in project_names:
                if proj in pn or pn in proj:
                    best_match = project_name_map[pn]
                    break
            if best_match:
                file.project_name = best_match
            else:
                file.project_name = info['project_name']
            file.work_order = info['work_order']
            file.workload = info['workload']
            file.author_abbreviation = info['author_abbreviation']
            file.version = info['version']
        else:
            file.status = 'non_compliant'
        update_count += 1
    session.commit()
    print(f"已批量修正合规状态和项目名，共处理 {update_count} 条文件记录")

    # 2. 统计同一任务多版本的工时（按项目+工单+作者分组，取最早和最晚上传时间差）
    print("正在统计工时...")
    task_groups = defaultdict(list)
    for file in files:
        if file.status == 'compliant':
            key = (file.project_name, file.work_order, file.author_abbreviation)
            task_groups[key].append(file)
    for group_files in task_groups.values():
        if len(group_files) < 2:
            for f in group_files:
                f.duration_hours = None
            continue
        times = sorted([f.upload_time for f in group_files if f.upload_time])
        if len(times) >= 2:
            duration = (times[-1] - times[0]).total_seconds() / 3600.0
            for f in group_files:
                f.duration_hours = round(duration, 2)
    session.commit()
    print("工时统计已写入数据库")

if __name__ == '__main__':
    with app.app_context():
        batch_fix_file_records() 