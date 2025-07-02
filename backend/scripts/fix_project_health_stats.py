import os
import sys
from datetime import datetime, timedelta
from backend.db import db
from backend.models.project import Project
from backend.models.risk_event import RiskEvent
from backend.models.file import FileRecord
from backend.models.project_health import ProjectHealthStats
from backend.models.workload import WorkloadRecord
from backend.models.chat import ChatMessage
from sqlalchemy import func

# 统计周期（以7天为单位）
PERIOD_DAYS = 7

def get_week_start(dt):
    # 返回本周一0点
    return (dt - timedelta(days=dt.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

def main(project_id=None):
    print("=== 开始统计并修复项目健康趋势数据（V2模型） ===")
    now = datetime.now()
    week_start = get_week_start(now)
    week_end = week_start + timedelta(days=PERIOD_DAYS)
    # 查询所有项目或指定项目
    if project_id:
        projects = Project.query.filter_by(id=project_id).all()
    else:
        projects = Project.query.all()
    for project in projects:
        # 1. 风险事件数
        risk_count = RiskEvent.query.filter(
            RiskEvent.project_id == project.id,
            RiskEvent.event_time >= week_start,
            RiskEvent.event_time < week_end
        ).count()
        # 2. 返工文件数
        warning_count = FileRecord.query.filter(
            FileRecord.project_id == project.id,
            FileRecord.upload_time >= week_start,
            FileRecord.upload_time < week_end,
            FileRecord.status == 'rework'
        ).count()
        # 3. 定稿周期（小时）
        finals = WorkloadRecord.query.filter(
            WorkloadRecord.project_id == project.id,
            WorkloadRecord.is_final == True,
            WorkloadRecord.date >= week_start.date(),
            WorkloadRecord.date < week_end.date()
        ).all()
        time_to_finals = []
        for f in finals:
            # 找到同一output_value的最早版本
            all_versions = WorkloadRecord.query.filter(
                WorkloadRecord.project_id == project.id,
                WorkloadRecord.output_value == f.output_value
            ).order_by(WorkloadRecord.date.asc()).all()
            if all_versions:
                first = all_versions[0]
                last = all_versions[-1]
                hours = (last.date - first.date).days * 24
                time_to_finals.append(hours)
        avg_time_to_final = round(sum(time_to_finals)/len(time_to_finals),2) if time_to_finals else None
        # 4. 平均迭代次数
        all_outputs = WorkloadRecord.query.filter(
            WorkloadRecord.project_id == project.id,
            WorkloadRecord.date >= week_start.date(),
            WorkloadRecord.date < week_end.date()
        ).with_entities(WorkloadRecord.output_value).distinct().all()
        revisions = []
        for out in all_outputs:
            count = WorkloadRecord.query.filter(
                WorkloadRecord.project_id == project.id,
                WorkloadRecord.output_value == out[0]
            ).count()
            revisions.append(count)
        avg_revisions = round(sum(revisions)/len(revisions),2) if revisions else None
        # 5. 负面情绪频率
        negative_words = ['差','糟糕','失误','问题','延误','投诉','不满','失败','返工','压力','崩溃','难受','生气','愤怒','无语','烦','累','吐槽','不行','不对','不合理','不满意']
        chat_msgs = ChatMessage.query.filter(
            ChatMessage.project_id == project.id,
            ChatMessage.timestamp >= week_start,
            ChatMessage.timestamp < week_end
        ).all()
        total_texts = 0
        negative_count = 0
        for m in chat_msgs:
            try:
                import json
                content = json.loads(m.content)
                text = content.get('text','') if isinstance(content,dict) else ''
                if text:
                    total_texts += 1
                    if any(word in text for word in negative_words):
                        negative_count += 1
            except Exception:
                continue
        negative_sentiment_rate = round(negative_count/total_texts,3) if total_texts else None
        # 6. 健康分综合打分
        health_score = 100
        health_score -= warning_count * 5
        health_score -= risk_count * 10
        if avg_time_to_final and avg_time_to_final > 168: # 7天
            health_score -= 10
        if avg_revisions and avg_revisions > 3:
            health_score -= 10
        if negative_sentiment_rate and negative_sentiment_rate > 0.05:
            health_score -= 5
        health_score = max(0, min(health_score, 100))
        # 检查是否已存在本周记录，存在则更新
        stat = ProjectHealthStats.query.filter_by(project_id=project.id, period='7d', created_at=week_start).first()
        if not stat:
            stat = ProjectHealthStats(
                project_id=project.id,
                period='7d',
                health_score=health_score,
                avg_time_to_final=avg_time_to_final,
                avg_revisions=avg_revisions,
                risk_count=risk_count,
                warning_count=warning_count,
                negative_sentiment_rate=negative_sentiment_rate,
                created_at=week_start
            )
            db.session.add(stat)
        else:
            stat.risk_count = risk_count
            stat.warning_count = warning_count
            stat.health_score = health_score
            stat.avg_time_to_final = avg_time_to_final
            stat.avg_revisions = avg_revisions
            stat.negative_sentiment_rate = negative_sentiment_rate
        print(f"项目{project.id} 健康分:{health_score} 风险:{risk_count} 返工:{warning_count} 定稿周期:{avg_time_to_final}h 迭代:{avg_revisions} 负面:{negative_sentiment_rate}")
    db.session.commit()
    print("=== 健康趋势数据统计完成 ===")

if __name__ == "__main__":
    from backend.app import app
    with app.app_context():
        main() 