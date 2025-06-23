# 清空所有核心业务表数据脚本
# 用于开发环境下快速清理所有业务数据，重置自增ID
# 使用前请确保数据库连接正确，且无重要数据

from app import app
from db import db
from sqlalchemy import text

# 需要清空的表，按依赖顺序排列
TABLES = [
    'asset_analyses',
    'assets',
    'chat_messages',
    'file_records',
    'projects',
    'project_chatrooms',
    'employee_mappings',
    'workload_records',
    'project_health_stats',
    'risk_events',
]

if __name__ == '__main__':
    with app.app_context():
        sql = f"TRUNCATE TABLE {', '.join(TABLES)} RESTART IDENTITY CASCADE;"
        db.session.execute(text(sql))
        db.session.commit()
        print("所有核心业务表已清空，ID已重置！") 