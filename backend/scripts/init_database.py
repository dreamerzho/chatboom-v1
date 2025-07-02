import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.app import app
from backend.db import db
from sqlalchemy import text

def ensure_columns(engine, table, columns):
    with engine.connect() as conn:
        for col, coltype in columns.items():
            try:
                conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {col} {coltype}'))
            except Exception as e:
                if 'already exists' in str(e):
                    continue
                print(f'补字段失败: {col} - {e}')

if __name__ == '__main__':
    from backend.app import create_app
    from backend.analysis_service import update_all_project_summaries
    app = create_app()
    with app.app_context():
        db.create_all()
        # 清空ProjectSummary表
        from backend.models.project_summary import ProjectSummary
        db.session.query(ProjectSummary).delete()
        db.session.commit()
        print("[ETL] ProjectSummary表已清空！")
        # 补全 employee_mappings 字段
        ensure_columns(db.engine, 'employee_mappings', {
            'wechat_nickname': 'VARCHAR(128)',
            'real_name': 'VARCHAR(128)',
            'position': 'VARCHAR(64)',
            'name_abbreviation': 'VARCHAR(32)',
            'role': 'VARCHAR(64)',
            'created_at': 'TIMESTAMP',
            'updated_at': 'TIMESTAMP'
        })
        # 补全 projects 字段
        ensure_columns(db.engine, 'projects', {
            'project_name': 'VARCHAR(128)',
            'description': 'TEXT',
            'status': 'VARCHAR(32)',
            'project_type': 'VARCHAR(64)',
            'external_group_name': 'VARCHAR(128)',
            'internal_group_name': 'VARCHAR(128)',
            'start_date': 'DATE',
            'end_date': 'DATE',
            'health_score': 'FLOAT',
            'risk_level': 'VARCHAR(32)',
            'efficiency_score': 'FLOAT',
            'quality_score': 'FLOAT',
            'total_messages': 'INTEGER',
            'total_files': 'INTEGER',
            'active_employees': 'INTEGER',
            'last_activity': 'TIMESTAMP',
            'health_details': 'TEXT',
            'risk_factors': 'TEXT',
            'efficiency_metrics': 'TEXT',
            'quality_metrics': 'TEXT',
            'created_at': 'TIMESTAMP',
            'updated_at': 'TIMESTAMP'
        })
        # 补全 file_records 字段
        ensure_columns(db.engine, 'file_records', {
            'original_name': 'VARCHAR(256)',
            'standardized_name': 'VARCHAR(256)',
            'project_name': 'VARCHAR(128)',
            'work_order': 'VARCHAR(128)',
            'workload': 'VARCHAR(32)',
            'author_abbreviation': 'VARCHAR(16)',
            'version': 'VARCHAR(32)',
            'file_extension': 'VARCHAR(16)',
            'upload_time': 'TIMESTAMP',
            'uploader': 'VARCHAR(128)',
            'file_size': 'BIGINT',
            'file_md5': 'VARCHAR(32)',
            'file_path': 'VARCHAR(256)',
            'status': 'VARCHAR(32)',
            'file_type': 'VARCHAR(32)',
            'file_category': 'VARCHAR(64)',
            'tags': 'TEXT',
            'is_archived': 'BOOLEAN',
            'archive_path': 'VARCHAR(256)',
            'created_at': 'TIMESTAMP',
            'updated_at': 'TIMESTAMP',
            'duration_hours': 'FLOAT',
            'project_id': 'INTEGER',
            'employee_id': 'INTEGER',
            'chatroom_name': 'VARCHAR(128)',
            'message_seq': 'VARCHAR(64)'
        })
        # 补全 workload_records 字段
        ensure_columns(db.engine, 'workload_records', {
            'employee_id': 'INTEGER',
            'project_id': 'INTEGER',
            'date': 'DATE',
            'role': 'VARCHAR(64)',
            'output_type': 'VARCHAR(64)',
            'output_value': 'TEXT',
            'we_value': 'FLOAT',
            'is_final': 'BOOLEAN',
            'is_iteration': 'BOOLEAN',
            'iteration_count': 'INTEGER',
            'related_file_id': 'INTEGER',
            'related_message_id': 'INTEGER',
            'business_unit': 'VARCHAR(64)',
            'quantity': 'FLOAT',
            'created_at': 'TIMESTAMP'
        })
        # 补全 chat_messages 字段
        ensure_columns(db.engine, 'chat_messages', {
            'message_id': 'VARCHAR(64)',
            'talker_name': 'VARCHAR(128)',
            'sender_name': 'VARCHAR(128)',
            'message_type': 'VARCHAR(32)',
            'content': 'TEXT',
            'file_name': 'VARCHAR(256)',
            'timestamp': 'TIMESTAMP',
            'project_id': 'INTEGER',
            'type': 'VARCHAR(32)'
        })
        # 补全 assets 字段
        ensure_columns(db.engine, 'assets', {
            'original_name': 'VARCHAR(256)',
            'file_path': 'VARCHAR(256)',
            'file_size': 'INTEGER',
            'file_md5': 'VARCHAR(32)',
            'file_extension': 'VARCHAR(16)',
            'file_type': 'VARCHAR(32)',
            'file_category': 'VARCHAR(64)',
            'task_identifier': 'VARCHAR(64)',
            'submission_date': 'DATE',
            'version': 'INTEGER',
            'workload_amount': 'FLOAT',
            'author_abbreviation': 'VARCHAR(16)',
            'author_id': 'INTEGER',
            'project_id': 'INTEGER',
            'chatroom_name': 'VARCHAR(128)',
            'status': 'VARCHAR(32)'
        })
        # 补全 project_health_stats 字段
        ensure_columns(db.engine, 'project_health_stats', {
            'project_id': 'INTEGER',
            'period': 'VARCHAR(16)',
            'health_score': 'INTEGER',
            'avg_time_to_final': 'FLOAT',
            'avg_revisions': 'FLOAT',
            'risk_count': 'INTEGER',
            'warning_count': 'INTEGER',
            'negative_sentiment_rate': 'FLOAT',
            'created_at': 'TIMESTAMP'
        })
        # 补全 risk_events 字段
        ensure_columns(db.engine, 'risk_events', {
            'project_id': 'INTEGER',
            'employee_id': 'INTEGER',
            'event_type': 'VARCHAR(64)',
            'event_desc': 'VARCHAR(256)',
            'event_time': 'TIMESTAMP',
            'severity': 'VARCHAR(32)',
            'resolved': 'BOOLEAN',
            'attribution': 'VARCHAR(128)'
        })
        update_all_project_summaries()
        print("[ETL] ProjectSummary表已批量更新完毕！")
        print('表结构补全完成') 