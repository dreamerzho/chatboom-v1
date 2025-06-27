# 数据模型包
# 只导入基础模型，避免新表模型（如 risk_event、project_health、workload）引起 MetaData 冲突

from .employee import EmployeeMapping
from .project import Project, ProjectChatroom
from .file import FileRecord, FileVersion
from .chat import ChatMessage
from .keyword import KeywordCategory, Keyword, KeywordAnalysis, MessageKeyword
from .risk_event import RiskEvent
from datetime import datetime
from backend.db import db

__all__ = [
    'EmployeeMapping',
    'Project', 
    'ProjectChatroom',
    'FileRecord',
    'FileVersion',
    'ChatMessage',
    'KeywordCategory',
    'Keyword',
    'KeywordAnalysis',
    'MessageKeyword',
    'RiskEvent'
] 

class AnalysisConfig(db.Model):
    """
    智能分析算法参数配置表
    支持动态调整各类算法阈值和权重
    """
    __tablename__ = 'analysis_config'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)  # 参数名
    value = db.Column(db.String(128), nullable=False)            # 参数值（字符串，前端可转float/int/bool等）
    description = db.Column(db.String(256))                      # 参数说明
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 