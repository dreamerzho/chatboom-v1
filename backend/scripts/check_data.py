#!/usr/bin/env python3
# 检查数据库中的数据

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from config import Config
from backend.db import db
from models.chat import ChatMessage
from models.file import FileRecord
from models.project import Project
from models.employee import EmployeeMapping
from file_validator import FileNameValidator
from sqlalchemy import func
from collections import defaultdict
from models.asset import Asset
from analysis_service import AnalysisService
import hashlib
import re

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

def batch_refresh_asset_workload_equivalent():
    """
    批量刷新所有Asset的workload_equivalent字段，确保WE统计链路打通
    """
    service = AnalysisService()
    assets = Asset.query.all()
    updated = 0
    for asset in assets:
        we = service.calculate_workload_equivalent(asset)
        if asset.workload_equivalent != we:
            asset.workload_equivalent = we
            updated += 1
    db.session.commit()
    print(f"已刷新{updated}条资产的workload_equivalent字段")

def batch_import_assets_from_files():
    """
    一次性将所有历史FileRecord批量归档为Asset
    """
    files = FileRecord.query.all()
    count = 0
    for f in files:
        if not f.file_md5:
            continue  # 跳过无md5的文件
        exists = Asset.query.filter_by(file_md5=f.file_md5).first()
        if exists:
            continue
        asset = Asset()
        asset.file_md5 = f.file_md5
        asset.project_id = f.project_id
        asset.file_name = f.standardized_name or f.original_name
        asset.author_id = f.uploader
        asset.submission_date = f.upload_time
        asset.status = f.status
        # original_name必填，兜底
        asset.original_name = f.original_name or f.standardized_name or asset.file_name
        # 只记录数字，无数字时赋1
        wa = f.workload
        if wa is None:
            wa_num = 1
        else:
            match = re.search(r'\d+', str(wa))
            wa_num = int(match.group()) if match else 1
        asset.workload_equivalent = wa_num
        # 动态兼容version为数字
        ver = f.version or ''
        match = re.search(r'\d+', ver)
        version_num = int(match.group()) if match else 1
        setattr(f, 'version', version_num)
        db.session.add(asset)
        count += 1
    db.session.commit()
    print(f"已批量归档{count}条FileRecord为Asset")

def batch_fill_file_md5():
    """
    批量补全FileRecord表file_md5字段，使用original_name+project_id生成md5
    """
    files = FileRecord.query.all()
    count = 0
    for f in files:
        if not f.file_md5:
            base = (f.original_name or '') + str(f.project_id or '')
            md5 = hashlib.md5(base.encode('utf-8')).hexdigest()
            f.file_md5 = md5
            count += 1
    db.session.commit()
    print(f"已补全{count}条FileRecord的file_md5字段")

if __name__ == '__main__':
    with app.app_context():
        batch_fix_file_records()
        if 'batch_refresh_asset_workload_equivalent' in sys.argv:
            batch_refresh_asset_workload_equivalent()
        if 'batch_import_assets_from_files' in sys.argv:
            batch_import_assets_from_files()
        if 'batch_fill_file_md5' in sys.argv:
            batch_fill_file_md5() 