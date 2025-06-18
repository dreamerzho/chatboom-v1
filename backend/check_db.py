# 数据库检查脚本
# 用于查看数据库中的项目数据

from app import create_app
from models import Project, ProjectChatroom
from db import db

def check_projects():
    """检查数据库中的项目数据"""
    app = create_app()
    with app.app_context():
        # 检查项目表
        projects = Project.query.all()
        print(f"数据库中共有 {len(projects)} 个项目:")
        
        for project in projects:
            print(f"\n项目ID: {project.id}")
            print(f"项目名称: {project.project_name}")
            print(f"项目描述: {project.description}")
            print(f"项目状态: {project.status}")
            print(f"创建时间: {project.created_at}")
            
            # 检查关联的群聊
            chatrooms = project.chatrooms.all()
            print(f"关联群聊数量: {len(chatrooms)}")
            for chatroom in chatrooms:
                print(f"  - 群聊: {chatroom.chatroom_name} ({chatroom.chatroom_type})")
        
        # 检查群聊表
        chatrooms = ProjectChatroom.query.all()
        print(f"\n数据库中共有 {len(chatrooms)} 个群聊记录:")
        for chatroom in chatrooms:
            print(f"  - {chatroom.chatroom_name} ({chatroom.chatroom_type}) - 项目ID: {chatroom.project_id}")

if __name__ == "__main__":
    check_projects() 