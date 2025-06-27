# 未匹配人员数据模型
# 用于记录所有未能匹配为员工的发言人及其初步推测角色

from datetime import datetime
try:
    from db import db
except ImportError:
    from backend.db import db

class UnmatchedPerson(db.Model):
    """
    未匹配人员模型
    用于管理未能匹配为员工的发言人及其角色
    """
    __tablename__ = 'unmatched_persons'

    id = db.Column(db.Integer, primary_key=True)
    sender_name = db.Column(db.String(128), nullable=False)  # 发言人昵称
    group_name = db.Column(db.String(128), nullable=False)   # 群聊名称
    role = db.Column(db.String(32), nullable=False, default='未知')  # 角色（如：客户、老板、行政、未添加员工等）
    remark = db.Column(db.String(256))  # 备注或推测依据
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """转换为字典格式，用于API响应"""
        return {
            'id': self.id,
            'sender_name': self.sender_name,
            'group_name': self.group_name,
            'role': self.role,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 