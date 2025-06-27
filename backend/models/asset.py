# 数字资产模型 - 核心数据实体
# 这是专家建议的新架构核心，用于替代当前的 File 实体
# 支持文件名解析、版本追溯、工作量计算等高级功能

from datetime import datetime
try:
    from db import db
except ImportError:
    from backend.db import db

class Asset(db.Model):
    """
    数字资产模型 - 核心业务实体
    用于管理从聊天记录中提取的所有数字资产
    支持文件名解析、版本追溯、工作量计算和效率分析
    """
    __tablename__ = 'assets'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # --- 基础文件信息 ---
    original_name = db.Column(db.String(256), nullable=False)  # 原始文件名
    file_path = db.Column(db.String(512))  # 文件路径
    file_size = db.Column(db.BigInteger)  # 文件大小（字节）
    file_md5 = db.Column(db.String(32))  # 文件MD5值，用于去重
    file_extension = db.Column(db.String(16), nullable=False)  # 文件扩展名
    file_type = db.Column(db.String(32))  # 文件类型：document/image/video/audio/other
    file_category = db.Column(db.String(64))  # 文件分类：设计稿/文案/视频脚本/其他
    
    # --- 由 ParserService 解析出的结构化元数据 ---
    task_identifier = db.Column(db.String(256), nullable=False)  # 任务标识符，如 "金陵中環-热销系列海报"
    submission_date = db.Column(db.Date, nullable=False)  # 提交日期, YYYY-MM-DD
    version = db.Column(db.Integer, nullable=False, default=1)  # 版本号, e.g., 1, 2, 3
    workload_amount = db.Column(db.String(32))  # 工作量描述, e.g., "3p", "5条"
    author_abbreviation = db.Column(db.String(16), nullable=False)  # 作者缩写
    
    # --- 关联关系 ---
    author_id = db.Column(db.Integer, db.ForeignKey('employee_mappings.id'))  # 作者 (关联到 EmployeeMapping)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))  # 所属项目 (关联到 Project)
    
    # --- 由 AnalysisService 计算出的分析指标 ---
    workload_equivalent = db.Column(db.Float)  # 工作量当量 (WE)
    is_final_version = db.Column(db.Boolean, default=False)  # 是否为最终版
    time_to_final = db.Column(db.Float)  # (仅最终版有值) 定稿周期（天）
    
    # --- 版本追溯和任务关联 ---
    task_group_id = db.Column(db.String(64))  # 任务组ID，用于关联同一任务的多个版本
    parent_asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'))  # 父版本资产ID
    
    # --- 来源信息 ---
    chatroom_name = db.Column(db.String(128))  # 来源群聊名称
    message_seq = db.Column(db.String(64))  # 关联的消息序列号
    uploader = db.Column(db.String(128), nullable=False)  # 上传者
    upload_time = db.Column(db.DateTime, nullable=False)  # 上传时间
    
    # --- 状态和标签 ---
    status = db.Column(db.String(32), default='pending')  # 文件状态：pending/compliant/non_compliant
    tags = db.Column(db.Text)  # 文件标签，JSON格式存储
    is_archived = db.Column(db.Boolean, default=False)  # 是否已归档
    archive_path = db.Column(db.String(256))  # 归档路径
    
    # --- 时间戳 ---
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # --- 关系定义 ---
    author = db.relationship('EmployeeMapping', backref='assets')
    project = db.relationship('Project', backref='assets')
    parent_asset = db.relationship('Asset', remote_side=[id], backref='child_versions')
    
    def to_dict(self):
        """转换为字典格式，用于API响应"""
        return {
            'id': self.id,
            'original_name': self.original_name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_md5': self.file_md5,
            'file_extension': self.file_extension,
            'file_type': self.file_type,
            'file_category': self.file_category,
            'task_identifier': self.task_identifier,
            'submission_date': self.submission_date.isoformat() if self.submission_date else None,
            'version': self.version,
            'workload_amount': self.workload_amount,
            'author_abbreviation': self.author_abbreviation,
            'author_id': self.author_id,
            'project_id': self.project_id,
            'workload_equivalent': self.workload_equivalent,
            'is_final_version': self.is_final_version,
            'time_to_final': self.time_to_final,
            'task_group_id': self.task_group_id,
            'parent_asset_id': self.parent_asset_id,
            'chatroom_name': self.chatroom_name,
            'message_seq': self.message_seq,
            'uploader': self.uploader,
            'upload_time': self.upload_time.isoformat() if self.upload_time else None,
            'status': self.status,
            'tags': self.tags,
            'is_archived': self.is_archived,
            'archive_path': self.archive_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            # 关联对象信息
            'author_info': self.author.to_dict() if self.author else None,
            'project_info': self.project.to_dict() if self.project else None
        }

class AssetAnalysis(db.Model):
    """
    资产分析结果模型
    用于存储对单个资产的分析结果，支持缓存和性能优化
    """
    __tablename__ = 'asset_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False, unique=True)
    
    # --- 分析指标 ---
    quality_score = db.Column(db.Float)  # 质量评分 (0-100)
    efficiency_score = db.Column(db.Float)  # 效率评分 (0-100)
    iteration_count = db.Column(db.Integer, default=1)  # 迭代次数
    rework_factor = db.Column(db.Float)  # 返工因子
    complexity_score = db.Column(db.Float)  # 复杂度评分
    
    # --- 时间分析 ---
    first_submission_time = db.Column(db.DateTime)  # 首次提交时间
    final_submission_time = db.Column(db.DateTime)  # 最终提交时间
    total_work_time = db.Column(db.Float)  # 总工作时间（小时）
    
    # --- 分析详情（JSON格式） ---
    analysis_details = db.Column(db.Text)  # 详细分析结果
    risk_factors = db.Column(db.Text)  # 风险因素
    improvement_suggestions = db.Column(db.Text)  # 改进建议
    
    # --- 时间戳 ---
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # --- 关系定义 ---
    asset = db.relationship('Asset', backref='analysis')
    
    def to_dict(self):
        """转换为字典格式，用于API响应"""
        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'quality_score': self.quality_score,
            'efficiency_score': self.efficiency_score,
            'iteration_count': self.iteration_count,
            'rework_factor': self.rework_factor,
            'complexity_score': self.complexity_score,
            'first_submission_time': self.first_submission_time.isoformat() if self.first_submission_time else None,
            'final_submission_time': self.final_submission_time.isoformat() if self.final_submission_time else None,
            'total_work_time': self.total_work_time,
            'analysis_details': self.analysis_details,
            'risk_factors': self.risk_factors,
            'improvement_suggestions': self.improvement_suggestions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 