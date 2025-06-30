#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天记录处理器
负责解析聊天记录中的文件信息、去重、人员关联等功能
整合了旧chat_parser.py中的核心功能
基于 seq 字段进行高效去重
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Callable
from difflib import SequenceMatcher
import json
import os
from backend.models.project import Project
from backend.models.unmatched_person import UnmatchedPerson
from backend.models.file import FileRecord
from backend.models.chat import ChatMessage
from backend.models.employee import EmployeeMapping
from backend.db import db
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import and_, or_
# from backend.chatlog_integration import ChatlogIntegration  # 移除顶部导入，避免循环依赖

logger = logging.getLogger(__name__)

# 定义聊天记录文件存放的基础路径
CHATLOG_BASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'basefiles')

class ChatMessageParser:
    """
    聊天记录解析器 - 重构版
    使用正则表达式替代XML解析，提高健壮性
    """
    
    def __init__(self):
        """初始化解析器"""
        self.message_types = {
            1: "文本消息",
            3: "图片消息", 
            34: "语音消息",
            43: "视频消息",
            47: "动画表情",
            49: "多媒体消息",  # 包含文件、链接等
            10000: "系统消息"
        }
        
        # 定义正则表达式，用于从混乱的content中提取文件名
        # 寻找 <title> 和 </title> 之间的内容
        self.filename_regex = re.compile(r'<title>(.*?)</title>', re.DOTALL)
        
        # 定义文件扩展名正则，用于识别文件类型
        self.file_extension_regex = re.compile(r'\.([a-zA-Z0-9]+)$')
        
        # 定义文件名解析正则，支持多种格式
        self.filename_parse_regex = re.compile(
            r'^(\d{6})-([^-]+)-([^-]+)-([^-]+)-([^-]+)-v?(\d+(?:\.\d+)*)\.([a-zA-Z0-9]+)$'
        )

    def _parse_multimedia_content(self, content: str) -> Dict[str, Any]:
        """
        【核心修复】解析多媒体消息内容 (type: 49)
        使用正则表达式替代XML解析，提高健壮性
        """
        parsed_data = {
            'type': '多媒体',
            'raw_content': content,
            'filename': None,
            'subtype': '未知多媒体',
            'file_extension': None
        }
        
        try:
            # 尝试使用正则表达式从content中提取文件名
            match = self.filename_regex.search(content)
            if match:
                # 如果匹配成功，提取到的就是文件名
                filename = match.group(1).strip()
                parsed_data['filename'] = filename
                parsed_data['subtype'] = '文件'
                
                # 提取文件扩展名
                ext_match = self.file_extension_regex.search(filename)
                if ext_match:
                    parsed_data['file_extension'] = ext_match.group(1).lower()
                
                logger.info(f"成功从多媒体消息中解析出文件名: {filename}")
            else:
                # 如果正则匹配失败，记录原始内容用于调试
                logger.warning(f"无法从多媒体消息中解析出文件名。Content预览: {content[:200]}...")
                
        except Exception as e:
            logger.error(f"解析多媒体消息时发生错误: {str(e)}")
            parsed_data['error'] = str(e)

        return parsed_data

    def parse_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析单条聊天记录
        """
        try:
            msg_type = message.get('type', 0)
            parsed_content = {}
            
            if msg_type == 1:
                parsed_content['type'] = '文本'
                parsed_content['text'] = message.get('content', '')
                parsed_content['word_count'] = len(parsed_content['text'])
            elif msg_type == 49:
                parsed_content.update(self._parse_multimedia_content(message.get('content', '')))
            else:
                parsed_content['type'] = self.message_types.get(msg_type, '未知类型')
                parsed_content['raw'] = message.get('content', '')

            return {
                'seq': message.get('seq'),
                'time': message.get('time'),
                'talker': message.get('talker'),
                'talker_name': message.get('talkerName'),
                'sender': message.get('sender'),
                'sender_name': message.get('senderName'),
                'is_self': message.get('isSelf', False),
                'type': msg_type,
                'sub_type': message.get('subType'),
                'parsed_content': parsed_content,
            }
            
        except Exception as e:
            logger.error(f"解析消息失败: {str(e)}, 消息: {message}")
            return message

class ChatLogProcessor:
    """
    聊天记录处理器 - 重构版
    负责对整个聊天记录列表进行处理，包括去重、关联等
    基于 chatlog 的 seq 字段进行高效去重
    """
    
    def __init__(self, project_id: int, date_str: Optional[str] = None, yield_log: Optional[Callable[[str], None]] = None):
        """
        初始化处理器
        :param project_id: 要处理的项目ID
        :param date_str: 要处理的特定日期 (YYYYMMDD)，如果为None则处理所有
        :param yield_log: 用于流式返回日志的回调函数
        """
        self.parser = ChatMessageParser()
        self.project_id = project_id
        self.date_str = date_str
        self.yield_log = yield_log or (lambda msg: logger.info(msg))
        self.employees = self._load_employees()

    def _log(self, message: str):
        """记录并可能发送日志"""
        logger.info(message)
        if self.yield_log:
            self.yield_log(message)

    def _load_employees(self) -> List[Dict[str, Any]]:
        """从数据库加载员工映射信息"""
        self._log("正在从数据库加载员工信息...")
        employees = EmployeeMapping.query.all()
        employee_list = [
            {
                'id': emp.id,
                'wechat_nickname': emp.wechat_nickname,
                'real_name': emp.real_name,
                'name_abbreviation': emp.name_abbreviation,
                'position': emp.position
            }
            for emp in employees
        ]
        self._log(f"成功加载 {len(employee_list)} 条员工信息。")
        return employee_list

    def process_chatlogs(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        处理并同步项目的聊天记录（只通过chatlogAPI获取）
        基于 seq 字段进行高效去重，使用数据库级别的 UPSERT 操作
        步骤：
        1. 读取项目的所有群昵称（chatroom_name），遍历每个群聊。
        2. 对每个群聊，调用chatlogAPI拉取消息（get_chatlog_by_talker_and_time），按时间段。
        3. 用process_and_deduplicate处理消息，批量入库ChatMessage和FileRecord。
        4. 统计消息数、文件数，返回真实统计。
        5. 日志详细，异常处理健壮。
        
        参数:
            start_date: 开始日期 (YYYY-MM-DD)，如果为None则使用最近7天
            end_date: 结束日期 (YYYY-MM-DD)，如果为None则使用今天
        """
        from backend.models.project import Project, ProjectChatroom
        from backend.models.chat import ChatMessage
        from backend.models.file import FileRecord
        from backend.db import db
        import traceback
        
        self._log(f"--- 开始处理项目ID: {self.project_id} 的聊天记录 ---")
        try:
            project = Project.query.get(self.project_id)
            if not project:
                self._log(f"未找到项目ID: {self.project_id}")
                return {'success': False, 'message': f'未找到项目ID: {self.project_id}', 'logs': []}
            
            # 获取所有群聊昵称
            chatrooms = project.chatrooms.all()
            if not chatrooms:
                self._log(f"项目未配置任何群聊，无法同步")
                return {'success': False, 'message': '项目未配置任何群聊', 'logs': []}
            
            # 设置时间范围
            from datetime import datetime, timedelta
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            self._log(f"📅 同步时间范围: {start_date} ~ {end_date}")
            
            chatlog_client = ChatlogIntegration()
            total_messages = 0
            total_files = 0
            all_new_msgs = []
            all_new_files = []
            
            for chatroom in chatrooms:
                group_name = chatroom.chatroom_name
                group_type = chatroom.chatroom_type
                self._log(f"同步群聊：{group_name}（类型：{group_type}）...")
                
                # 拉取该群的消息
                msgs = chatlog_client.get_chatlog_by_talker_and_time(
                    talker=group_name,
                    start_date=start_date,
                    end_date=end_date
                )
                self._log(f"获取到 {len(msgs)} 条消息，开始解析...")
                
                group_info = {'name': group_name, 'type': group_type}
                dedup_result = self.process_and_deduplicate(msgs, group_info)
                
                # 批量入库消息（使用 UPSERT 防止重复报错）
                chat_messages = dedup_result['chat_messages']
                if chat_messages:
                    try:
                        # 构建插入语句，使用 ON CONFLICT DO NOTHING 进行去重
                        insert_stmt = insert(ChatMessage).values([
                            {
                                'message_id': msg.get('message_id'),  # 存储 seq 值
                                'project_id': self.project_id,
                                'talker_name': group_name,
                                'sender_name': msg['sender_nickname'],
                                'message_type': msg['message_type'],
                                'content': msg['content'],
                                'timestamp': msg['message_time'],
                                'created_at': datetime.utcnow(),
                            }
                            for msg in chat_messages
                        ])
                        
                        # 使用复合唯一约束进行去重
                        do_nothing_stmt = insert_stmt.on_conflict_do_nothing(
                            index_elements=['project_id', 'message_id']
                        )
                        insert_result = db.session.execute(do_nothing_stmt)
                        db.session.commit()
                        
                        # 统计实际插入的记录数
                        try:
                            inserted_count = insert_result.rowcount if hasattr(insert_result, 'rowcount') else len(chat_messages)
                        except:
                            inserted_count = len(chat_messages)  # 如果无法获取 rowcount，使用原始数量
                        total_messages += inserted_count
                        all_new_msgs.extend(chat_messages)
                        self._log(f"群聊 {group_name} 批量入库消息 {inserted_count} 条（已自动跳过重复消息）。")
                        
                    except Exception as e:
                        db.session.rollback()
                        self._log(f"消息批量入库失败: {e}")
                
                # 批量入库文件（使用 UPSERT 进行去重）
                file_records = dedup_result['file_records']
                if file_records:
                    valid_files = []
                    for file in file_records:
                        try:
                            # 字段校验与默认值
                            filename = file.get('filename', '') or ''
                            group_name = file.get('group_name', '') or ''
                            file_type = file.get('file_type', '') or ''
                            uploader_id = str(file.get('uploader_id')) if file.get('uploader_id') else ''
                            upload_time = file.get('upload_time') or datetime.utcnow()
                            # 唯一性校验（project_id+chatroom_name+original_name）
                            exists = FileRecord.query.filter_by(
                                project_id=self.project_id,
                                chatroom_name=group_name,
                                original_name=filename
                            ).first()
                            if exists:
                                self._log(f"跳过重复文件: {filename} (群聊={group_name})")
                                continue
                            # 校验通过，加入待插入列表
                            valid_files.append({
                                'project_id': self.project_id,
                                'project_name': project.project_name,
                                'chatroom_name': group_name,
                                'original_name': filename,
                                'standardized_name': filename,
                                'author_abbreviation': file.get('parsed_author_abbreviation') or '',
                                'version': file.get('parsed_version') or '',
                                'file_extension': file_type,
                                'upload_time': upload_time,
                                'uploader': uploader_id,
                                'status': 'pending',
                                'message_seq': file.get('message_seq') if file.get('message_seq') else None,
                                'created_at': datetime.utcnow(),
                                'updated_at': datetime.utcnow()
                            })
                        except Exception as e:
                            self._log(f"单条文件数据校验异常: {file} - {str(e)}")
                            continue
                    if valid_files:
                        try:
                            file_insert_stmt = insert(FileRecord).values(valid_files)
                            file_do_nothing_stmt = file_insert_stmt.on_conflict_do_nothing(
                                index_elements=['project_id', 'chatroom_name', 'original_name']
                            )
                            file_insert_result = db.session.execute(file_do_nothing_stmt)
                            db.session.commit()
                            try:
                                inserted_file_count = file_insert_result.rowcount if hasattr(file_insert_result, 'rowcount') else len(valid_files)
                            except:
                                inserted_file_count = len(valid_files)
                            total_files += inserted_file_count
                            all_new_files.extend(valid_files)
                            self._log(f"群聊 {group_name} 批量入库文件 {inserted_file_count} 条（已自动跳过异常和重复文件）。")
                        except Exception as e:
                            db.session.rollback()
                            self._log(f"文件批量入库失败: {e}")
                
                self._log(f"群聊 {group_name} 处理完成。")
            
            self._log(f"全部群聊同步完成。共入库消息 {total_messages} 条，文件 {total_files} 条。")
            return {
                'success': True,
                'message': f'同步完成，消息 {total_messages} 条，文件 {total_files} 条',
                'total_messages': total_messages,
                'total_files': total_files,
                'logs': []
            }
            
        except Exception as e:
            self._log(f"同步过程发生异常: {e}\n{traceback.format_exc()}")
            db.session.rollback()
            return {'success': False, 'message': f'同步异常: {e}', 'logs': []}
    
    def _associate_employee(self, sender_name: str, group_type: str = 'unknown') -> Tuple[Optional[int], str]:
        if not sender_name:
            return None, 'unknown'

        best_match_employee = None
        highest_score = 0.6  # 相似度阈值

        for employee in self.employees:
            # 获取员工的各种名称进行匹配
            wechat_nickname = employee.get('wechat_nickname', '')
            real_name = employee.get('real_name', '')
            
            # 完全匹配优先
            if sender_name == wechat_nickname or sender_name == real_name:
                 best_match_employee = employee
                 break

            # 模糊匹配
            score1 = SequenceMatcher(None, sender_name, wechat_nickname).ratio() if wechat_nickname else 0
            score2 = SequenceMatcher(None, sender_name, real_name).ratio() if real_name else 0
            
            max_score = max(score1, score2)
            if max_score > highest_score:
                highest_score = max_score
                best_match_employee = employee
        
        if best_match_employee:
            return best_match_employee.get('id'), 'employee'
        
        # 如果是在外部群且没匹配到员工，则认为是客户
        if group_type == 'external':
            return None, 'client'
            
        # 记录未匹配到的人员
        self._record_unmatched_person(sender_name, group_type)
        return None, 'unmatched'

    def _record_unmatched_person(self, sender_name: str, group_name: str):
        """记录未匹配到的人员到数据库，避免重复记录"""
        exists = UnmatchedPerson.query.filter_by(sender_name=sender_name, group_name=group_name).first()
        if not exists:
            try:
                new_person = UnmatchedPerson(sender_name=sender_name, group_name=group_name, role='unknown')
                db.session.add(new_person)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.error(f"记录未匹配人员 '{sender_name}' 到数据库失败: {e}")

    def _parse_filename_components(self, filename: str) -> Dict[str, str]:
        """
        解析文件名组件，支持多种格式
        格式: [YYMMDD]-[项目名]-[工单名/内容描述]-[工作量]-[作者缩写]-[版本号].扩展名
        """
        components = {
            'date': '',
            'project_name': '',
            'work_order': '',
            'workload': '',
            'author_abbreviation': '',
            'version': '',
            'extension': '',
            'is_standard_format': False
        }
        
        try:
            # 尝试标准格式解析
            match = self.parser.filename_parse_regex.match(filename)
            if match:
                components.update({
                    'date': match.group(1),
                    'project_name': match.group(2),
                    'work_order': match.group(3),
                    'workload': match.group(4),
                    'author_abbreviation': match.group(5),
                    'version': match.group(6),
                    'extension': match.group(7),
                    'is_standard_format': True
                })
            else:
                # 非标准格式，尝试简单解析
                components['project_name'] = self._extract_project_name_simple(filename)
                components['extension'] = self._extract_extension_simple(filename)
                
        except Exception as e:
            logger.error(f"解析文件名组件失败: {str(e)}, 文件名: {filename}")
        
        return components

    def _extract_project_name_simple(self, filename: str) -> str:
        """简单提取项目名称"""
        # 常见的项目名称模式
        patterns = [
            r'(\w+项目)',  # 匹配"项目"结尾
            r'(\w+天地)',  # 匹配"天地"结尾
            r'(\w+府)',    # 匹配"府"结尾
            r'(\w+城)',    # 匹配"城"结尾
            r'(\w+园)',    # 匹配"园"结尾
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                return match.group(1)
        
        return '未知项目'

    def _extract_extension_simple(self, filename: str) -> str:
        """简单提取文件扩展名"""
        ext_match = re.search(r'\.([a-zA-Z0-9]+)$', filename)
        return ext_match.group(1).lower() if ext_match else ''

    def _create_file_record(self, parsed_message: Dict[str, Any], employee_id: Optional[int], role: str, group_info: Dict) -> Optional[Dict]:
        """
        创建文件记录
        """
        content = parsed_message.get('parsed_content', {})
        filename = content.get('filename')

        if not filename:
            return None

        components = self._parse_filename_components(filename)
        # 兼容time为字符串或数字
        raw_time = parsed_message.get('time', 0)
        if isinstance(raw_time, str):
            try:
                raw_time = float(raw_time)
            except Exception:
                raw_time = 0
        timestamp = datetime.fromtimestamp(raw_time)

        return {
            'project_id': self.project_id,
            'filename': filename,
            'uploader_id': employee_id,
            'uploader_role': role,
            'upload_time': timestamp,
            'file_type': components.get('extension'),
            'group_name': group_info.get('name'),
            'group_type': group_info.get('type'),
            'is_standard_format': components.get('is_standard_format'),
            'parsed_project_name': components.get('project_name'),
            'parsed_date': components.get('date'),
            'parsed_author_abbreviation': components.get('author_abbreviation'),
            'parsed_version': components.get('version'),
        }

    def _create_chat_message(self, parsed_message: Dict[str, Any], employee_id: Optional[int], role: str) -> Dict[str, Any]:
        """
        创建聊天消息记录
        """
        from datetime import datetime
        time_val = parsed_message.get('time', 0)
        if isinstance(time_val, (int, float)):
            timestamp = datetime.fromtimestamp(time_val)
        elif isinstance(time_val, str):
            try:
                timestamp = datetime.fromisoformat(time_val.replace('Z', '+00:00'))
            except Exception:
                try:
                    timestamp = datetime.strptime(time_val, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    timestamp = datetime.utcnow()
        else:
            timestamp = datetime.utcnow()

        return {
            'project_id': self.project_id,
            'message_id': parsed_message.get('seq'),
            'message_time': timestamp,
            'sender_id': employee_id,
            'sender_role': role,
            'sender_nickname': parsed_message.get('sender_name'),
            'group_name': parsed_message.get('talker_name'),
            'message_type': parsed_message.get('parsed_content', {}).get('type', '未知'),
            'content': json.dumps(parsed_message.get('parsed_content', {}), ensure_ascii=False)
        }

    def process_and_deduplicate(self, 
                       chatlog: List[Dict[str, Any]], 
                       group_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理聊天记录，包括解析、关联、去重
        基于 seq 字段进行高效去重，减少数据库查询
        """
        new_messages = []
        new_files = []
        
        # 优化：减少数据库查询，直接处理所有消息
        # 数据库级别的唯一约束会自动处理重复
        self._log(f"开始处理 {len(chatlog)} 条消息...")
        
        for message in chatlog:
            seq = message.get('seq')
            if not seq:
                self._log(f"跳过无 seq 字段的消息: {message.get('senderName', 'unknown')}")
                continue

            parsed_message = self.parser.parse_message(message)
            sender_name = parsed_message.get('sender_name')
            
            employee_id, role = self._associate_employee(sender_name, group_info['type'])

            # 创建聊天消息记录
            chat_record = self._create_chat_message(parsed_message, employee_id, role)
            new_messages.append(chat_record)
            
            # 如果是文件，创建文件记录
            if parsed_message.get('parsed_content', {}).get('filename'):
                file_record = self._create_file_record(parsed_message, employee_id, role, group_info)
                if file_record:
                    new_files.append(file_record)

        self._log(f"处理完成：消息 {len(new_messages)} 条，文件 {len(new_files)} 条")
        return {
            "chat_messages": new_messages,
            "file_records": new_files
        } 