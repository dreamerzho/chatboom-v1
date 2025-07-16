#!/usr/bin/env python3
# 检查数据库中的数据

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from backend.config import Config
from backend.db import db
from backend.models.chat import ChatMessage
from backend.models.file import FileRecord
from backend.models.project import Project
from backend.models.employee import EmployeeMapping
from backend.file_validator import FileNameValidator
from sqlalchemy import func
from collections import defaultdict
from backend.models.asset import Asset
from backend.analysis_service import AnalysisService
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
    批量修正文件合规状态、项目名归类、工时统计（升级为走 ParserService 归一链路）
    """
    print("\n=== 批量修正文件合规状态、项目名归类、工时统计（ParserService归一） ===")
    from backend.parser_service import ParserService
    parser = ParserService()
    session = db.session

    # 获取所有项目名（去除"项目"等后缀，全部小写）
    projects = Project.query.all()
    project_names = [p.project_name.lower().replace('项目', '').replace(' ', '') for p in projects]
    project_name_map = {p.project_name.lower().replace('项目', '').replace(' ', ''): p.project_name for p in projects}

    # 1. 重新校验所有文件合规性、项目名归类
    files = FileRecord.query.all()
    update_count = 0
    for file in files:
        # 自动补全关键字段（无论合规与否）
        if not file.uploader:
            file.uploader = 'SYSTEM'  # 默认填充
        if not file.author_abbreviation:
            match = re.search(r'-([A-Za-z]{2,3})-', file.original_name)
            file.author_abbreviation = match.group(1).upper() if match else 'SYS'
        if not file.work_order:
            parts = file.original_name.split('-')
            file.work_order = parts[2] if len(parts) > 2 else ''
        if not file.workload:
            match = re.search(r'(\d+)', file.original_name)
            file.workload = match.group(1) if match else '1'
        if not file.version:
            match = re.search(r'[Vv](\d+)', file.original_name)
            file.version = f'V{match.group(1)}' if match else 'V1'
        # 统一用 ParserService 解析
        parsed = parser.parse(
            filename=file.original_name,
            file_record={
                'original_name': file.original_name,
                'author_abbreviation': file.author_abbreviation,
                'uploader': file.uploader,
                'employee_id': file.employee_id,
                'file_extension': file.file_extension,
                'project_name': file.project_name,
                'work_order': file.work_order,
                'workload': file.workload,
                'upload_time': file.upload_time,
                'version': file.version,
            },
            uploader=file.uploader,
            employee_id=file.employee_id
        )
        # 员工判定与岗位归一
        role = parsed.role or '未知'
        if role not in ['设计', '文案', 'PM', 'AE', '内部员工']:
            file.status = 'non_compliant'
            if hasattr(parsed, 'parse_errors'):
                file.parse_errors = str(parsed.parse_errors)
            else:
                file.parse_errors = f"非内部员工/外部客户/未知岗位，role={role}，文件名={file.original_name}"
            update_count += 1
            continue
        # 字段归一与兜底
        file.status = 'compliant'
        file.role = role
        file.output_type = parsed.output_type or '其他'
        file.business_unit = parsed.business_unit or None
        if hasattr(parsed, 'extra') and 'quantity' in parsed.extra:
            try:
                file.quantity = float(parsed.extra['quantity'])
            except Exception:
                file.quantity = 1.0
                if hasattr(parsed, 'parse_errors'):
                    file.parse_errors = str(parsed.parse_errors) + f"; quantity 字段无法转为 float，原始值: {parsed.extra['quantity']}"
        else:
            file.quantity = 1.0
        # 项目名归类
        proj = (parsed.project_name or '').lower().replace('项目', '').replace(' ', '')
        best_match = None
        for pn in project_names:
            if proj in pn or pn in proj:
                best_match = project_name_map[pn]
                break
        if best_match:
            file.project_name = best_match
        elif parsed.project_name:
            file.project_name = parsed.project_name
        # parse_errors 记录
        if hasattr(parsed, 'parse_errors'):
            file.parse_errors = str(parsed.parse_errors)
        update_count += 1
    session.commit()
    print(f"已批量修正合规状态和项目名，共处理 {update_count} 条文件记录（ParserService归一）")

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

def batch_fix_file_records_employee_id():
    """
    批量修正 file_records 的 employee_id 字段，根据 uploader 字段与员工表多字段模糊匹配，并同步修正 uploader 字段为微信昵称
    """
    print("\n=== 批量修正 file_records.employee_id 字段（增强模糊匹配） ===")
    session = db.session
    employees = EmployeeMapping.query.all()
    # 构建多种映射，全部小写、去空格
    def norm(s):
        return str(s).strip().lower() if s else ''
    emp_realname_map = {norm(e.real_name): e for e in employees}
    emp_abbr_map = {norm(e.name_abbreviation): e for e in employees}
    emp_nickname_map = {norm(e.wechat_nickname): e for e in employees}
    emp_id_map = {str(e.id): e for e in employees}
    files = FileRecord.query.all()
    update_count = 0
    for file in files:
        if file.employee_id:
            continue  # 已有则跳过
        u = norm(file.uploader)
        emp = None
        # 1. 精确匹配
        if u in emp_realname_map:
            emp = emp_realname_map[u]
        elif u in emp_abbr_map:
            emp = emp_abbr_map[u]
        elif u in emp_nickname_map:
            emp = emp_nickname_map[u]
        # 2. uploader为数字，尝试用id查找
        elif file.uploader in emp_id_map:
            emp = emp_id_map[file.uploader]
        # 3. 部分匹配
        else:
            for e in employees:
                if u and (u in norm(e.real_name) or u in norm(e.name_abbreviation) or u in norm(e.wechat_nickname)):
                    emp = e
                    break
        if emp:
            file.employee_id = emp.id
            file.uploader = emp.wechat_nickname  # 同步修正为微信昵称
            update_count += 1
    session.commit()
    print(f"已批量修正 {update_count} 条 file_records 的 employee_id 字段，并同步修正 uploader 字段为微信昵称")

if __name__ == '__main__':
    with app.app_context():
        batch_fix_file_records()
        if 'batch_refresh_asset_workload_equivalent' in sys.argv:
            batch_refresh_asset_workload_equivalent()
        if 'batch_import_assets_from_files' in sys.argv:
            batch_import_assets_from_files()
        if 'batch_fill_file_md5' in sys.argv:
            batch_fill_file_md5()
        if 'batch_fix_file_records_employee_id' in sys.argv:
            batch_fix_file_records_employee_id() 