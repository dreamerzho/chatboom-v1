# 清空所有核心业务表数据脚本
# 用于开发环境下快速清理所有业务数据，重置自增ID（仅支持PostgreSQL）

from backend.app import app
from backend.db import db
from backend.models.project import Project, ProjectChatroom
from backend.models.chat import ChatMessage
from backend.models.file import FileRecord
from backend.models.asset import Asset
from backend.models.workload import WorkloadRecord
from backend.models.project_health import ProjectHealthStats, ProjectDifficultyIndex
from backend.models.risk_event import RiskEvent
from backend.models.unmatched_person import UnmatchedPerson

with app.app_context():
    print('开始彻底清空所有核心业务表数据...')
    # 依赖顺序：先清空从表，再清空主表
    # 1. 先用 ORM delete
    db.session.query(ProjectChatroom).delete()
    db.session.query(ChatMessage).delete()
    db.session.query(FileRecord).delete()
    db.session.query(Asset).delete()
    db.session.query(WorkloadRecord).delete()
    db.session.query(ProjectHealthStats).delete()
    db.session.query(ProjectDifficultyIndex).delete()
    db.session.query(RiskEvent).delete()
    db.session.query(UnmatchedPerson).delete()
    db.session.query(Project).delete()
    db.session.commit()
    # 2. 再用原生 SQL 强制清空（仅支持PostgreSQL）
    # 仅支持PostgreSQL环境，其他数据库请勿使用本脚本
    engine = db.get_engine()
    conn = engine.connect()
    trans = conn.begin()
    try:
        for table in [
            'projectchatroom', 'chatmessage', 'filerecord', 'asset', 'workloadrecord',
            'projecthealthstats', 'projectdifficultyindex', 'riskevent', 'unmatchedperson', 'project']:
            try:
                conn.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
            except Exception as e:
                print(f"清空表 {table} 时出错: {e}")
        trans.commit()
    except Exception as e:
        print(f"原生SQL清空表时出错: {e}")
        trans.rollback()
    finally:
        conn.close()
    print('所有核心业务表数据已彻底清空！')
    # 打印各表剩余数据量
    print('项目数:', Project.query.count())
    print('工作量记录数:', WorkloadRecord.query.count())
    print('聊天消息数:', ChatMessage.query.count())
    print('文件记录数:', FileRecord.query.count())
    print('资产数:', Asset.query.count()) 