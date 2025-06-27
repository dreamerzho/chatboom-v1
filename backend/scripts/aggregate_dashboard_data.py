# aggregate_dashboard_data.py
# 自动聚合仪表盘核心数据，定期统计项目健康、风险事件等
# 支持手动和定时任务调用，便于前端仪表盘实时刷新

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta
from backend.db import db
from models.project import Project
from models.workload import WorkloadRecord
from models.project_health import ProjectHealthStats
from models.risk_event import RiskEvent

# ========== 聚合统计逻辑 ==========
def aggregate_project_health(period_days=7):
    """
    聚合统计每个项目的健康度、定稿周期、平均迭代、风险事件等，写入 project_health_stats
    """
    now = datetime.now()
    since = now - timedelta(days=period_days)
    projects = Project.query.all()
    for p in projects:
        # 统计该项目近 period_days 的工作量
        workloads = WorkloadRecord.query.filter(
            WorkloadRecord.project_id == p.id,
            WorkloadRecord.date >= since.date()
        ).all()
        # 统计健康分、定稿周期、平均迭代等（移除mock逻辑，改为合理默认值或真实统计）
        health_score = 100 - len([w for w in workloads if w.is_iteration]) * 2  # 迭代多则健康分低
        # avg_time_to_final 应根据实际数据统计，这里设为0或None
        avg_time_to_final = None
        avg_revisions = sum([w.iteration_count for w in workloads]) / len(workloads) if workloads else 0
        risk_count = RiskEvent.query.filter(
            RiskEvent.project_id == p.id,
            RiskEvent.event_time >= since
        ).count()
        # warning_count、negative_sentiment_rate 也设为None或根据实际统计
        warning_count = None
        negative_sentiment_rate = None
        # 写入 project_health_stats
        stat = ProjectHealthStats(
            project_id=p.id,
            period=f'{period_days}d',
            health_score=max(0, health_score),
            avg_time_to_final=avg_time_to_final,
            avg_revisions=avg_revisions,
            risk_count=risk_count,
            warning_count=warning_count,
            negative_sentiment_rate=negative_sentiment_rate,
            created_at=now
        )
        db.session.add(stat)
    db.session.commit()
    print(f'已聚合统计所有项目的健康度（周期：{period_days}天）')

# ========== 主执行入口 ==========
if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        aggregate_project_health(period_days=7) 