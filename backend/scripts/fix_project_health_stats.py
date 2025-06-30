import os
import sys
from datetime import datetime, timedelta
from backend.db import db
from backend.models.project import Project
from backend.models.risk_event import RiskEvent
from backend.models.file import FileRecord
from backend.models.project_health import ProjectHealthStats

# 统计周期（以7天为单位）
PERIOD_DAYS = 7

def get_week_start(dt):
    # 返回本周一0点
    return (dt - timedelta(days=dt.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

def main():
    print("=== 开始统计并修复项目健康趋势数据 ===")
    now = datetime.now()
    week_start = get_week_start(now)
    week_end = week_start + timedelta(days=PERIOD_DAYS)
    # 查询所有项目
    projects = Project.query.all()
    for project in projects:
        # 统计本周风险事件数
        risk_count = RiskEvent.query.filter(
            RiskEvent.project_id == project.id,
            RiskEvent.event_time >= week_start,
            RiskEvent.event_time < week_end
        ).count()
        # 统计本周返工文件数（status='rework'）
        warning_count = FileRecord.query.filter(
            FileRecord.project_id == project.id,
            FileRecord.upload_time >= week_start,
            FileRecord.upload_time < week_end,
            FileRecord.status == 'rework'
        ).count()
        # 统计健康分（可用默认100或后续完善）
        health_score = 100
        # 检查是否已存在本周记录，存在则更新
        stat = ProjectHealthStats.query.filter_by(project_id=project.id, period='7d', created_at=week_start).first()
        if not stat:
            stat = ProjectHealthStats(
                project_id=project.id,
                period='7d',
                health_score=health_score,
                risk_count=risk_count,
                warning_count=warning_count,
                created_at=week_start
            )
            db.session.add(stat)
        else:
            stat.risk_count = risk_count
            stat.warning_count = warning_count
            stat.health_score = health_score
        print(f"项目{project.id} 本周风险事件: {risk_count} 返工: {warning_count}")
    db.session.commit()
    print("=== 健康趋势数据统计完成 ===")

if __name__ == "__main__":
    from backend.app import app
    with app.app_context():
        main() 