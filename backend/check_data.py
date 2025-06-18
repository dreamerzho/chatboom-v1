#!/usr/bin/env python3
# 检查数据库中的数据

from app import db, ChatMessage
from flask import Flask
from config import SQLALCHEMY_DATABASE_URI

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    # 检查ChatMessage表的数据
    count = ChatMessage.query.count()
    print(f'ChatMessage count: {count}')
    
    if count > 0:
        msg = ChatMessage.query.first()
        print(f'First message: {msg.sender_name}, {msg.content[:50] if msg.content else "No content"}...')
        
        # 检查最近的几条消息
        recent_msgs = ChatMessage.query.order_by(ChatMessage.timestamp.desc()).limit(5).all()
        print(f'\nRecent messages:')
        for msg in recent_msgs:
            print(f'- {msg.sender_name}: {msg.content[:30] if msg.content else "No content"}...')
    else:
        print('No chat messages found in database') 