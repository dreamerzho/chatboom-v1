# 工作量当量（WE）相关数据模型
# 包含工作量明细记录、员工能力基线等模型定义
# 支持V2精准评估模型的WE计算和负荷指数分析

from datetime import datetime
try:
    from db import db
except ImportError:
    from backend.db import db

class WorkloadRecord(db.Model):
    """
    工作量明细记录模型
    用于记录每个员工的所有产出和行为，并计算对应的WE值
    支持按岗位、产出类型、项目等维度进行负荷分析
    """
    __tablename__ = 'workload_records'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee_mappings.id'), nullable=False)  # 员工ID
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)  # 项目ID
    date = db.Column(db.Date, nullable=False)  # 工作日期
    role = db.Column(db.String(32), nullable=False)  # 岗位类型：设计/文案/PM/AE
    output_type = db.Column(db.String(64), nullable=False)  # 产出类型：最终版-海报/过程迭代版本/内部修改意见/外部群沟通等
    output_value = db.Column(db.String(256))  # 产出内容标识（文件ID、消息ID等）
    we_value = db.Column(db.Float, nullable=False, default=0.0)  # 本条记录的WE数值
    is_final = db.Column(db.Boolean, default=False)  # 是否为最终版产出
    is_iteration = db.Column(db.Boolean, default=False)  # 是否为迭代过程
    iteration_count = db.Column(db.Integer, default=0)  # 迭代次数（针对创意岗位）
    related_file_id = db.Column(db.Integer, db.ForeignKey('file_records.id'))  # 关联文件记录
    related_message_id = db.Column(db.String(128))  # 关联消息ID
    business_unit = db.Column(db.String(64))  # 业务单位（如P、篇、套、次等）
    quantity = db.Column(db.Float, default=1.0)  # 数量
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    employee = db.relationship('EmployeeMapping', backref='workload_records')
    project = db.relationship('Project', backref='workload_records')
    file_record = db.relationship('FileRecord', backref='workload_records')
    
    def to_dict(self):
        """转换为字典格式，用于API响应"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.real_name if self.employee else None,
            'project_id': self.project_id,
            'project_name': self.project.project_name if self.project else None,
            'date': self.date.isoformat() if self.date else None,
            'role': self.role,
            'output_type': self.output_type,
            'output_value': self.output_value,
            'we_value': self.we_value,
            'is_final': self.is_final,
            'is_iteration': self.is_iteration,
            'iteration_count': self.iteration_count,
            'related_file_id': self.related_file_id,
            'related_message_id': self.related_message_id,
            'business_unit': self.business_unit,
            'quantity': self.quantity,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class EmployeeLoadBaseline(db.Model):
    """
    员工能力基线模型
    用于记录每个员工的长期平均能力水平
    支持智能返工归因和项目难度预警
    """
    __tablename__ = 'employee_load_baselines'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee_mappings.id'), nullable=False)  # 员工ID
    role = db.Column(db.String(32), nullable=False)  # 岗位类型
    avg_revisions = db.Column(db.Float, default=0.0)  # 长期平均迭代次数
    avg_we_per_day = db.Column(db.Float, default=0.0)  # 平均每日WE产出
    avg_final_we = db.Column(db.Float, default=0.0)  # 平均最终版WE
    avg_process_we = db.Column(db.Float, default=0.0)  # 平均过程成本WE
    total_projects = db.Column(db.Integer, default=0)  # 参与项目总数
    total_outputs = db.Column(db.Integer, default=0)  # 总产出数量
    period_days = db.Column(db.Integer, default=90)  # 统计周期（天数）
    calculation_date = db.Column(db.Date, nullable=False)  # 计算日期
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    employee = db.relationship('EmployeeMapping', backref='load_baselines')
    
    def to_dict(self):
        """转换为字典格式，用于API响应"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.real_name if self.employee else None,
            'role': self.role,
            'avg_revisions': self.avg_revisions,
            'avg_we_per_day': self.avg_we_per_day,
            'avg_final_we': self.avg_final_we,
            'avg_process_we': self.avg_process_we,
            'total_projects': self.total_projects,
            'total_outputs': self.total_outputs,
            'period_days': self.period_days,
            'calculation_date': self.calculation_date.isoformat() if self.calculation_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class WorkloadWeights(db.Model):
    """
    工作量当量权重配置模型
    用于存储不同岗位、不同产出类型的WE换算规则
    支持V2模型的动态权重调整
    """
    __tablename__ = 'workload_weights'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(32), nullable=False)  # 岗位：文案/设计/PM/AE
    output_type = db.Column(db.String(64), nullable=False)  # 产出类型
    business_unit = db.Column(db.String(32), nullable=False)  # 业务单位：篇/P/套/次等
    we_per_unit = db.Column(db.Float, nullable=False)  # 每单位WE值
    is_final = db.Column(db.Boolean, default=True)  # 是否为最终版
    iteration_multiplier = db.Column(db.Float, default=1.0)  # 迭代倍数（过程版本用）
    description = db.Column(db.Text)  # 规则描述
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式，用于API响应"""
        return {
            'id': self.id,
            'role': self.role,
            'output_type': self.output_type,
            'business_unit': self.business_unit,
            'we_per_unit': self.we_per_unit,
            'is_final': self.is_final,
            'iteration_multiplier': self.iteration_multiplier,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }