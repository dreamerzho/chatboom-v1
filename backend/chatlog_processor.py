#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天记录处理器
负责解析聊天记录中的文件信息、去重、人员关联等功能
整合了旧chat_parser.py中的核心功能
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Callable
from difflib import SequenceMatcher
import json
import os
from models.project import Project
from models.unmatched_person import UnmatchedPerson
from models.file import FileRecord
from models.chat import ChatMessage
from models.employee import EmployeeMapping
from db import db

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

    def get_chatlog_filenames(self) -> Dict[str, List[str]]:
        """根据项目ID获取对应的聊天记录文件名"""
        project = Project.query.get(self.project_id)
        if not project:
            self._log(f"错误：找不到ID为 {self.project_id} 的项目。")
            return {}

        self._log(f"开始为项目 '{project.project_name}' 查找聊天记录文件...")
        
        # 严格按 chatrooms 结构分类
        chatrooms = getattr(project, 'chatrooms', [])
        internal_chat_groups = [c.chatroom_name for c in chatrooms if getattr(c, 'chatroom_type', '') == '内部群聊']
        external_chat_groups = [c.chatroom_name for c in chatrooms if getattr(c, 'chatroom_type', '') == '外部群聊']
        chat_groups = {
            'internal': internal_chat_groups,
            'external': external_chat_groups
        }
        
        filenames = {'internal': [], 'external': []}
        
        # 确保基础路径存在
        if not os.path.isdir(CHATLOG_BASE_PATH):
            self._log(f"错误：聊天记录基础路径 {CHATLOG_BASE_PATH} 不存在或不是一个目录。")
            return {}

        all_files = [f for f in os.listdir(CHATLOG_BASE_PATH) if f.endswith('.txt')]
        self._log(f"在 {CHATLOG_BASE_PATH} 中找到 {len(all_files)} 个 .txt 文件。")

        for group_type, groups in chat_groups.items():
            for group_name in groups:
                found = False
                for filename in all_files:
                    if group_name in filename:
                        filenames[group_type].append(filename)
                        self._log(f"  - 匹配成功 ({group_type}): 群聊 '{group_name}' -> 文件 '{filename}'")
                        found = True
                if not found:
                     self._log(f"  - 匹配失败 ({group_type}): 未找到与群聊 '{group_name}' 相关的文件。")

        return filenames

    def load_and_parse_chatlog_file(self, filename: str) -> List[Dict[str, Any]]:
        """加载并解析单个聊天记录文件"""
        full_path = os.path.join(CHATLOG_BASE_PATH, filename)
        self._log(f"正在读取文件: {full_path}")
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                # 假设文件内容是JSON数组
                data = json.load(f)
                if isinstance(data, list):
                    self._log(f"文件 '{filename}' 读取成功，包含 {len(data)} 条记录。")
                    return data
                else:
                    self._log(f"文件 '{filename}' 格式错误：内容不是一个JSON列表。")
                    return []
        except FileNotFoundError:
            self._log(f"错误：文件不存在 {full_path}")
            return []
        except json.JSONDecodeError as e:
            self._log(f"错误：解析文件 {filename} JSON失败: {e}")
            return []
        except Exception as e:
            self._log(f"错误：读取文件 {filename} 时发生未知错误: {e}")
            return []

    def process_chatlogs(self) -> Dict[str, Any]:
        """
        主处理流程
        1. 获取文件名 -> 2. 读取文件 -> 3. 解析和处理 -> 4. 保存到数据库
        """
        self._log(f"--- 开始处理项目ID: {self.project_id} 的聊天记录 ---")
        filenames_by_type = self.get_chatlog_filenames()

        if not any(filenames_by_type.values()):
            self._log("未找到任何相关的聊天记录文件，处理中止。")
            return {"success": False, "message": "未找到相关的聊天记录文件"}
        
        all_messages = []
        all_files = []

        for group_type, filenames in filenames_by_type.items():
            for filename in filenames:
                chatlog_data = self.load_and_parse_chatlog_file(filename)
                if not chatlog_data:
                    continue

                group_info = {'type': group_type, 'name': os.path.splitext(filename)[0]}
                
                processed_data = self.process_and_deduplicate(chatlog_data, group_info)
                
                messages_to_add = processed_data.get('chat_messages', [])
                files_to_add = processed_data.get('file_records', [])

                self._log(f"文件 '{filename}' 处理完成: 新增消息 {len(messages_to_add)}, 新增文件 {len(files_to_add)}")

                all_messages.extend(messages_to_add)
                all_files.extend(files_to_add)

        # 批量保存到数据库
        try:
            if all_messages:
                db.session.bulk_insert_mappings(ChatMessage, all_messages)
                self._log(f"准备向数据库批量插入 {len(all_messages)} 条消息记录...")
            
            if all_files:
                db.session.bulk_insert_mappings(FileRecord, all_files)
                self._log(f"准备向数据库批量插入 {len(all_files)} 条文件记录...")

            if all_messages or all_files:
                db.session.commit()
                self._log("数据已成功提交到数据库。")
            else:
                self._log("没有新的数据需要提交到数据库。")
                
        except Exception as e:
            db.session.rollback()
            self._log(f"数据库操作失败: {e}")
            return {"success": False, "message": f"数据库操作失败: {e}"}

        summary = {
            "total_new_messages": len(all_messages),
            "total_new_files": len(all_files)
        }
        self._log(f"--- 项目ID: {self.project_id} 处理完成。总结: {summary} ---")
        return {"success": True, "summary": summary}
    
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
        
        timestamp = datetime.fromtimestamp(parsed_message.get('time', 0))

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
        timestamp = datetime.fromtimestamp(parsed_message.get('time', 0))

        return {
            'project_id': self.project_id,
            'message_seq': parsed_message.get('seq'),
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
        """
        new_messages = []
        new_files = []
        
        # 首先检查数据库中已存在的seq
        seqs_in_log = [msg.get('seq') for msg in chatlog if msg.get('seq')]
        if seqs_in_log:
            existing_seqs = db.session.query(ChatMessage.message_seq).filter(
                ChatMessage.project_id == self.project_id,
                ChatMessage.message_seq.in_(seqs_in_log)
            ).all()
            processed_seqs = {seq[0] for seq in existing_seqs}
            self._log(f"在数据库中找到 {len(processed_seqs)} 条已存在的记录，将跳过处理。")
        else:
            processed_seqs = set()

        for message in chatlog:
            seq = message.get('seq')
            if not seq or seq in processed_seqs:
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
            
            processed_seqs.add(seq)

        return {
            "chat_messages": new_messages,
            "file_records": new_files
        } 