import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.normalizer import Normalizer
from models.project import Project, ProjectChatroom
from models.employee import EmployeeMapping
from app import app


def test_project_normalization():
    print("\n=== 项目名称归一化测试 ===")
    for project in Project.query.all():
        pid = Normalizer.normalize_project_name(project.project_name)
        print(f"项目名: {project.project_name} -> 项目ID: {pid}")


def test_employee_normalization():
    print("\n=== 员工归一化测试 ===")
    for emp in EmployeeMapping.query.all():
        eid1 = Normalizer.normalize_employee(emp.wechat_nickname)
        eid2 = Normalizer.normalize_employee(emp.real_name)
        eid3 = Normalizer.normalize_employee(emp.name_abbreviation)
        print(f"微信昵称: {emp.wechat_nickname} -> 员工ID: {eid1}")
        print(f"真实姓名: {emp.real_name} -> 员工ID: {eid2}")
        print(f"姓名缩写: {emp.name_abbreviation} -> 员工ID: {eid3}")


def test_chatroom_normalization():
    print("\n=== 群聊归一化测试 ===")
    for chatroom in ProjectChatroom.query.all():
        cid = Normalizer.normalize_chatroom(chatroom.chatroom_name)
        print(f"群聊名: {chatroom.chatroom_name} -> 群聊ID: {cid}")


if __name__ == "__main__":
    with app.app_context():
        test_project_normalization()
        test_employee_normalization()
        test_chatroom_normalization() 