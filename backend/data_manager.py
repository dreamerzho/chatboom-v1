# 统一数据管理模块
# 根据新开发计划第一阶段：统一数据架构
# 整合所有数据处理逻辑，解决数据源混乱问题

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import joinedload

from backend.db import db
from models.employee import EmployeeMapping
from models.project import Project, ProjectChatroom
from models.file import FileRecord, FileVersion
from models.chat import ChatMessage
from models.keyword import KeywordCategory
from models.workload import WorkloadRecord, WorkloadWeights
from models.asset import Asset, AssetAnalysis  # 新增 Asset 模型导入
from file_validator import FileNameValidator

# 导入chatlog集成模块
from chatlog_integration import ChatlogIntegration
from chatlog_processor import ChatLogProcessor

# 导入新的解析和分析服务
from parser_service import ParserService
from analysis_service import AnalysisService

logger = logging.getLogger(__name__)

class DataManager:
    """
    统一数据管理器
    负责整合所有数据处理逻辑，包括：
    1. 聊天记录同步和处理
    2. 员工匹配和管理
    3. 文件解析和验证
    4. 项目数据管理
    5. 统计和分析
    """
    
    def __init__(self):
        """初始化数据管理器"""
        self.chatlog_integration = ChatlogIntegration()
        # self.chatlog_processor = ChatLogProcessor() # 已废弃，改为动态创建
        # 初始化新的解析和分析服务
        self.parser_service = ParserService()
        self.analysis_service = AnalysisService()
        
    def sync_project_data(self,
                          project_id: int,
                          force_resync: bool = False) -> Dict[str, Any]:
        """
        同步项目数据（统一入口）- 已重构
        此方法现在是 chatlog_integration.sync_project_chatlogs 的一个简单代理
        """
        try:
            logger.info(f"DataManager: 开始为项目ID {project_id} 调用同步流程...")

            # 完全委托给 chatlog_integration 来处理
            sync_result = self.chatlog_integration.sync_project_chatlogs(
                project_id=project_id,
                force_resync=force_resync
            )
            # 新增：同步完成后自动归档资产
            if sync_result.get('success'):
                project = Project.query.get(project_id)
                if project:
                    self._update_project_stats(project)
                    logger.info(f"DataManager: 项目ID {project_id} 的统计数据已更新。")
                    # 自动归档资产
                    self._save_sync_results(project, sync_result)
                    logger.info(f"DataManager: 项目ID {project_id} 的资产已自动归档。");

            return {
                'success': sync_result.get('success', False),
                'data': sync_result
            }
        except Exception as e:
            logger.error(f"DataManager: 同步项目ID {project_id} 数据失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _determine_group_type(self, chatroom_name: str, project_name: str) -> str:
        """
        确定群聊类型（内部/外部）
        根据群聊名称判断是内部群还是外部群
        """
        # 常见的内部群标识
        internal_indicators = ['内部', '工作群', '团队', '开发', '设计', '文案']
        # 常见的外部群标识
        external_indicators = ['外部', '客户', '对接', '沟通', '反馈']
        
        chatroom_lower = chatroom_name.lower()
        
        # 检查内部群标识
        for indicator in internal_indicators:
            if indicator in chatroom_lower:
                return 'internal'
        
        # 检查外部群标识
        for indicator in external_indicators:
            if indicator in chatroom_lower:
                return 'external'
        
        # 默认根据项目名称判断
        if project_name in chatroom_name:
            return 'internal'  # 包含项目名的通常是内部群
        else:
            return 'external'  # 不包含项目名的通常是外部群
    
    def _get_or_create_project(self, project_name: str) -> Project:
        """获取或创建项目"""
        project = Project.query.filter_by(project_name=project_name).first()
        if not project:
            project = Project(
                project_name=project_name,
                description=f"自动创建的项目: {project_name}",
                status='active',
                project_type='standard'
            )
            db.session.add(project)
            db.session.commit()
            logger.info(f"创建新项目: {project_name}")
        return project
    
    def _get_employee_mappings(self) -> List[Dict[str, Any]]:
        """获取员工映射数据"""
        employees = EmployeeMapping.query.all()
        return [emp.to_dict() for emp in employees]
    
    def _save_sync_results(self, project: Project, sync_result: Dict[str, Any]):
        """保存同步结果到数据库，使用新的 Asset 模型替代 FileRecord"""
        try:
            # 保存文件记录到 Asset 表
            for file_data in sync_result.get('file_records', []):
                # 使用 ParserService 解析文件名
                filename = file_data.get('original_name', '')
                parsed_data = self.parser_service.parse(filename)
                
                if parsed_data:
                    # 创建 Asset 记录
                    asset = Asset(
                        # 基础文件信息
                        original_name=file_data.get('original_name', ''),
                        file_path=file_data.get('file_path', ''),
                        file_size=file_data.get('file_size', 0),
                        file_md5=file_data.get('file_md5', ''),
                        file_extension=parsed_data.file_extension or file_data.get('file_extension', ''),
                        file_type=self._determine_file_type(parsed_data.file_extension),
                        file_category=self._determine_file_category(parsed_data.file_extension),
                        
                        # 解析出的结构化元数据
                        task_identifier=parsed_data.task_identifier,
                        submission_date=parsed_data.submission_date,
                        version=parsed_data.version,
                        workload_amount=parsed_data.workload_amount,
                        author_abbreviation=parsed_data.author_abbreviation,
                        
                        # 关联关系
                        author_id=file_data.get('employee_id'),
                        project_id=project.id,
                        
                        # 来源信息
                        chatroom_name=file_data.get('chatroom_name', ''),
                        message_seq=file_data.get('message_seq', ''),
                        uploader=file_data.get('uploader', ''),
                        upload_time=datetime.fromisoformat(file_data.get('upload_time', '')) if file_data.get('upload_time') else datetime.utcnow(),
                        
                        # 状态
                        status='compliant' if parsed_data.is_compliant else 'non_compliant',
                        tags=json.dumps({
                            'project_name': parsed_data.project_name,
                            'work_order': parsed_data.work_order
                        }) if parsed_data.project_name or parsed_data.work_order else None
                    )
                    
                    # 计算工作量当量 (WE)
                    asset.workload_equivalent = self.analysis_service.calculate_workload_equivalent(asset)
                    
                    # 生成任务组ID
                    asset.task_group_id = self.parser_service.generate_task_group_id(
                        parsed_data.project_name or project.project_name,
                        parsed_data.task_identifier,
                        parsed_data.author_abbreviation
                    )
                    
                    # 判断是否为最终版（简化逻辑）
                    asset.is_final_version = 'final' in filename.lower() or '最终' in filename
                    
                    db.session.add(asset)
                    
                    # 同时保存到 FileRecord 以保持向后兼容
                    file_record = FileRecord(
                        original_name=file_data.get('original_name', ''),
                        standardized_name=file_data.get('standardized_name', ''),
                        project_name=file_data.get('project_name', ''),
                        work_order=file_data.get('work_order', ''),
                        workload=file_data.get('workload', ''),
                        author_abbreviation=file_data.get('author_abbreviation', ''),
                        version=file_data.get('version', ''),
                        file_extension=file_data.get('file_extension', ''),
                        upload_time=datetime.fromisoformat(file_data.get('upload_time', '')) if file_data.get('upload_time') else datetime.utcnow(),
                        uploader=file_data.get('uploader', ''),
                        file_size=file_data.get('file_size', 0),
                        status=file_data.get('status', 'pending'),
                        chatroom_name=file_data.get('chatroom_name', ''),
                        message_seq=file_data.get('message_seq', ''),
                        employee_id=file_data.get('employee_id'),
                        project_id=project.id
                    )
                    db.session.add(file_record)
                    
                    # 自动生成工作量明细记录（保持原有逻辑）
                    self._generate_workload_record(file_record, project, parsed_data)
                else:
                    # 解析失败的文件，仍然保存到 FileRecord
                    logger.warning(f"文件名解析失败: {filename}")
                    file_record = FileRecord(
                        original_name=file_data.get('original_name', ''),
                        standardized_name=file_data.get('standardized_name', ''),
                        project_name=file_data.get('project_name', ''),
                        work_order=file_data.get('work_order', ''),
                        workload=file_data.get('workload', ''),
                        author_abbreviation=file_data.get('author_abbreviation', ''),
                        version=file_data.get('version', ''),
                        file_extension=file_data.get('file_extension', ''),
                        upload_time=datetime.fromisoformat(file_data.get('upload_time', '')) if file_data.get('upload_time') else datetime.utcnow(),
                        uploader=file_data.get('uploader', ''),
                        file_size=file_data.get('file_size', 0),
                        status='non_compliant',
                        chatroom_name=file_data.get('chatroom_name', ''),
                        message_seq=file_data.get('message_seq', ''),
                        employee_id=file_data.get('employee_id'),
                        project_id=project.id
                    )
                    db.session.add(file_record)
            
            # 保存聊天消息
            for message_data in sync_result.get('chat_messages', []):
                chat_message = ChatMessage(
                    message_id=message_data.get('message_id') or message_data.get('seq', ''),
                    talker_name=message_data.get('talker_name', ''),
                    sender_name=message_data.get('sender_name', ''),
                    message_type=message_data.get('message_type', 1),
                    content=message_data.get('content', ''),
                    timestamp=datetime.fromisoformat(message_data.get('timestamp', '')) if message_data.get('timestamp') else datetime.utcnow(),
                    project_id=project.id
                )
                db.session.add(chat_message)
            
            db.session.commit()
            logger.info(f"保存了 {len(sync_result.get('file_records', []))} 个文件记录和 {len(sync_result.get('chat_messages', []))} 条聊天消息")
            
        except Exception as e:
            logger.error(f"保存同步结果失败: {str(e)}")
            db.session.rollback()
            raise
    
    def _determine_file_type(self, file_extension: str) -> str:
        """根据文件扩展名确定文件类型"""
        if not file_extension:
            return 'other'
        
        extension = file_extension.lower()
        
        if extension in ['psd', 'ai', 'sketch', 'figma', 'xd']:
            return 'design'
        elif extension in ['doc', 'docx', 'txt', 'md']:
            return 'copywriting'
        elif extension in ['mp4', 'mov', 'avi', 'prproj']:
            return 'video'
        else:
            return 'other'
    
    def _determine_file_category(self, file_extension: str) -> str:
        """根据文件扩展名确定文件分类"""
        if not file_extension:
            return '其他'
        
        extension = file_extension.lower()
        
        if extension in ['psd', 'ai', 'sketch', 'figma', 'xd']:
            return '设计稿'
        elif extension in ['doc', 'docx', 'txt', 'md']:
            return '文案'
        elif extension in ['mp4', 'mov', 'avi', 'prproj']:
            return '视频脚本'
        else:
            return '其他'
    
    def _generate_workload_record(self, file_record: FileRecord, project: Project, parsed_data):
        """生成工作量明细记录（保持原有逻辑）"""
        try:
            # 初始化文件名验证器
            file_name_validator = FileNameValidator()
            
            # 解析文件名，获取产出类型、业务单位、数量等
            filename = file_record.original_name
            validate_result = file_name_validator.validate_filename(filename)
            parsed_info = validate_result.get('parsed_info', {}) if validate_result.get('is_compliant') else {}
            
            # 获取员工岗位
            employee_id = file_record.employee_id
            employee = EmployeeMapping.query.get(employee_id) if employee_id else None
            role = employee.role if employee else '未知'
            
            # 推断产出类型
            output_type = '最终版-' + parsed_info.get('extension', '') if parsed_info else '其他'
            
            # 业务单位与数量
            business_unit = None
            quantity = 1.0
            workload_str = parsed_info.get('workload') if parsed_info else None
            if workload_str:
                import re
                m = re.match(r'^(\d+)([a-zA-Z\u4e00-\u9fa5]*)$', workload_str)
                if m:
                    quantity = float(m.group(1))
                    business_unit = m.group(2) or None
            
            # 是否为最终版
            is_final = True if '最终' in output_type or 'final' in output_type.lower() else False
            
            # 计算WE值（查找权重表）
            we_value = 0.0
            if role != '未知' and output_type != '其他' and business_unit:
                weight = WorkloadWeights.query.filter_by(
                    role=role, 
                    output_type=output_type, 
                    business_unit=business_unit, 
                    is_final=is_final, 
                    is_active=True
                ).first()
                if weight:
                    we_value = weight.we_per_unit * quantity
            
            # 生成WorkloadRecord
            workload_record = WorkloadRecord(
                employee_id=employee_id or None,
                project_id=project.id,
                date=file_record.upload_time.date() if file_record.upload_time else datetime.utcnow().date(),
                role=role,
                output_type=output_type,
                output_value=file_record.id,
                we_value=we_value,
                is_final=is_final,
                is_iteration=False,
                iteration_count=0,
                related_file_id=file_record.id,
                related_message_id=file_record.message_seq,
                business_unit=business_unit,
                quantity=quantity,
                created_at=datetime.utcnow()
            )
            db.session.add(workload_record)
            
        except Exception as e:
            logger.error(f"生成工作量记录失败: {str(e)}")
    
    def _update_project_stats(self, project: Project):
        """更新项目统计信息"""
        try:
            # 统计消息数量
            message_count = ChatMessage.query.filter_by(project_id=project.id).count()
            
            # 统计文件数量
            file_count = FileRecord.query.filter_by(project_name=project.project_name).count()
            
            # 统计活跃员工数量
            active_employees = db.session.query(
                func.count(func.distinct(ChatMessage.sender_name))
            ).filter_by(project_id=project.id).scalar()
            
            # 获取最后活动时间
            latest_message = ChatMessage.query.filter_by(project_id=project.id).order_by(ChatMessage.timestamp.desc()).first()
            last_activity = latest_message.timestamp if latest_message else None
            
            # 更新项目统计
            project.total_messages = message_count
            project.total_files = file_count
            project.active_employees = active_employees or 0
            project.last_activity = last_activity
            project.updated_at = datetime.utcnow()
            
            db.session.commit()
            logger.info(f"更新项目 {project.project_name} 统计信息完成")
            
        except Exception as e:
            logger.error(f"更新项目统计信息失败: {str(e)}")
            db.session.rollback()
    
    def get_employee_stats(self, employee_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        获取员工统计数据
        
        参数:
            employee_id: 员工ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
        
        返回:
            员工统计数据
        """
        try:
            employee = EmployeeMapping.query.get(employee_id)
            if not employee:
                return {'success': False, 'error': '员工不存在'}
            
            # 构建查询条件
            query_conditions = [ChatMessage.sender_name == employee.wechat_nickname]
            
            if start_date:
                start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query_conditions.append(ChatMessage.timestamp >= start_datetime)
            
            if end_date:
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query_conditions.append(ChatMessage.timestamp <= end_datetime)
            
            # 统计消息数量
            message_query = ChatMessage.query.filter(*query_conditions)
            total_messages = message_query.count()
            
            # 统计文件消息
            file_messages = message_query.filter_by(message_type=49).count()
            
            # 统计图片消息
            image_messages = message_query.filter_by(message_type=3).count()
            
            # 统计文本消息
            text_messages = message_query.filter_by(message_type=1).count()
            
            # 统计活跃天数
            active_days_query = db.session.query(
                func.date(ChatMessage.timestamp).label('date')
            ).filter(*query_conditions)
            active_days = active_days_query.distinct().count()
            
            # 获取最近活跃时间
            latest_message = message_query.order_by(ChatMessage.timestamp.desc()).first()
            latest_activity = latest_message.timestamp if latest_message else None
            
            # 按项目统计
            project_stats = db.session.query(
                ChatMessage.project_id,
                func.count(ChatMessage.id).label('message_count')
            ).filter(*query_conditions).group_by(ChatMessage.project_id).all()
            
            project_details = []
            for project_id, message_count in project_stats:
                if project_id:
                    project = Project.query.get(project_id)
                    project_name = project.project_name if project else f"项目{project_id}"
                else:
                    project_name = "未分类"
                
                project_details.append({
                    'project_id': project_id,
                    'project_name': project_name,
                    'message_count': message_count
                })
            
            # 按消息数量排序
            project_details.sort(key=lambda x: x['message_count'], reverse=True)
            
            # 计算平均每天消息数
            avg_messages_per_day = round(total_messages / active_days, 2) if active_days > 0 else 0
            
            return {
                'success': True,
                'data': {
                    'employee_info': employee.to_dict(),
                    'message_stats': {
                        'total_messages': total_messages,
                        'text_messages': text_messages,
                        'image_messages': image_messages,
                        'file_messages': file_messages,
                        'avg_messages_per_day': avg_messages_per_day
                    },
                    'activity_stats': {
                        'active_days': active_days,
                        'latest_activity': latest_activity.isoformat() if latest_activity else None
                    },
                    'project_stats': project_details,
                    'time_range': {
                        'start_date': start_date,
                        'end_date': end_date
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"获取员工统计失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_project_stats(self, project_id: int) -> Dict[str, Any]:
        """
        获取项目统计数据
        
        参数:
            project_id: 项目ID
        
        返回:
            项目统计数据
        """
        try:
            project = Project.query.get(project_id)
            if not project:
                return {'success': False, 'error': '项目不存在'}
            
            # 获取项目消息统计
            message_stats = db.session.query(
                ChatMessage.message_type,
                func.count(ChatMessage.id).label('count')
            ).filter_by(project_id=project_id).group_by(ChatMessage.message_type).all()
            
            # 获取活跃员工统计
            employee_stats = db.session.query(
                ChatMessage.sender_name,
                func.count(ChatMessage.id).label('message_count')
            ).filter_by(project_id=project_id).group_by(ChatMessage.sender_name).order_by(
                func.count(ChatMessage.id).desc()
            ).limit(10).all()
            
            # 获取文件统计
            file_stats = db.session.query(
                FileRecord.status,
                func.count(FileRecord.id).label('count')
            ).filter_by(project_name=project.project_name).group_by(FileRecord.status).all()
            
            # 获取最近活动
            recent_messages = ChatMessage.query.filter_by(project_id=project_id).order_by(
                ChatMessage.timestamp.desc()
            ).limit(10).all()
            
            return {
                'success': True,
                'data': {
                    'project_info': project.to_dict(),
                    'message_stats': dict(message_stats),
                    'employee_stats': [
                        {
                            'sender_name': sender_name,
                            'message_count': message_count
                        } for sender_name, message_count in employee_stats
                    ],
                    'file_stats': dict(file_stats),
                    'recent_messages': [
                        {
                            'sender_name': msg.sender_name,
                            'content': msg.content[:100] + '...' if len(msg.content) > 100 else msg.content,
                            'timestamp': msg.timestamp.isoformat(),
                            'message_type': msg.message_type
                        } for msg in recent_messages
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"获取项目统计失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_unmapped_senders(self) -> Dict[str, Any]:
        """
        获取未映射的微信用户列表
        
        返回:
            未映射用户列表
        """
        try:
            # 获取所有已映射的微信昵称
            mapped_nicknames = db.session.query(EmployeeMapping.wechat_nickname).all()
            mapped_nicknames_set = {nickname[0] for nickname in mapped_nicknames}
            
            # 获取所有聊天记录中的发送者昵称
            all_senders = db.session.query(ChatMessage.sender_name).distinct().all()
            all_senders_set = {sender[0] for sender in all_senders if sender[0]}
            
            # 找出未映射的发送者
            unmapped_senders = all_senders_set - mapped_nicknames_set
            
            # 统计每个未映射发送者的消息数量
            unmapped_senders_with_stats = []
            for sender in unmapped_senders:
                message_count = ChatMessage.query.filter_by(sender_name=sender).count()
                unmapped_senders_with_stats.append({
                    'sender_name': sender,
                    'message_count': message_count
                })
            
            # 按消息数量降序排列
            unmapped_senders_with_stats.sort(key=lambda x: x['message_count'], reverse=True)
            
            return {
                'success': True,
                'data': {
                    'unmapped_senders': unmapped_senders_with_stats,
                    'total_count': len(unmapped_senders_with_stats),
                    'mapped_count': len(mapped_nicknames_set),
                    'total_senders': len(all_senders_set)
                }
            }
            
        except Exception as e:
            logger.error(f"获取未映射用户列表失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def batch_add_employee_mappings(self, mappings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量添加员工映射
        
        参数:
            mappings: 员工映射列表
        
        返回:
            批量添加结果
        """
        try:
            # 验证数据格式
            for mapping in mappings:
                required_fields = ['wechat_nickname', 'real_name', 'position', 'name_abbreviation']
                for field in required_fields:
                    if field not in mapping or not mapping[field]:
                        return {'success': False, 'error': f'缺少必填字段: {field}'}
            
            # 检查重复
            wechat_nicknames = [m['wechat_nickname'] for m in mappings]
            existing_employees = EmployeeMapping.query.filter(
                EmployeeMapping.wechat_nickname.in_(wechat_nicknames)
            ).all()
            
            if existing_employees:
                existing_names = [emp.wechat_nickname for emp in existing_employees]
                return {
                    'success': False,
                    'error': f'以下微信昵称已存在: {", ".join(existing_names)}'
                }
            
            # 批量创建
            created_employees = []
            for mapping_data in mappings:
                employee = EmployeeMapping(
                    wechat_nickname=mapping_data['wechat_nickname'],
                    real_name=mapping_data['real_name'],
                    position=mapping_data['position'],
                    name_abbreviation=mapping_data['name_abbreviation'],
                    role=mapping_data.get('role', '内部员工')
                )
                db.session.add(employee)
                created_employees.append(employee)
            
            db.session.commit()
            
            return {
                'success': True,
                'data': {
                    'created_count': len(created_employees),
                    'employees': [emp.to_dict() for emp in created_employees]
                },
                'message': f'成功创建 {len(created_employees)} 个员工映射'
            }
            
        except Exception as e:
            logger.error(f"批量添加员工映射失败: {str(e)}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def get_employee_full_stats(self, employee_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        统一聚合员工统计数据
        - 同时聚合产出（工作量、WE、岗位分布等）与沟通（消息数、文件数、活跃天数等）所有核心统计字段
        - 便于前端一次性获取全部员工相关统计数据
        - 参数：employee_id 员工ID，start_date 开始日期，end_date 结束日期
        - 返回：success, data（包含产出与沟通统计）
        """
        try:
            # 产出类统计（调用 get_employee_workload_stats 逻辑）
            workload_stats = self._get_employee_workload_stats_internal(employee_id, start_date, end_date)
            # 沟通类统计（调用 get_employee_stats 逻辑）
            comm_stats = self.get_employee_stats(employee_id, start_date, end_date)
            if not workload_stats['success']:
                return {'success': False, 'error': workload_stats.get('error', '产出统计失败')}
            if not comm_stats['success']:
                return {'success': False, 'error': comm_stats.get('error', '沟通统计失败')}
            # 合并结构，字段对齐
            return {
                'success': True,
                'data': {
                    'employee_info': comm_stats['data']['employee_info'],
                    '产出统计': workload_stats['data'],
                    '沟通统计': comm_stats['data']
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _get_employee_workload_stats_internal(self, employee_id: int, start_date: Optional[str], end_date: Optional[str]) -> Dict[str, Any]:
        """
        内部方法：复用 get_employee_workload_stats 的聚合逻辑，便于统一聚合API调用
        """
        try:
            # 获取时间范围参数
            if not start_date:
                start_date_obj = datetime.today().date() - timedelta(days=30)
            else:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            if not end_date:
                end_date_obj = datetime.today().date()
            else:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            # 获取员工信息
            employee = EmployeeMapping.query.filter(EmployeeMapping.id == employee_id).first()
            if not employee:
                return {'success': False, 'error': '员工不存在'}
            # 获取工作量记录
            records = WorkloadRecord.query.filter(
                and_(
                    WorkloadRecord.employee_id == employee_id,
                    WorkloadRecord.date >= start_date_obj,
                    WorkloadRecord.date <= end_date_obj
                )
            ).all()
            # 统计数据
            total_we = sum(record.we_value for record in records)
            total_records = len(records)
            final_records = sum(1 for record in records if record.is_final)
            iteration_records = sum(1 for record in records if record.is_iteration)
            role_stats = {}
            for record in records:
                role = record.role
                if role not in role_stats:
                    role_stats[role] = {
                        'total_we': 0,
                        'record_count': 0,
                        'final_count': 0
                    }
                role_stats[role]['total_we'] += record.we_value
                role_stats[role]['record_count'] += 1
                if record.is_final:
                    role_stats[role]['final_count'] += 1
            # 负荷指数（如有分析服务可调用）
            load_index = 0
            try:
                load_index = self.analysis_service.calculate_employee_load_index(employee_id, start_date_obj, end_date_obj)
            except Exception:
                pass
            return {
                'success': True,
                'data': {
                    'period': {
                        'start_date': start_date_obj.isoformat(),
                        'end_date': end_date_obj.isoformat(),
                        'days': (end_date_obj - start_date_obj).days + 1
                    },
                    'summary': {
                        'total_we': round(total_we, 2),
                        'total_records': total_records,
                        'final_records': final_records,
                        'iteration_records': iteration_records,
                        'avg_we_per_day': round(total_we / max(1, (end_date_obj - start_date_obj).days + 1), 2)
                    },
                    'role_stats': role_stats,
                    'load_index': load_index
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

# 创建全局数据管理器实例
data_manager = DataManager() 