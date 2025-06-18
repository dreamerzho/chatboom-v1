# 关键词相关数据模型
# 包含关键词分类、权重等模型定义

from datetime import datetime
from db import db

class KeywordCategory(db.Model):
    """
    关键词分类模型
    用于管理关键词分析的相关配置
    支持关键词分类和权重设置
    """
    __tablename__ = 'keyword_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(64), nullable=False)  # 分类名称（如：正面词、负面词）
    keyword = db.Column(db.String(64), nullable=False)  # 关键词
    weight = db.Column(db.Integer, default=1)  # 权重
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 确保分类名和关键词的组合唯一
    __table_args__ = (db.UniqueConstraint('category_name', 'keyword', name='_category_keyword_uc'),)
    
    def to_dict(self):
        """转换为字典格式，用于API响应"""
        return {
            'id': self.id,
            'category_name': self.category_name,
            'keyword': self.keyword,
            'weight': self.weight,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 