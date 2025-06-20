# scheduler.py
# 集成 APScheduler，实现定时自动聚合仪表盘数据
# 每天凌晨自动刷新项目健康统计，支持灵活扩展

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from aggregate_dashboard_data import aggregate_project_health
from app import create_app
import time

# 创建 Flask 应用上下文
app = create_app()

# 创建 APScheduler 实例
scheduler = BackgroundScheduler()

# 定义定时任务：每天凌晨 0 点自动聚合统计
@scheduler.scheduled_job('cron', hour=0, minute=0)
def scheduled_aggregate():
    with app.app_context():
        print(f"[定时任务] {datetime.now()} 自动聚合项目健康数据...")
        aggregate_project_health(period_days=7)
        print(f"[定时任务] {datetime.now()} 聚合完成！")

if __name__ == '__main__':
    print("启动 APScheduler 定时任务...")
    scheduler.start()
    try:
        # 保持主线程运行，防止脚本退出
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("定时任务已关闭。") 