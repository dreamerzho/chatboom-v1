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
            if not f.file_md5:
                # 自动补全 file_md5
                base = (f.original_name or '') + str(f.project_id or '')
                import hashlib
                f.file_md5 = hashlib.md5(base.encode('utf-8')).hexdigest()
            exists = Asset.query.filter_by(file_md5=f.file_md5).first()
            if exists:
                skip += 1
                continue
            # 文件名解析
            parsed = parser.parse(f.original_name)
            # 字段映射
            asset = Asset(
                original_name = f.original_name,
                file_path = f.file_path,
                file_size = f.file_size,
                file_md5 = f.file_md5,
                file_extension = f.file_extension,
                file_type = f.file_type,
                file_category = f.file_category,
                task_identifier = parsed.task_identifier if parsed else f.work_order or '',
                submission_date = parsed.submission_date if parsed and parsed.submission_date else (f.upload_time.date() if f.upload_time else date.today()),
                version = parsed.version if parsed else (int(re.search(r'\d+', str(f.version)).group()) if f.version and re.search(r'\d+', str(f.version)) else 1),
                workload_amount = parsed.workload_amount if parsed else (f.workload or ''),
                author_abbreviation = parsed.author_abbreviation if parsed else (f.author_abbreviation or ''),
                author_id = f.employee_id,
                project_id = f.project_id,
                chatroom_name = f.chatroom_name,
                message_seq = f.message_seq,
                uploader = f.uploader,
                upload_time = f.upload_time or datetime.utcnow(),
                status = f.status or ('compliant' if parsed and parsed.is_compliant else 'non_compliant'),
                tags = f.tags,
                is_archived = f.is_archived,
                archive_path = f.archive_path,
                created_at = f.created_at or datetime.utcnow(),
                updated_at = f.updated_at or datetime.utcnow()
            )
            # 计算 WE
            asset.workload_equivalent = analyzer.calculate_workload_equivalent(asset)
            # 生成任务组ID
            asset.task_group_id = parser.generate_task_group_id(
                parsed.project_name if parsed and parsed.project_name else '',
                parsed.task_identifier if parsed else '',
                parsed.author_abbreviation if parsed else ''
            )
            # 是否为最终版
            asset.is_final_version = ('final' in (f.original_name or '').lower()) or ('最终' in (f.original_name or ''))
            session.add(asset)
            count += 1
        except Exception as e:
            print(f"[ERROR] 跳过文件: {f.original_name}, 错误: {e}")
            error += 1
            continue
    session.commit()
    print(f"导入完成: 新增 {count} 条, 跳过已存在 {skip} 条, 错误 {error} 条")

if __name__ == '__main__':
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    with app.app_context():
        batch_import_assets() 