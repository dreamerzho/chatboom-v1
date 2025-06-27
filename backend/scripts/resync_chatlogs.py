# 重新同步聊天记录脚本
# 这个脚本用于重新同步聊天记录，确保使用正确的微信昵称而不是微信ID

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from chatlog_integration import chatlog_client
import json
from datetime import datetime
import hashlib
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)

# 定义数据库模型
class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(128), unique=True, nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(32), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    internal_group_name = db.Column(db.String(128))
    external_group_name = db.Column(db.String(128))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.String(128), unique=True)
    group_name = db.Column(db.String(128), nullable=False)
    sender_name = db.Column(db.String(128), nullable=False)
    message_type = db.Column(db.String(32), nullable=False)
    content = db.Column(db.Text)
    file_name = db.Column(db.String(256))
    file_size = db.Column(db.String(32))
    timestamp = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def resync_chatlogs():
    """
    重新同步所有项目的聊天记录，使用正确的senderName字段
    """
    with app.app_context():
        # 清空现有的聊天记录
        logger.info("清空现有聊天记录...")
        ChatMessage.query.delete()
        db.session.commit()
        logger.info("现有聊天记录已清空")
        
        # 获取所有项目
        projects = Project.query.all()
        logger.info(f"找到 {len(projects)} 个项目")
        
        for project in projects:
            logger.info(f"开始重新同步项目: {project.project_name}")
            
            # 设置时间范围（最近一个月）
            start = "2025-06-01"
            end = "2025-06-12"
            
            # 获取群聊配置
            group_configs = []
            
            if project.internal_group_name:
                group_configs.append(project.internal_group_name)
                logger.info(f"内部群: {project.internal_group_name}")
            
            if project.external_group_name:
                group_configs.append(project.external_group_name)
                logger.info(f"外部群: {project.external_group_name}")
            
            total_count = 0
            
            for group_name in group_configs:
                logger.info(f"同步群聊: {group_name}")
                offset = 0
                page_size = 1000
                
                while True:
                    try:
                        messages = chatlog_client.get_chatlog(
                            talker=group_name,
                            time_range=f"{start}~{end}",
                            limit=page_size,
                            offset=offset,
                            format_type='json'
                        )
                        
                        if not messages:
                            logger.info(f"群聊 {group_name} 没有更多消息")
                            break
                        
                        logger.info(f"获取到 {len(messages)} 条消息")
                        
                        page_count = 0
                        
                        for msg in messages:
                            try:
                                # 使用senderName作为发送者名称
                                sender_name = msg.get('senderName') or msg.get('sender') or '未知'
                                
                                # 生成消息ID
                                msg_id = msg.get('msgid') or msg.get('id')
                                if not msg_id:
                                    time_value = msg.get('time') or msg.get('timestamp') or datetime.utcnow().timestamp()
                                    content_preview = (msg.get('content') or msg.get('text') or '')[:20]
                                    unique_string = f"{time_value}_{sender_name}_{content_preview}"
                                    msg_id = hashlib.md5(unique_string.encode('utf-8')).hexdigest()
                                
                                # 解析其他字段
                                msg_type = msg.get('type') or 'text'
                                content = msg.get('content') or msg.get('text') or ''
                                
                                # 清理内容
                                if isinstance(content, str):
                                    content = content.replace('\x00', '').replace('\r', '').strip()
                                
                                # 解析文件名
                                file_name = msg.get('file') or msg.get('fileName') or ''
                                if isinstance(file_name, str):
                                    file_name = file_name.replace('\x00', '').strip()
                                
                                file_size = str(msg.get('file_size') or msg.get('fileSize') or '')
                                
                                # 解析时间戳
                                timestamp = None
                                time_value = msg.get('time') or msg.get('timestamp')
                                
                                if time_value:
                                    try:
                                        if isinstance(time_value, (int, float)):
                                            timestamp = datetime.fromtimestamp(time_value)
                                        elif isinstance(time_value, str):
                                            timestamp = datetime.fromisoformat(time_value.replace('Z', '+00:00'))
                                        else:
                                            timestamp = datetime.utcnow()
                                    except:
                                        timestamp = datetime.utcnow()
                                else:
                                    timestamp = datetime.utcnow()
                                
                                # 创建聊天消息记录
                                chat = ChatMessage(
                                    message_id=msg_id,
                                    group_name=group_name,
                                    sender_name=sender_name,
                                    message_type=str(msg_type),
                                    content=content,
                                    file_name=file_name,
                                    file_size=file_size,
                                    timestamp=timestamp
                                )
                                
                                db.session.add(chat)
                                page_count += 1
                                total_count += 1
                                
                            except Exception as e:
                                logger.error(f"处理消息时出错: {e}")
                                continue
                        
                        # 提交本页数据
                        db.session.commit()
                        logger.info(f"群聊 {group_name} 第 {offset//page_size + 1} 页完成，写入 {page_count} 条消息")
                        
                        # 如果返回的消息数少于页大小，说明已经获取完所有数据
                        if len(messages) < page_size:
                            break
                        
                        offset += page_size
                        
                    except Exception as e:
                        logger.error(f"获取群聊 {group_name} 消息时出错: {e}")
                        break
            
            logger.info(f"项目 {project.project_name} 重新同步完成，总共写入 {total_count} 条消息")
        
        logger.info("所有项目重新同步完成！")

if __name__ == "__main__":
    print("开始重新同步聊天记录...")
    resync_chatlogs()
    print("重新同步完成！") 