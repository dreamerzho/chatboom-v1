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
from typing import Dict, List, Optional, Any, Tuple
from difflib import SequenceMatcher
from models.unmatched_person import UnmatchedPerson
from db import db

logger = logging.getLogger(__name__)

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
    
    def __init__(self):
        """初始化处理器"""
        self.parser = ChatMessageParser()
        self.processed_seqs = set()  # 已处理的消息序列号
        
    def _associate_employee(self, sender_name: str, employees: List[Dict[str, Any]], group_type: str = 'unknown') -> Tuple[Optional[Dict], str]:
        """
        将发件人姓名与员工列表进行模糊匹配
        支持内部/外部群的角色区分
        """
        if not sender_name or not employees:
            return None, 'unknown'

        best_match = None
        highest_score = 0.6  # 相似度阈值

        for employee in employees:
            # 获取员工的各种名称进行匹配
            wechat_nickname = employee.get('wechat_nickname', '')
            real_name = employee.get('real_name', '')
            name_abbreviation = employee.get('name_abbreviation', '')
            
            # 计算相似度
            scores = []
            
            if wechat_nickname:
                scores.append(SequenceMatcher(None, sender_name, wechat_nickname).ratio())
            
            if real_name:
                scores.append(SequenceMatcher(None, sender_name, real_name).ratio())
            
            if name_abbreviation:
                scores.append(SequenceMatcher(None, sender_name, name_abbreviation).ratio())
            
            # 取最高分
            if scores:
                max_score = max(scores)
                if max_score > highest_score:
                    highest_score = max_score
                    best_match = employee
        
        if best_match:
            return best_match, 'employee'
        
        # 如果是在外部群且没匹配到员工，则认为是客户
        if group_type == 'external':
            return {'name': sender_name, 'role': '外部客户'}, 'client'
            
        return None, 'unmatched'

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

    def _create_file_record(self, parsed_message: Dict[str, Any], employee: Optional[Dict], role: str, group_info: Dict) -> Optional[Dict]:
        """
        创建文件记录
        """
        content = parsed_message.get('parsed_content', {})
        filename = content.get('filename')

        if not filename:
            return None

        # 解析文件名组件
        filename_components = self._parse_filename_components(filename)
        
        # 确定项目名称（优先使用解析出的，否则使用群聊信息）
        project_name = filename_components['project_name']
        if not project_name or project_name == '未知项目':
            project_name = group_info.get('project_name', '未知项目')

        return {
            'original_name': filename,
            'standardized_name': filename,  # 可以后续标准化
            'project_name': project_name,
            'work_order': filename_components['work_order'],
            'workload': filename_components['workload'],
            'author_abbreviation': filename_components['author_abbreviation'],
            'version': filename_components['version'],
            'file_extension': filename_components['extension'],
            'upload_time': parsed_message.get('time'),
            'uploader': parsed_message.get('sender_name'),
            'file_size': '0',  # 暂时设为0，后续可以从content中提取
            'status': 'pending',
            'employee_id': employee.get('id') if employee and role == 'employee' else None,
            'chatroom_name': group_info.get('chatroom_name'),
            'message_seq': parsed_message.get('seq'),
            'is_standard_format': filename_components['is_standard_format'],
            'sender_role': role,
            'group_type': group_info.get('group_type', 'unknown')
        }

    def _create_chat_message(self, parsed_message: Dict[str, Any], employee: Optional[Dict], role: str) -> Dict[str, Any]:
        """
        创建聊天消息记录
        """
        return {
            'seq': parsed_message.get('seq'),  # 使用seq字段，与数据库模型保持一致
            'time': parsed_message.get('time'),
            'talker': parsed_message.get('talker'),
            'talker_name': parsed_message.get('talker_name'),
            'sender': parsed_message.get('sender'),
            'sender_name': parsed_message.get('sender_name'),
            'is_self': parsed_message.get('is_self', False),
            'type': parsed_message.get('type'),
            'sub_type': parsed_message.get('sub_type', 0),
            'content': parsed_message.get('parsed_content', {}).get('text', ''),
            'employee_id': employee.get('id') if employee and role == 'employee' else None,
            'sender_role': role
        }

    def process_and_deduplicate(self, 
                       chatlog: List[Dict[str, Any]], 
                       employees: List[Dict[str, Any]],
                       group_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理聊天记录并去重 - 群聊类型与角色区分增强版
        
        参数:
            chatlog: 原始聊天记录列表
            employees: 员工列表（用于匹配）
            group_info: 群聊信息 {'chatroom_name': '群名', 'project_name': '项目名', 'group_type': 'internal/external'}
        
        返回:
            处理结果
        """
        try:
            # 设置默认群聊信息（已强制要求传入，不再自动补全）
            if not group_info or 'group_type' not in group_info:
                raise ValueError('group_info参数必须包含group_type')
            
            result = {
                'total_messages': len(chatlog),
                'processed_messages': 0,
                'duplicate_messages': 0,
                'file_messages': 0,
                'text_messages': 0,
                'other_messages': 0,
                'matched_employees': 0,
                'unmatched_employees': 0,
                'client_messages': 0,
                'parsed_messages': [],
                'file_records': [],
                'chat_messages': [],
                'employee_stats': {},
                'errors': []
            }
            
            for message in chatlog:
                try:
                    # 检查是否已处理过（去重）
                    seq = message.get('seq')
                    if seq in self.processed_seqs:
                        result['duplicate_messages'] += 1
                        continue
                    
                    self.processed_seqs.add(seq)
                    result['processed_messages'] += 1
                    
                    # 解析消息
                    parsed_message = self.parser.parse_message(message)
                    
                    # 匹配员工
                    matched_employee, role = self._associate_employee(
                        parsed_message['sender_name'], 
                        employees,
                        group_info.get('group_type', 'unknown')
                    )
                    
                    if role == 'employee':
                        result['matched_employees'] += 1
                        # 统计员工消息数量
                        emp_id = matched_employee['id']
                        if emp_id not in result['employee_stats']:
                            result['employee_stats'][emp_id] = {
                                'employee': matched_employee,
                                'message_count': 0,
                                'file_count': 0
                            }
                        result['employee_stats'][emp_id]['message_count'] += 1
                    elif role == 'client':
                        result['client_messages'] += 1
                    else:
                        result['unmatched_employees'] += 1
                        # 记录未匹配人员到数据库
                        try:
                            unmatched = UnmatchedPerson.query.filter_by(
                                sender_name=parsed_message['sender_name'],
                                group_name=group_info.get('chatroom_name', '未知群聊')
                            ).first()
                            if not unmatched:
                                unmatched = UnmatchedPerson(
                                    sender_name=parsed_message['sender_name'],
                                    group_name=group_info.get('chatroom_name', '未知群聊'),
                                    role='未知',
                                    remark='自动记录，未匹配为员工'
                                )
                                db.session.add(unmatched)
                                db.session.commit()
                        except Exception as e:
                            logger.error(f"记录未匹配人员失败: {str(e)}")
                    
                    # 统计消息类型
                    msg_type = parsed_message.get('type')
                    if msg_type == 49 and parsed_message.get('parsed_content', {}).get('filename'):
                        result['file_messages'] += 1
                        if matched_employee and role == 'employee':
                            emp_id = matched_employee['id']
                            result['employee_stats'][emp_id]['file_count'] += 1
                        
                        # 创建文件记录
                        file_record = self._create_file_record(parsed_message, matched_employee, role, group_info)
                        if file_record:
                            result['file_records'].append(file_record)
                    
                    elif msg_type == 1:
                        result['text_messages'] += 1
                    else:
                        result['other_messages'] += 1
                    
                    # 创建聊天消息记录
                    chat_message = self._create_chat_message(parsed_message, matched_employee, role)
                    result['chat_messages'].append(chat_message)
                    
                    result['parsed_messages'].append(parsed_message)
                    
                except Exception as e:
                    error_msg = f"处理消息失败: {str(e)}, seq: {message.get('seq')}"
                    logger.error(error_msg)
                    result['errors'].append(error_msg)
            
            logger.info(f"聊天记录处理完成："
                       f"总消息 {result['total_messages']} 条，"
                       f"处理 {result['processed_messages']} 条，"
                       f"文件 {result['file_messages']} 个，"
                       f"去重 {result['duplicate_messages']} 条，"
                       f"员工匹配 {result['matched_employees']} 个，"
                       f"客户消息 {result['client_messages']} 条")
            
            return result
            
        except Exception as e:
            logger.error(f"处理聊天记录失败: {str(e)}")
            return {
                'error': str(e),
                'total_messages': len(chatlog),
                'processed_messages': 0,
                'file_records': [],
                'chat_messages': []
            }
    
    def clear_processed_seqs(self):
        """清空已处理的消息序列号（用于重新同步）"""
        self.processed_seqs.clear()
        logger.info("已清空处理记录，可以重新同步") 