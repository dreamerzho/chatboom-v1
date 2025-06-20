# mock_dashboard_data.py
# 用于自动生成仪表盘核心表的 mock 数据，便于前端联调和演示
# 包含项目、员工、workload、项目健康、风险事件等样例数据

from datetime import datetime, timedelta
import random
from db import db
from models.project_health import ProjectHealthStats
from models.risk_event import RiskEvent
from models.workload import WorkloadRecord
from models.project import Project, ProjectChatroom
from models.employee import EmployeeMapping
from app import create_app  # 正确导入工厂函数

# ========== 配置区 ==========
PROJECT_NAMES = ['SKP项目', '越城天地', '金陵中环']
EMPLOYEE_NAMES = ['张三', '李四', '王五', '赵六']
ROLES = ['设计', '文案', 'PM', 'AE']
OUTPUT_TYPES = ['最终版-海报', '过程迭代版本', '内部修改意见', '外部群沟通']

# ========== mock 生成函数 ==========
def create_projects():
    """生成项目样例数据"""
    projects = []
    for name in PROJECT_NAMES:
        p = Project(project_name=name)
        db.session.add(p)
        projects.append(p)
    db.session.commit()
    return projects

def create_employees():
    """生成员工样例数据"""
    employees = []
    for i, name in enumerate(EMPLOYEE_NAMES):
        e = EmployeeMapping(
            wechat_nickname=f"mock_{name}_{i}",  # mock 微信昵称，确保唯一且非空
            real_name=name,
            role=ROLES[i % len(ROLES)],
            position=ROLES[i % len(ROLES)],      # mock 岗位
            name_abbreviation=name[0],           # mock 姓名缩写
        )
        db.session.add(e)
        employees.append(e)
    db.session.commit()
    return employees

def create_workloads(projects, employees):
    """生成工作量明细样例数据"""
    for p in projects:
        for e in employees:
            for i in range(7):
                w = WorkloadRecord(
                    employee_id=e.id,
                    project_id=p.id,
                    date=datetime.now().date() - timedelta(days=i),
                    role=e.role,
                    output_type=random.choice(OUTPUT_TYPES),
                    output_value=f"{e.real_name}-{p.project_name}-{i}",
                    we_value=round(random.uniform(0.2, 2.0), 2),
                    is_final=random.choice([True, False]),
                    is_iteration=random.choice([True, False]),
                    created_at=datetime.now() - timedelta(days=i)
                )
                db.session.add(w)
    db.session.commit()

def create_project_health_stats(projects):
    """生成项目健康度样例数据"""
    for p in projects:
        s = ProjectHealthStats(
            project_id=p.id,
            period='7d',
            health_score=random.randint(40, 100),
            avg_time_to_final=round(random.uniform(24, 72), 1),
            avg_revisions=round(random.uniform(1, 6), 1),
            risk_count=random.randint(0, 5),
            warning_count=random.randint(0, 3),
            negative_sentiment_rate=round(random.uniform(0, 0.2), 2),
            created_at=datetime.now()
        )
        db.session.add(s)
    db.session.commit()

def create_risk_events(projects, employees):
    """生成风险事件样例数据"""
    event_types = ['高迭代', '定稿周期异常', '情绪预警']
    for p in projects:
        for _ in range(random.randint(1, 3)):
            e = RiskEvent(
                project_id=p.id,
                employee_id=random.choice(employees).id,
                event_type=random.choice(event_types),
                event_desc=f"{p.project_name} 出现{random.choice(event_types)}",
                event_time=datetime.now() - timedelta(hours=random.randint(1, 48)),
                severity=random.choice(['高', '中', '低']),
                resolved=random.choice([True, False]),
                attribution=random.choice(['项目难度预警', '技能错配', None])
            )
            db.session.add(e)
    db.session.commit()

# ========== 主执行入口 ==========
def main():
    # ========== mock 数据填充前，先清空所有相关表，避免唯一约束和外键冲突 ==========
    # 1. 先清空所有依赖于项目的从表（如 project_chatrooms、workload、健康度、风险事件等）
    db.session.query(ProjectChatroom).delete()
    db.session.query(WorkloadRecord).delete()
    db.session.query(ProjectHealthStats).delete()
    db.session.query(RiskEvent).delete()
    # 2. 再清空主表（projects、employees）
    db.session.query(Project).delete()
    db.session.query(EmployeeMapping).delete()
    db.session.commit()
    # ========== 下面开始正常 mock 数据填充 ==========
    print('开始生成仪表盘 mock 数据...')
    projects = create_projects()
    employees = create_employees()
    create_workloads(projects, employees)
    create_project_health_stats(projects)
    create_risk_events(projects, employees)
    print('mock 数据生成完毕！')

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        main() 