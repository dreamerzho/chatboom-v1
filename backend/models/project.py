# 项目相关数据模型
# 包含项目信息、项目与群聊多对多关系等模型定义

from datetime import datetime
try:
    from db import db
except ImportError:
    from backend.db import db

class Project(db.Model):
    """
    项目模型
    用于管理广告公司项目信息
    支持项目与多个群聊的关联和健康度评估
    """
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(128), unique=True, nullable=False)  # 项目名称
    description = db.Column(db.Text)  # 项目描述
    status = db.Column(db.String(32), default='active')  # 项目状态：active/completed/paused/cancelled
    project_type = db.Column(db.String(32), default='standard')  # 项目类型：standard/urgent/vip/regular
    external_group_name = db.Column(db.Text)  # 外部群名称
    internal_group_name = db.Column(db.Text)  # 内部群名称
    start_date = db.Column(db.Date)  # 开始日期
    end_date = db.Column(db.Date)  # 结束日期
    
    # 健康度评估字段
    health_score = db.Column(db.Float, default=100.0)  # 健康度评分 (0-100)
    risk_level = db.Column(db.String(16), default='low')  # 风险等级：low/medium/high/critical
    efficiency_score = db.Column(db.Float, default=100.0)  # 效率评分 (0-100)
    quality_score = db.Column(db.Float, default=100.0)  # 质量评分 (0-100)
    
    # 统计字段
    total_messages = db.Column(db.Integer, default=0)  # 总消息数
    total_files = db.Column(db.Integer, default=0)  # 总文件数
    active_employees = db.Column(db.Integer, default=0)  # 活跃员工数
    last_activity = db.Column(db.DateTime)  # 最后活动时间
    
    # 评估详情（JSON格式存储）
    health_details = db.Column(db.Text)  # 健康度评估详情
    risk_factors = db.Column(db.Text)  # 风险因素列表
    efficiency_metrics = db.Column(db.Text)  # 效率指标详情
    quality_metrics = db.Column(db.Text)  # 质量指标详情
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 新增：项目与群聊的多对多关系
    # 通过 ProjectChatroom 关联表实现，支持一个项目关联多个群聊
    chatrooms = db.relationship('ProjectChatroom', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    
    # 新增：项目与风险事件的关系
    risk_events = db.relationship('RiskEvent', back_populates='project', lazy='dynamic', cascade='all, delete-orphan')
    
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
            'project_type': self.project_type,
            'external_group_name': self.external_group_name,
            'internal_group_name': self.internal_group_name,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'health_score': self.health_score,
            'risk_level': self.risk_level,
            'efficiency_score': self.efficiency_score,
            'quality_score': self.quality_score,
            'total_messages': self.total_messages,
            'total_files': self.total_files,
            'active_employees': self.active_employees,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'health_details': self.health_details,
            'risk_factors': self.risk_factors,
            'efficiency_metrics': self.efficiency_metrics,
            'quality_metrics': self.quality_metrics,
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
    is_active = db.Column(db.Boolean, default=True)  # 是否活跃
    last_sync_time = db.Column(db.DateTime)  # 最后同步时间
    message_count = db.Column(db.Integer, default=0)  # 消息数量
    file_count = db.Column(db.Integer, default=0)  # 文件数量
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式，用于API响应"""
        return {
            'id': self.id,
            'chatroom_id': self.chatroom_id,
            'chatroom_name': self.chatroom_name,
            'chatroom_type': self.chatroom_type,
            'is_active': self.is_active,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'message_count': self.message_count,
            'file_count': self.file_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 