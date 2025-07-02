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
            # 传入file_record信息，提升兜底归因能力
            parsed = parser.parse(f.original_name, file_record={
                'author_abbreviation': getattr(f, 'uploader', None),
                'uploader': getattr(f, 'uploader', None),
                'employee_id': getattr(f, 'employee_id', None),
                'file_extension': getattr(f, 'file_extension', None),
                'project_name': getattr(f, 'project_name', None),
                'work_order': getattr(f, 'work_order', None),
                'workload': getattr(f, 'workload', None),
                'upload_time': getattr(f, 'upload_time', None)
            })
            # 字段兜底与类型安全，优先用解析结果，无则用 file_record 原始字段
            file_extension = (parsed.file_extension or f.file_extension or '').lower().strip() if (parsed.file_extension or f.file_extension) else ''
            author_abbreviation = (parsed.author_abbreviation or f.uploader or '')
            if author_abbreviation:
                author_abbreviation = str(author_abbreviation).strip().upper()
            file_type = (f.file_type or '').lower().strip() if f.file_type else ''
            file_category = (f.file_category or '').strip() if f.file_category else ''
            status = f.status or ('compliant' if parsed.is_compliant else 'non_compliant')
            # 只要有基础信息就生成Asset
            asset = Asset(
                original_name=f.original_name or '',
                file_path=f.file_path or '',
                file_size=f.file_size or 0,
                file_md5=f.file_md5 or '',
                file_extension=file_extension,
                file_type=file_type,
                file_category=file_category,
                task_identifier=parsed.task_identifier or f.work_order or '',
                submission_date=parsed.submission_date or (f.upload_time.date() if f.upload_time else None),
                version=parsed.version or 1,
                workload_amount=parsed.workload_amount or f.workload or '',
                author_abbreviation=author_abbreviation,
                author_id=f.employee_id,
                project_id=f.project_id,
                chatroom_name=f.chatroom_name or '',
                message_seq=f.message_seq or '',
                uploader=f.uploader or '',
                upload_time=f.upload_time or datetime.utcnow(),
                status=status,
                tags=f.tags or '',
                is_archived=f.is_archived or False,
                archive_path=f.archive_path or '',
                created_at=f.created_at or datetime.utcnow(),
                updated_at=f.updated_at or datetime.utcnow()
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
            # 日志输出 parse_errors 和 extra 字段内容
            if parsed and (parsed.parse_errors or parsed.extra):
                print(f"[INFO] 文件: {f.original_name}, parse_errors: {parsed.parse_errors}, extra: {json.dumps(parsed.extra, ensure_ascii=False)}")
        except Exception as e:
            error += 1
            print(f"[ERROR] 跳过文件: {f.original_name}, 错误: {str(e)}")
            continue
    session.commit()
    print(f"导入完成: 新增 {count} 条, 跳过已存在 {skip} 条, 错误 {error} 条")
    # 新增：commit后立即查询assets表总数
    print(f"assets表当前总数: {session.query(Asset).count()}")

if __name__ == '__main__':
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    with app.app_context():
        batch_import_assets() 