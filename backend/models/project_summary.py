from datetime import datetime
from backend.db import db

class ProjectSummary(db.Model):
    """
    项目核心数据聚合表
    存储预计算的项目核心指标
    """
    __tablename__ = 'project_summary'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), unique=True, nullable=False)  # 项目ID，唯一
    project_name = db.Column(db.String(128), nullable=False)  # 项目名称
    total_files = db.Column(db.Integer, default=0)  # 文件总数
    total_workload_we = db.Column(db.Float, default=0.0)  # 总工作量（WE）
    health_score = db.Column(db.Float, default=0.0)  # 健康分
    rework_rate = db.Column(db.Float, default=0.0)  # 返工率
    avg_internal_revisions = db.Column(db.Float, default=0.0)  # 平均内部迭代次数
    avg_customer_revisions = db.Column(db.Float, default=0.0)  # 平均客户迭代次数
    risk_events_count = db.Column(db.Integer, default=0)  # 风险事件数
    positive_feedback_count = db.Column(db.Integer, default=0)  # 正向反馈数
    negative_feedback_count = db.Column(db.Integer, default=0)  # 负向反馈数
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 更新时间
    status = db.Column(db.String(32), default='active')  # 项目状态

    project = db.relationship('Project', backref=db.backref('summary', uselist=False, passive_deletes=True))

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'project_name': self.project_name,
            'total_files': self.total_files,
            'total_workload_we': self.total_workload_we,
            'health_score': self.health_score,
            'rework_rate': self.rework_rate,
            'avg_internal_revisions': self.avg_internal_revisions,
            'avg_customer_revisions': self.avg_customer_revisions,
            'risk_events_count': self.risk_events_count,
            'positive_feedback_count': self.positive_feedback_count,
            'negative_feedback_count': self.negative_feedback_count,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'status': self.status
        } 