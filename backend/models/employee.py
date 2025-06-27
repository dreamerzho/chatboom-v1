# 员工相关数据模型
# 包含员工映射、角色管理等模型定义

from datetime import datetime
try:
    from db import db
except ImportError:
    from backend.db import db

class EmployeeMapping(db.Model):
    """
    员工映射模型
    用于管理微信昵称与真实员工信息的对应关系
    支持员工角色区分（内部员工/外部客户）
    """
    __tablename__ = 'employee_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    wechat_nickname = db.Column(db.String(128), unique=True, nullable=False)  # 微信昵称
    real_name = db.Column(db.String(128), nullable=False)  # 真实姓名
    position = db.Column(db.String(128))  # 职位
    name_abbreviation = db.Column(db.String(16), nullable=False)  # 姓名缩写
    # 新增：员工角色字段，区分"内部员工"与"外部客户"，默认"内部员工"
    role = db.Column(db.String(32), nullable=False, default='内部员工')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # 新增：员工与风险事件的关系
    risk_events = db.relationship('RiskEvent', back_populates='employee', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """转换为字典格式，用于API响应"""
        return {
            'id': self.id,
            'wechat_nickname': self.wechat_nickname,
            'real_name': self.real_name,
            'position': self.position,
            'name_abbreviation': self.name_abbreviation,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 