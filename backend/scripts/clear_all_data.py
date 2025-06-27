# 清空所有核心业务表数据脚本
# 用于开发环境下快速清理所有业务数据，重置自增ID
# 使用前请确保数据库连接正确，且无重要数据

from app import create_app
from backend.db import db
from models.project import Project, ProjectChatroom
from models.chat import ChatMessage
from models.file import FileRecord
from models.asset import Asset
from models.workload import WorkloadRecord
from models.project_health import ProjectHealthStats, ProjectDifficultyIndex
from models.risk_event import RiskEvent
from models.unmatched_person import UnmatchedPerson

app = create_app()

with app.app_context():
    print('开始清空所有核心业务表数据...')
    # 依赖顺序：先清空从表，再清空主表
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
    print('所有核心业务表数据已清空！')
    # 新增：打印各表剩余数据量
    print('项目数:', Project.query.count())
    print('工作量记录数:', WorkloadRecord.query.count())
    print('聊天消息数:', ChatMessage.query.count())
    print('文件记录数:', FileRecord.query.count())
    print('资产数:', Asset.query.count()) 