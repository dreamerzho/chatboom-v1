# 风险事件模型
# 用于记录所有自动识别的风险事件（如高迭代、定稿周期异常、情绪预警等）
# 支持风险流、预警推送、项目/员工风险榜单等业务

from datetime import datetime
try:
    from db import db
except ImportError:
    from backend.db import db

class RiskEvent(db.Model):
    """
    风险事件表
    记录所有自动识别的风险事件（如高迭代、定稿周期异常、情绪预警等）
    """
    __tablename__ = 'risk_events'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)  # 项目ID
    employee_id = db.Column(db.Integer, db.ForeignKey('employee_mappings.id'))  # 员工ID（可选）
    event_type = db.Column(db.String(32), nullable=False)  # 事件类型（高迭代/定稿周期异常/情绪预警等）
    event_desc = db.Column(db.String(256))  # 事件描述
    event_time = db.Column(db.DateTime, default=datetime.utcnow)  # 事件发生时间
    severity = db.Column(db.String(8), default="中")  # 严重程度（高/中/低）
    resolved = db.Column(db.Boolean, default=False)  # 是否已处理
    attribution = db.Column(db.String(32))  # 归因标签（如项目难度预警/技能错配等）

    # 关联关系
    project = db.relationship('Project', back_populates='risk_events')
    employee = db.relationship('EmployeeMapping', back_populates='risk_events')

    def to_dict(self):
        """转换为字典格式，用于API响应"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'project_name': self.project.project_name if self.project else None,
            'employee_id': self.employee_id,
            'employee_name': self.employee.real_name if self.employee else None,
            'event_type': self.event_type,
            'event_desc': self.event_desc,
            'event_time': self.event_time.isoformat() if self.event_time else None,
            'severity': self.severity,
            'resolved': self.resolved,
            'attribution': self.attribution
        } 