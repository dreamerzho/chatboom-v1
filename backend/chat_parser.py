# 聊天记录解析模块
# 这个模块负责解析微信群聊的JSON格式聊天记录，提取关键信息并存储到数据库

import json
import sqlite3
import re
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ChatParser:
    """
    聊天记录解析器
    负责解析JSON格式的聊天记录，提取消息、文件、发送者等信息
    """
    
    def __init__(self, db_path: str):
        """
        初始化解析器
        参数:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
    
    def get_db_connection(self):
        """
        获取数据库连接
        返回: sqlite3.Connection 对象
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def parse_chat_file(self, file_path: str, group_name: str) -> Dict[str, Any]:
        """
        解析单个聊天记录文件
        参数:
            file_path: 聊天记录文件路径
            group_name: 群聊名称
        返回: 解析结果统计信息
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                chat_data = json.load(f)
            
            logger.info(f"开始解析群聊: {group_name}, 文件: {file_path}")
            
            # 统计信息
            stats = {
                'total_messages': 0,
                'text_messages': 0,
                'file_messages': 0,
                'image_messages': 0,
                'video_messages': 0,
                'other_messages': 0,
                'parsed_files': 0,
                'errors': 0
            }
            
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            for message in chat_data:
                try:
                    # 解析单条消息
                    message_info = self._parse_single_message(message, group_name)
                    
                    if message_info:
                        # 存储到数据库
                        self._save_message_to_db(cursor, message_info)
                        stats['total_messages'] += 1
                        
                        # 统计消息类型
                        if message_info['message_type'] == 'text':
                            stats['text_messages'] += 1
                        elif message_info['message_type'] == 'file':
                            stats['file_messages'] += 1
                            if message_info.get('file_name'):
                                stats['parsed_files'] += 1
                        elif message_info['message_type'] == 'image':
                            stats['image_messages'] += 1
                        elif message_info['message_type'] == 'video':
                            stats['video_messages'] += 1
                        else:
                            stats['other_messages'] += 1
                
                except Exception as e:
                    logger.error(f"解析消息失败: {str(e)}, 消息: {message}")
                    stats['errors'] += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"群聊 {group_name} 解析完成: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"解析聊天文件失败: {file_path}, 错误: {str(e)}")
            return {'error': str(e)}
    
    def _parse_single_message(self, message: Dict[str, Any], group_name: str) -> Optional[Dict[str, Any]]:
        """
        解析单条消息
        参数:
            message: 单条消息的JSON数据
            group_name: 群聊名称
        返回: 解析后的消息信息字典
        """
        try:
            # 提取基本信息
            message_id = message.get('id', '')
            sender_name = message.get('talkerName', '')
            message_type = message.get('type', '')
            content = message.get('content', '')
            timestamp_str = message.get('time', '')
            
            # 转换时间戳
            try:
                timestamp = datetime.fromtimestamp(int(timestamp_str) / 1000)
            except:
                timestamp = datetime.now()
            
            # 解析消息类型
            parsed_type = self._parse_message_type(message_type, content)
            
            # 解析文件信息（如果是文件类型）
            file_name = None
            file_size = None
            
            if parsed_type == 'file' and content:
                file_info = self._parse_file_content(content)
                file_name = file_info.get('file_name')
                file_size = file_info.get('file_size')
            
            return {
                'message_id': message_id,
                'group_name': group_name,
                'sender_name': sender_name,
                'message_type': parsed_type,
                'content': content,
                'file_name': file_name,
                'file_size': file_size,
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"解析单条消息失败: {str(e)}")
            return None
    
    def _parse_message_type(self, type_code: str, content: str) -> str:
        """
        解析消息类型
        参数:
            type_code: 消息类型代码
            content: 消息内容
        返回: 消息类型字符串
        """
        type_mapping = {
            '1': 'text',      # 文本消息
            '3': 'image',     # 图片消息
            '34': 'voice',    # 语音消息
            '43': 'video',    # 视频消息
            '47': 'animation', # 动画表情
            '49': 'file',     # 文件消息
            '10000': 'system' # 系统消息
        }
        
        return type_mapping.get(type_code, 'unknown')
    
    def _parse_file_content(self, content: str) -> Dict[str, str]:
        """
        解析文件消息的内容
        参数:
            content: 文件消息的JSON内容
        返回: 包含文件名和文件大小的字典
        """
        try:
            # 文件消息的content通常是JSON格式
            file_data = json.loads(content)
            
            # 提取文件名
            file_name = file_data.get('title', '')
            
            # 提取文件大小
            file_size = file_data.get('size', '')
            if file_size:
                file_size = self._format_file_size(int(file_size))
            
            return {
                'file_name': file_name,
                'file_size': file_size
            }
            
        except json.JSONDecodeError:
            # 如果不是JSON格式，尝试其他解析方式
            return self._parse_file_name_from_text(content)
        except Exception as e:
            logger.error(f"解析文件内容失败: {str(e)}")
            return {'file_name': '', 'file_size': ''}
    
    def _parse_file_name_from_text(self, content: str) -> Dict[str, str]:
        """
        从文本内容中解析文件名
        参数:
            content: 文件消息的文本内容
        返回: 包含文件名的字典
        """
        # 尝试匹配常见的文件名模式
        patterns = [
            r'文件名[：:]\s*(.+)',
            r'文件[：:]\s*(.+)',
            r'(.+\.(pdf|doc|docx|ppt|pptx|xls|xlsx|jpg|jpeg|png|gif|mp4|avi|mov|psd|ai|sketch))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return {'file_name': match.group(1).strip(), 'file_size': ''}
        
        return {'file_name': content.strip(), 'file_size': ''}
    
    def _format_file_size(self, size_bytes: int) -> str:
        """
        格式化文件大小
        参数:
            size_bytes: 文件大小（字节）
        返回: 格式化后的文件大小字符串
        """
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f}MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f}GB"
    
    def _save_message_to_db(self, cursor: sqlite3.Cursor, message_info: Dict[str, Any]):
        """
        将解析后的消息保存到数据库
        参数:
            cursor: 数据库游标
            message_info: 消息信息字典
        """
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO chat_messages 
                (message_id, group_name, sender_name, message_type, content, 
                 file_name, file_size, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message_info['message_id'],
                message_info['group_name'],
                message_info['sender_name'],
                message_info['message_type'],
                message_info['content'],
                message_info['file_name'],
                message_info['file_size'],
                message_info['timestamp'].isoformat()
            ))
            
        except Exception as e:
            logger.error(f"保存消息到数据库失败: {str(e)}")
            raise
    
    def parse_all_chat_files(self, chat_files_dir: str) -> Dict[str, Any]:
        """
        解析指定目录下的所有聊天记录文件
        参数:
            chat_files_dir: 聊天记录文件目录
        返回: 总体解析结果
        """
        total_stats = {
            'total_files': 0,
            'successful_files': 0,
            'failed_files': 0,
            'total_messages': 0,
            'total_files_parsed': 0,
            'errors': 0
        }
        
        try:
            # 遍历目录下的所有txt文件
            for filename in os.listdir(chat_files_dir):
                if filename.endswith('.txt'):
                    file_path = os.path.join(chat_files_dir, filename)
                    group_name = filename.replace('.txt', '')
                    
                    total_stats['total_files'] += 1
                    
                    # 解析单个文件
                    file_stats = self.parse_chat_file(file_path, group_name)
                    
                    if 'error' not in file_stats:
                        total_stats['successful_files'] += 1
                        total_stats['total_messages'] += file_stats.get('total_messages', 0)
                        total_stats['total_files_parsed'] += file_stats.get('parsed_files', 0)
                        total_stats['errors'] += file_stats.get('errors', 0)
                    else:
                        total_stats['failed_files'] += 1
                        total_stats['errors'] += 1
            
            logger.info(f"所有聊天文件解析完成: {total_stats}")
            return total_stats
            
        except Exception as e:
            logger.error(f"解析聊天文件目录失败: {str(e)}")
            return {'error': str(e)}

# 使用示例
if __name__ == '__main__':
    # 初始化解析器
    parser = ChatParser('database/chat_monitor.db')
    
    # 解析所有聊天文件
    chat_files_dir = '../basefiles'  # 聊天记录文件目录
    result = parser.parse_all_chat_files(chat_files_dir)
    
    print("解析结果:", result) 