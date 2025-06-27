# 检查聊天记录中的发送者名称
import sys
sys.path.append('.')
from app import db, ChatMessage
from flask import Flask
from config import SQLALCHEMY_DATABASE_URI

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    messages = ChatMessage.query.limit(20).all()
    print('=== 前20条消息的发送者 ===')
    for msg in messages:
        print(f'发送者: "{msg.sender_name}", 群聊: "{msg.group_name}", 内容: {msg.content[:50]}...')
    
    print('\n=== 所有唯一的发送者 ===')
    all_senders = db.session.query(ChatMessage.sender_name).distinct().all()
    for sender in all_senders:
        print(f'"{sender[0]}"') 