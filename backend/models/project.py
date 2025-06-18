# 项目相关数据模型
# 包含项目信息、项目与群聊多对多关系等模型定义

from datetime import datetime
from db import db

class Project(db.Model):
    """
    项目模型
    用于管理广告公司项目信息
    支持项目与多个群聊的关联
    """
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(128), unique=True, nullable=False)  # 项目名称
    description = db.Column(db.Text)  # 项目描述
    status = db.Column(db.String(32), default='active')  # 项目状态
    external_group_name = db.Column(db.Text)  # 外部群名称
    internal_group_name = db.Column(db.Text)  # 内部群名称
    start_date = db.Column(db.Date)  # 开始日期
    end_date = db.Column(db.Date)  # 结束日期
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 新增：项目与群聊的多对多关系
    # 通过 ProjectChatroom 关联表实现，支持一个项目关联多个群聊
    chatrooms = db.relationship('ProjectChatroom', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """转换为字典格式，用于API响应"""
        # 获取项目关联的群聊列表
        chatrooms = []
        for chatroom in self.chatrooms:
            chatrooms.append({
                'id': chatroom.id,
                'chatroom_id': chatroom.chatroom_id,
                'chatroom_name': chatroom.chatroom_name,
                'chatroom_type': chatroom.chatroom_type,
                'created_at': chatroom.created_at.isoformat() if chatroom.created_at else None
            })
        
        return {
            'id': self.id,
            'project_name': self.project_name,
            'description': self.description,
            'status': self.status,
            'external_group_name': self.external_group_name,
            'internal_group_name': self.internal_group_name,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'chatrooms': chatrooms,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ProjectChatroom(db.Model):
    """
    项目与群聊多对多关联表
    用于管理项目与微信群聊的关联关系
    支持群聊类型区分（内部沟通群/客户对接群等）
    """
    __tablename__ = 'project_chatrooms'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)  # 关联的项目ID
    chatroom_id = db.Column(db.String(128), nullable=False)  # 群聊唯一标识（如wxid/群号）
    chatroom_name = db.Column(db.String(128), nullable=False)  # 群聊名称，便于前端展示
    chatroom_type = db.Column(db.String(32), nullable=False)  # 群聊类型：'内部沟通群'/'客户对接群'等
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式，用于API响应"""
        return {
            'id': self.id,
            'chatroom_id': self.chatroom_id,
            'chatroom_name': self.chatroom_name,
            'chatroom_type': self.chatroom_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 