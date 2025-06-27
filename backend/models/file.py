# 文件相关数据模型
# 包含文件记录、文件命名规范验证等模型定义

from datetime import datetime
from db import db
from sqlalchemy import UniqueConstraint

class FileRecord(db.Model):
    """
    文件记录模型
    用于管理聊天记录中的文件信息
    支持文件命名规范验证、版本控制和分类管理
    基于 message_seq 和 original_name 进行去重
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
    file_size = db.Column(db.BigInteger)  # 文件大小（字节）
    file_md5 = db.Column(db.String(32))  # 文件MD5值，用于去重
    file_path = db.Column(db.String(256))  # 文件路径
    status = db.Column(db.String(32), default='pending')  # 文件状态：pending/compliant/non_compliant
    file_type = db.Column(db.String(32))  # 文件类型：document/image/video/audio/other
    file_category = db.Column(db.String(64))  # 文件分类：设计稿/文案/视频脚本/其他
    tags = db.Column(db.Text)  # 文件标签，JSON格式存储
    is_archived = db.Column(db.Boolean, default=False)  # 是否已归档
    archive_path = db.Column(db.String(256))  # 归档路径
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    duration_hours = db.Column(db.Float, nullable=True)  # 工时（小时），同一任务多版本时间差
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)  # 关联项目ID，可为空
    
    # 关联字段
    employee_id = db.Column(db.Integer, db.ForeignKey('employee_mappings.id'))  # 关联员工
    chatroom_name = db.Column(db.String(128))  # 来源群聊名称
    message_seq = db.Column(db.String(64))  # 关联的消息序列号
    
    # 复合唯一约束：确保同一消息中的同一文件不会重复记录
    __table_args__ = (
        UniqueConstraint('message_seq', 'original_name', name='uq_message_file'),
    )
    
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
            'file_md5': self.file_md5,
            'file_path': self.file_path,
            'status': self.status,
            'file_type': self.file_type,
            'file_category': self.file_category,
            'tags': self.tags,
            'is_archived': self.is_archived,
            'archive_path': self.archive_path,
            'employee_id': self.employee_id,
            'chatroom_name': self.chatroom_name,
            'message_seq': self.message_seq,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'duration_hours': self.duration_hours
        }

class FileVersion(db.Model):
    """
    文件版本控制模型
    用于管理同一文件的不同版本
    """
    __tablename__ = 'file_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    file_record_id = db.Column(db.Integer, db.ForeignKey('file_records.id'), nullable=False)
    version_number = db.Column(db.String(32), nullable=False)  # 版本号
    file_path = db.Column(db.String(256), nullable=False)  # 文件路径
    file_size = db.Column(db.BigInteger)  # 文件大小
    file_md5 = db.Column(db.String(32))  # 文件MD5
    upload_time = db.Column(db.DateTime, nullable=False)  # 上传时间
    uploader = db.Column(db.String(128), nullable=False)  # 上传者
    change_description = db.Column(db.Text)  # 版本变更描述
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式，用于API响应"""
        return {
            'id': self.id,
            'file_record_id': self.file_record_id,
            'version_number': self.version_number,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_md5': self.file_md5,
            'upload_time': self.upload_time.isoformat() if self.upload_time else None,
            'uploader': self.uploader,
            'change_description': self.change_description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 