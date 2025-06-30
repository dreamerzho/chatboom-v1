import sys
import os

# 动态查找config.py所在目录并加入sys.path
possible_paths = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')),
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../')),
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')),
    os.path.abspath(os.path.dirname(__file__)),
]
for p in possible_paths:
    if os.path.exists(os.path.join(p, 'config.py')):
        if p not in sys.path:
            sys.path.insert(0, p)
        break

from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from backend.config import Config

# 连接数据库
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

# 需要检查的表及其时间字段
TABLES = [
    ("projects", "created_at"),
    ("employee_mappings", "created_at"),
    ("workload_records", "date"),
    ("file_records", "upload_time"),
    ("project_health_stats", "created_at"),
    ("asset", "submission_date"),
    ("risk_event", "event_time"),
]

now = datetime.now()
seven_days_ago = now - timedelta(days=7)

with engine.connect() as conn:
    print("\n==== 数据库核心表入库检查 ====")
    for table, time_field in TABLES:
        print(f"\n表: {table}")
        try:
            # 总行数
            total = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"  总行数: {total}")
            if total == 0:
                print("  [警告] 该表无数据！")
                if table == "workload_records":
                    print("  [修复建议] 请检查同步/导入脚本，确保工作量明细能正确写入workload_records，或用脚本批量补充测试数据。")
                continue
            # 最近一条数据时间
            try:
                latest = conn.execute(text(f"SELECT MAX({time_field}) FROM {table}")).scalar()
                print(f"  最新数据时间: {latest}")
                # 近7天数据量
                recent = conn.execute(text(f"SELECT COUNT(*) FROM {table} WHERE {time_field} >= :since"), {"since": seven_days_ago}).scalar()
                print(f"  近7天数据量: {recent}")
                if not recent or recent == 0:
                    print("  [警告] 近7天无数据！")
                    if table == "file_records":
                        print("  [修复建议] 检查file_records的upload_time字段写入逻辑，确保为真实上传时间，或修正历史数据。")
                if table == "file_records" and latest and str(latest).startswith("1970"):
                    print("  [警告] file_records的upload_time异常，疑似未写入真实时间！")
                    print("  [修复建议] 检查数据导入逻辑，修正upload_time字段。")
            except Exception as e:
                print(f"  [提示] 无法获取时间字段({time_field})，原因: {e}")
        except Exception as e:
            print(f"  [警告] 检查表{table}时出错: {e}")
            if 'does not exist' in str(e) or '不存在' in str(e):
                print(f"  [提示] 表{table}不存在，可忽略或修正表名。")
    print("\n==== 检查完毕 ====") 