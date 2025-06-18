# 文件相关数据模型
# 包含文件记录、文件命名规范验证等模型定义

from datetime import datetime
from db import db

class FileRecord(db.Model):
    """
    文件记录模型
    用于管理聊天记录中的文件信息
    支持文件命名规范验证和状态管理
    """
    __tablename__ = 'file_records'
    
    id = db.Column(db.Integer, primary_key=True)
    original_name = db.Column(db.String(256), nullable=False)  # 原始文件名
    standardized_name = db.Column(db.String(256), nullable=False)  # 标准化文件名
    project_name = db.Column(db.String(128), nullable=False)  # 项目名称
    work_order = db.Column(db.String(128))  # 工单名/内容描述
    workload = db.Column(db.String(32))  # 工作量
    author_abbreviation = db.Column(db.String(16), nullable=False)  # 作者缩写
    version = db.Column(db.String(32))  # 版本号
    file_extension = db.Column(db.String(16), nullable=False)  # 文件扩展名
    upload_time = db.Column(db.DateTime, nullable=False)  # 上传时间
    uploader = db.Column(db.String(128), nullable=False)  # 上传者
    file_size = db.Column(db.String(32))  # 文件大小
    file_path = db.Column(db.String(256))  # 文件路径
    status = db.Column(db.String(32), default='pending')  # 文件状态：pending/compliant/non_compliant
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式，用于API响应"""
        return {
            'id': self.id,
            'original_name': self.original_name,
            'standardized_name': self.standardized_name,
            'project_name': self.project_name,
            'work_order': self.work_order,
            'workload': self.workload,
            'author_abbreviation': self.author_abbreviation,
            'version': self.version,
            'file_extension': self.file_extension,
            'upload_time': self.upload_time.isoformat() if self.upload_time else None,
            'uploader': self.uploader,
            'file_size': self.file_size,
            'file_path': self.file_path,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 