# 项目健康度与风险预警相关数据模型
# 包含项目健康度统计等模型定义
# 支持V2精准评估模型的项目健康度分析和智能风险预警

from datetime import datetime
try:
    from db import db
except ImportError:
    from backend.db import db

class ProjectHealthStats(db.Model):
    """
    项目健康度统计表
    每条记录代表某项目在某统计周期内的健康度快照
    """
    __tablename__ = 'project_health_stats'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)  # 项目ID
    period = db.Column(db.String(16), nullable=False)  # 统计周期（如7d/30d/90d）
    health_score = db.Column(db.Integer, nullable=False)  # 健康分
    avg_time_to_final = db.Column(db.Float)  # 平均定稿周期（小时）
    avg_revisions = db.Column(db.Float)  # 平均迭代次数
    risk_count = db.Column(db.Integer, default=0)  # 风险事件数
    warning_count = db.Column(db.Integer, default=0)  # 预警事件数
    negative_sentiment_rate = db.Column(db.Float)  # 负面情绪频率
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    project = db.relationship('Project', backref='health_stats')
    
    def to_dict(self):
        """转换为字典格式，用于API响应"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'project_name': self.project.project_name if self.project else None,
            'period': self.period,
            'health_score': self.health_score,
            'avg_time_to_final': self.avg_time_to_final,
            'avg_revisions': self.avg_revisions,
            'risk_count': self.risk_count,
            'warning_count': self.warning_count,
            'negative_sentiment_rate': self.negative_sentiment_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ProjectDifficultyIndex(db.Model):
    """
    项目难度指数模型
    用于记录和评估不同项目的客观难度
    支持智能返工归因和项目难度预警
    """
    __tablename__ = 'project_difficulty_indices'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)  # 项目ID
    
    # 难度评估指标
    complexity_score = db.Column(db.Float, default=50.0)  # 复杂度评分 (0-100)
    client_difficulty = db.Column(db.Float, default=50.0)  # 客户难度评分
    requirement_clarity = db.Column(db.Float, default=50.0)  # 需求明确度评分
    timeline_pressure = db.Column(db.Float, default=50.0)  # 时间压力评分
    resource_adequacy = db.Column(db.Float, default=50.0)  # 资源充足度评分
    
    # 统计数据支撑
    avg_employee_revisions = db.Column(db.Float, default=0.0)  # 项目内员工平均迭代次数
    team_baseline_revisions = db.Column(db.Float, default=0.0)  # 团队基线平均迭代次数
    difficulty_ratio = db.Column(db.Float, default=1.0)  # 难度比率（项目迭代/基线迭代）
    outlier_employees = db.Column(db.Integer, default=0)  # 异常员工数（迭代远超基线）
    
    # 历史对比
    similar_projects_avg = db.Column(db.Float, default=0.0)  # 同类项目平均难度
    industry_benchmark = db.Column(db.Float, default=0.0)  # 行业基准
    
    calculation_date = db.Column(db.Date, nullable=False)  # 计算日期
    is_active = db.Column(db.Boolean, default=True)  # 是否为当前有效难度评估
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    project = db.relationship('Project', backref='difficulty_indices')
    
    def to_dict(self):
        """转换为字典格式，用于API响应"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'project_name': self.project.project_name if self.project else None,
            'complexity_score': self.complexity_score,
            'client_difficulty': self.client_difficulty,
            'requirement_clarity': self.requirement_clarity,
            'timeline_pressure': self.timeline_pressure,
            'resource_adequacy': self.resource_adequacy,
            'avg_employee_revisions': self.avg_employee_revisions,
            'team_baseline_revisions': self.team_baseline_revisions,
            'difficulty_ratio': self.difficulty_ratio,
            'outlier_employees': self.outlier_employees,
            'similar_projects_avg': self.similar_projects_avg,
            'industry_benchmark': self.industry_benchmark,
            'calculation_date': self.calculation_date.isoformat() if self.calculation_date else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 