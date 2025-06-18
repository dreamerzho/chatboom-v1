#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天记录处理器
负责解析聊天记录中的文件信息、去重、人员关联等功能
整合了旧chat_parser.py中的核心功能
"""

import xml.etree.ElementTree as ET
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class ChatMessageParser:
    """
    聊天记录解析器
    负责解析聊天记录中的各种信息，包括文件、文本、图片等
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
        
        self.file_subtypes = {
            1: "链接",
            3: "图片",
            5: "视频",
            6: "文件",
            8: "音乐"
        }
    
    def parse_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析单条聊天记录
        
        参数:
            message: 原始消息数据
            
        返回:
            解析后的消息信息
        """
        try:
            parsed = {
                'seq': message.get('seq'),
                'time': message.get('time'),
                'talker': message.get('talker'),
                'talkerName': message.get('talkerName'),
                'sender': message.get('sender'),
                'senderName': message.get('senderName'),
                'isSelf': message.get('isSelf', False),
                'type': message.get('type'),
                'subType': message.get('subType'),
                'content': message.get('content', ''),
                'contents': message.get('contents', {}),
                'parsed_content': None,
                'file_info': None,
                'message_type_name': self.message_types.get(message.get('type'), '未知类型')
            }
            
            # 根据消息类型进行特殊解析
            if parsed['type'] == 49:  # 多媒体消息
                parsed['file_info'] = self._parse_file_message(message)
            elif parsed['type'] == 1:  # 文本消息
                parsed['parsed_content'] = self._parse_text_message(message)
            
            return parsed
            
        except Exception as e:
            logger.error(f"解析消息失败: {str(e)}, 消息: {message}")
            return message
    
    def _parse_file_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        解析文件消息
        
        参数:
            message: 文件消息数据
            
        返回:
            解析后的文件信息
        """
        try:
            content = message.get('content', '')
            if not content:
                return None
            
            # 解析XML内容
            root = ET.fromstring(content)
            
            # 获取appmsg节点
            appmsg = root.find('appmsg')
            if appmsg is None:
                return None
            
            # 获取文件信息
            title = appmsg.find('title')
            title_text = title.text if title is not None else ''
            
            # 获取appattach节点（文件附件信息）
            appattach = appmsg.find('appattach')
            if appattach is None:
                return None
            
            file_info = {
                'title': title_text,
                'fileext': appattach.find('fileext').text if appattach.find('fileext') is not None else '',
                'totallen': appattach.find('totallen').text if appattach.find('totallen') is not None else '0',
                'attachid': appattach.find('attachid').text if appattach.find('attachid') is not None else '',
                'md5': appmsg.find('md5').text if appmsg.find('md5') is not None else '',
                'subtype': message.get('subType'),
                'subtype_name': self.file_subtypes.get(message.get('subType'), '未知子类型')
            }
            
            # 从contents中获取额外信息
            contents = message.get('contents', {})
            if contents:
                file_info.update(contents)
            
            return file_info
            
        except Exception as e:
            logger.error(f"解析文件消息失败: {str(e)}")
            return None
    
    def _parse_text_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析文本消息
        
        参数:
            message: 文本消息数据
            
        返回:
            解析后的文本信息
        """
        content = message.get('content', '')
        
        return {
            'text': content,
            'word_count': len(content),
            'has_keywords': self._check_keywords(content)
        }
    
    def _check_keywords(self, text: str) -> Dict[str, int]:
        """
        检查文本中的关键词
        
        参数:
            text: 文本内容
            
        返回:
            关键词统计
        """
        # 定义关键词列表
        positive_keywords = ['好的', '收到', '没问题', '可以', '行', 'OK', 'ok', '嗯', '是的']
        negative_keywords = ['不行', '做不了', '有问题', '不能', '不可以', '不行', 'NO', 'no']
        
        result = {
            'positive': 0,
            'negative': 0
        }
        
        for keyword in positive_keywords:
            result['positive'] += text.count(keyword)
        
        for keyword in negative_keywords:
            result['negative'] += text.count(keyword)
        
        return result

class EmployeeMatcher:
    """
    员工匹配器
    负责将微信昵称与真实员工信息进行匹配
    """
    
    def __init__(self):
        """初始化匹配器"""
        self.similarity_threshold = 0.6  # 相似度阈值
    
    def match_employee(self, sender_name: str, employees: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        匹配员工信息
        
        参数:
            sender_name: 发送者昵称
            employees: 员工列表
            
        返回:
            匹配到的员工信息
        """
        if not employees or not sender_name:
            return None
        
        best_match = None
        best_score = 0
        
        for employee in employees:
            # 多维度匹配
            scores = []
            
            # 1. 微信昵称匹配
            if employee.get('wechat_nickname'):
                score = self._calculate_similarity(sender_name, employee['wechat_nickname'])
                scores.append(score)
            
            # 2. 真实姓名匹配
            if employee.get('real_name'):
                score = self._calculate_similarity(sender_name, employee['real_name'])
                scores.append(score)
            
            # 3. 姓名缩写匹配
            if employee.get('name_abbreviation'):
                score = self._calculate_similarity(sender_name, employee['name_abbreviation'])
                scores.append(score)
            
            # 取最高分
            if scores:
                max_score = max(scores)
                if max_score > best_score and max_score >= self.similarity_threshold:
                    best_score = max_score
                    best_match = employee
                    best_match['match_score'] = max_score
        
        return best_match
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        计算两个字符串的相似度
        
        参数:
            str1: 字符串1
            str2: 字符串2
            
        返回:
            相似度分数 (0-1)
        """
        if not str1 or not str2:
            return 0.0
        
        # 使用SequenceMatcher计算相似度
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

class ChatlogProcessor:
    """
    聊天记录处理器
    整合了解析、匹配、去重等功能
    """
    
    def __init__(self):
        """初始化处理器"""
        self.parser = ChatMessageParser()
        self.matcher = EmployeeMatcher()
        self.processed_seqs = set()  # 已处理的消息序列号
    
    def process_chatlog(self, 
                       chatlog: List[Dict[str, Any]], 
                       employees: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理聊天记录
        
        参数:
            chatlog: 聊天记录列表
            employees: 员工列表（用于人员匹配）
            
        返回:
            处理结果
        """
        result = {
            "total_messages": len(chatlog),
            "processed_messages": 0,
            "duplicate_messages": 0,
            "file_messages": 0,
            "text_messages": 0,
            "matched_employees": 0,
            "unmatched_employees": 0,
            "file_records": [],
            "chat_messages": [],
            "employee_stats": {}
        }
        
        for message in chatlog:
            try:
                # 检查是否已处理过
                seq = message.get('seq')
                if seq in self.processed_seqs:
                    result["duplicate_messages"] += 1
                    continue
                
                # 解析消息
                parsed_message = self.parser.parse_message(message)
                
                # 人员匹配
                matched_employee = None
                if employees and parsed_message.get('senderName'):
                    matched_employee = self.matcher.match_employee(
                        parsed_message['senderName'], 
                        employees
                    )
                
                if matched_employee:
                    result["matched_employees"] += 1
                    # 更新员工统计
                    emp_id = matched_employee.get('id')
                    if emp_id not in result["employee_stats"]:
                        result["employee_stats"][emp_id] = {
                            "employee": matched_employee,
                            "message_count": 0,
                            "file_count": 0
                        }
                    result["employee_stats"][emp_id]["message_count"] += 1
                else:
                    result["unmatched_employees"] += 1
                
                # 创建聊天消息记录
                chat_message = self._create_chat_message(parsed_message, matched_employee)
                if chat_message:
                    result["chat_messages"].append(chat_message)
                    result["text_messages"] += 1
                
                # 处理文件消息
                if parsed_message.get('file_info'):
                    file_record = self._create_file_record(parsed_message, matched_employee)
                    if file_record:
                        result["file_records"].append(file_record)
                        result["file_messages"] += 1
                        # 更新员工文件统计
                        if matched_employee:
                            emp_id = matched_employee.get('id')
                            if emp_id in result["employee_stats"]:
                                result["employee_stats"][emp_id]["file_count"] += 1
                
                # 标记为已处理
                if seq:
                    self.processed_seqs.add(seq)
                result["processed_messages"] += 1
                
            except Exception as e:
                logger.error(f"处理消息失败: {str(e)}, 消息: {message}")
                continue
        
        return result
    
    def _create_file_record(self, parsed_message: Dict[str, Any], employee: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        创建文件记录
        
        参数:
            parsed_message: 解析后的消息
            employee: 匹配的员工信息
            
        返回:
            文件记录
        """
        file_info = parsed_message.get('file_info')
        if not file_info:
            return None
        
        # 解析文件名规范
        filename = file_info.get('title', '')
        project_name = self._extract_project_name(filename)
        work_order = self._extract_work_order(filename)
        workload = self._extract_workload(filename)
        author = self._extract_author(filename)
        version = self._extract_version(filename)
        
        return {
            'filename': filename,
            'file_ext': file_info.get('fileext', ''),
            'file_size': int(file_info.get('totallen', 0)),
            'file_md5': file_info.get('md5', ''),
            'project_name': project_name,
            'work_order': work_order,
            'workload': workload,
            'author': author,
            'version': version,
            'upload_time': parsed_message.get('time'),
            'uploader_name': parsed_message.get('senderName'),
            'employee_id': employee.get('id') if employee else None,
            'chatroom_name': parsed_message.get('talkerName'),
            'message_seq': parsed_message.get('seq')
        }
    
    def _create_chat_message(self, parsed_message: Dict[str, Any], employee: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        创建聊天消息记录
        
        参数:
            parsed_message: 解析后的消息
            employee: 匹配的员工信息
            
        返回:
            聊天消息记录
        """
        return {
            'message_seq': parsed_message.get('seq'),
            'message_time': parsed_message.get('time'),
            'sender_name': parsed_message.get('senderName'),
            'sender_id': parsed_message.get('sender'),
            'message_type': parsed_message.get('type'),
            'message_content': parsed_message.get('content', ''),
            'chatroom_name': parsed_message.get('talkerName'),
            'chatroom_id': parsed_message.get('talker'),
            'employee_id': employee.get('id') if employee else None,
            'is_self': parsed_message.get('isSelf', False),
            'keywords': parsed_message.get('parsed_content', {}).get('has_keywords', {})
        }
    
    def _extract_project_name(self, filename: str) -> str:
        """从文件名中提取项目名称"""
        # 文件名格式: [YYMMDD]-[项目名]-[工单名/内容描述]-[工作量]-[作者缩写]-[版本号].扩展名
        parts = filename.split('-')
        if len(parts) >= 2:
            return parts[1]
        return ''
    
    def _extract_work_order(self, filename: str) -> str:
        """从文件名中提取工单名"""
        parts = filename.split('-')
        if len(parts) >= 3:
            return parts[2]
        return ''
    
    def _extract_workload(self, filename: str) -> str:
        """从文件名中提取工作量"""
        parts = filename.split('-')
        if len(parts) >= 4:
            return parts[3]
        return ''
    
    def _extract_author(self, filename: str) -> str:
        """从文件名中提取作者缩写"""
        parts = filename.split('-')
        if len(parts) >= 5:
            return parts[4]
        return ''
    
    def _extract_version(self, filename: str) -> str:
        """从文件名中提取版本号"""
        parts = filename.split('-')
        if len(parts) >= 6:
            return parts[5].split('.')[0]  # 去掉扩展名
        return ''
    
    def clear_processed_seqs(self):
        """清空已处理的消息序列号"""
        self.processed_seqs.clear() 