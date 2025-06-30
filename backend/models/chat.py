# 聊天相关数据模型
# 包含聊天消息、消息类型等模型定义

from datetime import datetime
from backend.db import db
from sqlalchemy import UniqueConstraint

class ChatMessage(db.Model):
    """
    聊天消息模型
    用于存储微信群聊中的消息记录
    支持多种消息类型（文本、图片、文件等）
    基于 chatlog 的 seq 字段进行高效去重
    """
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.String(128), nullable=False)  # 存储 chatlog 的 seq 值作为唯一标识
    talker_name = db.Column(db.String(128), nullable=False)  # 群聊名称
    sender_name = db.Column(db.String(128), nullable=False)  # 发送者昵称
    message_type = db.Column(db.String(32), nullable=False)  # 消息类型（如：文本、图片、文件、图片消息、视频等，支持字符串）
    content = db.Column(db.Text)  # 消息内容（重命名为content以匹配API）
    message_content = db.Column(db.Text)  # 消息内容（保留原字段）
    file_name = db.Column(db.String(256))  # 文件名（当消息类型为文件时）
    timestamp = db.Column(db.DateTime, nullable=False)  # 消息时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'))  # 关联的项目ID
    message_subtype = db.Column(db.Integer)  # 消息子类型
    type = db.Column(db.Integer)  # 消息类型（别名，用于兼容）
    
    # 复合唯一约束：确保同一项目下同一消息ID不会重复
    __table_args__ = (
        UniqueConstraint('project_id', 'message_id', name='uq_project_message'),
    )
    
    project = db.relationship('Project', backref=db.backref('chat_messages', passive_deletes=True))
    
    def to_dict(self):
        """转换为字典格式，用于API响应"""
        return {
            'id': self.id,
            'message_id': self.message_id,
            'talker_name': self.talker_name,
            'sender_name': self.sender_name,
            'message_type': self.message_type,
            'type': self.type or self.message_type,
            'content': self.content or self.message_content,
            'message_content': self.message_content,
            'file_name': self.file_name,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'project_id': self.project_id,
            'message_subtype': self.message_subtype
        } 