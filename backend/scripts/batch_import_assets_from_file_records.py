import sys
import re
import json
from datetime import datetime, date
from flask import Flask
from backend.config import Config
from backend.db import db
from backend.models.file import FileRecord
from backend.models.asset import Asset
from backend.models.project import Project
from backend.models.employee import EmployeeMapping
from backend.parser_service import ParserService
from backend.analysis_service import AnalysisService

def batch_import_assets():
    print("=== 批量导入 file_records 到 assets 表 ===")
    session = db.session
    parser = ParserService()
    analyzer = AnalysisService()
    files = FileRecord.query.all()
    count, skip, error = 0, 0, 0
    for f in files:
        try:
            if not f.employee_id:
                print(f"[SKIP] 外部文件跳过: {f.original_name}")
                continue
            if not f.file_md5:
                # 自动补全 file_md5
                base = (f.original_name or '') + str(f.project_id or '')
                import hashlib
                f.file_md5 = hashlib.md5(base.encode('utf-8')).hexdigest()
            exists = Asset.query.filter_by(file_md5=f.file_md5).first()
            if exists:
                skip += 1
                continue
            # 1. project_id 必须存在
            if not f.project_id:
                print(f"[ERROR] 跳过文件: {f.original_name}, project_id 缺失")
                error += 1
                continue
            # 2. role/author_abbreviation/author_id/uploader 匹配员工表
            emp = None
            if f.employee_id:
                emp = EmployeeMapping.query.filter_by(id=f.employee_id).first()
            if not emp and f.uploader:
                emp = EmployeeMapping.query.filter((EmployeeMapping.real_name==f.uploader)|(EmployeeMapping.name_abbreviation==f.uploader)).first()
            role = emp.position if emp and emp.position else "待确定"
            author_abbreviation = emp.name_abbreviation if emp and emp.name_abbreviation else "待确定"
            author_id = emp.id if emp else None
            uploader = emp.wechat_nickname if emp and emp.wechat_nickname else (f.uploader or "待确定")
            # 3. output_type 判定
            ext = (f.file_extension or '').lower().strip()
            output_type = ''
            # 常见后缀映射
            ext_map = {'docx':'文档','pdf':'文档','jpg':'图片','jpeg':'图片','png':'图片','zip':'压缩包','rar':'压缩包','mp4':'视频','m4v':'视频','psd':'设计稿','ai':'设计稿'}
            if ext in ext_map:
                output_type = ext_map[ext]
            else:
                # 文件名关键词
                name = (f.original_name or '').lower()
                if '海报' in name: output_type = '海报'
                elif '方案' in name: output_type = '方案'
                elif '总结' in name: output_type = '总结'
                elif '视频' in name: output_type = '视频'
                elif 'PPT' in name or 'ppt' in name: output_type = 'PPT'
                else: output_type = '其他'
            # 4. file_type 兜底
            file_type = f.file_type or '其他'
            # 5. version 兜底并转 int
            vstr = str(f.version or '')
            m = re.search(r'(\d+)', vstr)
            version = int(m.group(1)) if m else 1
            # 6. workload_amount 兜底并转 float
            wstr = str(f.workload or '')
            m = re.search(r'(\d+)', wstr)
            workload_amount = float(m.group(1)) if m else 1.0
            # 7. 其它字段常规兜底
            file_category = f.file_category or ''
            status = f.status or 'non_compliant'
            task_identifier = f.work_order or ''
            submission_date = f.upload_time.date() if f.upload_time else datetime.utcnow().date()
            chatroom_name = f.chatroom_name or ''
            message_seq = f.message_seq or ''
            tags = f.tags or ''
            is_archived = f.is_archived or False
            archive_path = f.archive_path or ''
            created_at = f.created_at or datetime.utcnow()
            updated_at = f.updated_at or datetime.utcnow()
            # 8. 构造 asset
            asset = Asset(
                original_name=f.original_name or '',
                file_path=f.file_path or '',
                file_size=f.file_size or 0,
                file_md5=f.file_md5 or '',
                file_extension=ext,
                file_type=file_type,
                file_category=file_category,
                task_identifier=task_identifier,
                submission_date=submission_date,
                version=version,
                workload_amount=workload_amount,
                author_abbreviation=author_abbreviation,
                author_id=author_id,
                project_id=f.project_id,
                chatroom_name=chatroom_name,
                message_seq=message_seq,
                uploader=uploader,
                upload_time=f.upload_time or datetime.utcnow(),
                status=status,
                tags=tags,
                is_archived=is_archived,
                archive_path=archive_path,
                created_at=created_at,
                updated_at=updated_at
            )
            # 9. 计算 WE，失败则报错并跳过
            try:
                asset.workload_equivalent = workload_amount
                # 可扩展：乘以权重等
            except Exception as e:
                print(f"[ERROR] 跳过文件: {f.original_name}, workload_equivalent 计算失败: {e}")
                error += 1
                continue
            session.add(asset)
            count += 1
        except Exception as e:
            error += 1
            print(f"[ERROR] 跳过文件: {f.original_name}, 错误: {str(e)}")
            continue
    session.commit()
    print(f"导入完成: 新增 {count} 条, 跳过已存在 {skip} 条, 错误 {error} 条")
    # 新增：commit后立即查询assets表总数
    print(f"assets表当前总数: {session.query(Asset).count()}")

    # === 新增：自动标记终稿 ===
    print("[后处理] 自动标记终稿（最新版本为终稿）...")
    from sqlalchemy import func
    assets = session.query(Asset).all()
    # 先全部置为 False
    for a in assets:
        a.is_final_version = False
    session.commit()
    # 分组 project_id + work_order + author_abbreviation
    from collections import defaultdict
    group_map = defaultdict(list)
    for a in assets:
        group_key = (a.project_id, a.task_identifier or '', a.author_abbreviation or '')
        group_map[group_key].append(a)
    for group in group_map.values():
        # 取 version 最大的 asset
        def version_num(asset):
            v = str(asset.version or '')
            import re
            m = re.search(r'(\d+)', v)
            return int(m.group(1)) if m else 1
        final_asset = max(group, key=version_num)
        final_asset.is_final_version = True
    session.commit()
    print("[后处理] 终稿标记已完成。")

if __name__ == '__main__':
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    with app.app_context():
        batch_import_assets() 