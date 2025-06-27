# 关键词分析相关数据模型
# 包含关键词分类、关键词统计、情感分析等模型定义

from datetime import datetime
from backend.db import db

class KeywordCategory(db.Model):
    """
    关键词分类模型
    用于管理不同类型的关键词（正面/负面/中性）
    """
    __tablename__ = 'keyword_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)  # 分类名称：正面/负面/中性
    description = db.Column(db.Text)  # 分类描述
    color = db.Column(db.String(16), default='#666666')  # 分类颜色，用于前端展示
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关键词
    keywords = db.relationship('Keyword', backref='category', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """转换为字典格式，用于API响应"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'is_active': self.is_active,
            'keyword_count': self.keywords.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Keyword(db.Model):
    """
    关键词模型
    用于管理具体的关键词及其权重
    """
    __tablename__ = 'keywords'
    
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(128), nullable=False)  # 关键词内容
    category_id = db.Column(db.Integer, db.ForeignKey('keyword_categories.id'), nullable=False)  # 所属分类
    weight = db.Column(db.Float, default=1.0)  # 关键词权重，用于情感分析
    synonyms = db.Column(db.Text)  # 同义词列表，JSON格式存储
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式，用于API响应"""
        return {
            'id': self.id,
            'keyword': self.keyword,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'weight': self.weight,
            'synonyms': self.synonyms,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class KeywordAnalysis(db.Model):
    """
    关键词分析结果模型
    用于存储每次分析的结果
    """
    __tablename__ = 'keyword_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    analysis_date = db.Column(db.Date, nullable=False)  # 分析日期
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'))  # 关联项目
    employee_id = db.Column(db.Integer, db.ForeignKey('employee_mappings.id'))  # 关联员工
    chatroom_name = db.Column(db.String(128))  # 群聊名称
    
    # 分析结果
    total_messages = db.Column(db.Integer, default=0)  # 总消息数
    analyzed_messages = db.Column(db.Integer, default=0)  # 已分析消息数
    positive_score = db.Column(db.Float, default=0.0)  # 正面情感得分
    negative_score = db.Column(db.Float, default=0.0)  # 负面情感得分
    neutral_score = db.Column(db.Float, default=0.0)  # 中性情感得分
    overall_sentiment = db.Column(db.String(16), default='neutral')  # 整体情感倾向
    
    # 关键词统计
    keyword_stats = db.Column(db.Text)  # 关键词统计详情，JSON格式存储
    top_keywords = db.Column(db.Text)  # 高频关键词，JSON格式存储
    sentiment_trend = db.Column(db.Text)  # 情感趋势，JSON格式存储
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式，用于API响应"""
        return {
            'id': self.id,
            'analysis_date': self.analysis_date.isoformat() if self.analysis_date else None,
            'project_id': self.project_id,
            'employee_id': self.employee_id,
            'chatroom_name': self.chatroom_name,
            'total_messages': self.total_messages,
            'analyzed_messages': self.analyzed_messages,
            'positive_score': self.positive_score,
            'negative_score': self.negative_score,
            'neutral_score': self.neutral_score,
            'overall_sentiment': self.overall_sentiment,
            'keyword_stats': self.keyword_stats,
            'top_keywords': self.top_keywords,
            'sentiment_trend': self.sentiment_trend,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class MessageKeyword(db.Model):
    """
    消息关键词关联模型
    用于记录每条消息中包含的关键词
    """
    __tablename__ = 'message_keywords'
    
    id = db.Column(db.Integer, primary_key=True)
    message_seq = db.Column(db.String(64), nullable=False)  # 关联的消息序列号
    keyword_id = db.Column(db.Integer, db.ForeignKey('keywords.id'), nullable=False)  # 关联的关键词
    keyword_text = db.Column(db.String(128), nullable=False)  # 关键词文本（冗余存储）
    position = db.Column(db.Integer)  # 关键词在消息中的位置
    context = db.Column(db.Text)  # 关键词上下文
    sentiment_score = db.Column(db.Float)  # 该关键词的情感得分
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式，用于API响应"""
        return {
            'id': self.id,
            'message_seq': self.message_seq,
            'keyword_id': self.keyword_id,
            'keyword_text': self.keyword_text,
            'position': self.position,
            'context': self.context,
            'sentiment_score': self.sentiment_score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 