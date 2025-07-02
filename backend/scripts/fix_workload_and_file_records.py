import sys
import os
from datetime import datetime, timedelta
import random
from sqlalchemy import create_engine, text
# 动态查找config.py
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
from backend.config import Config

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

def fix_file_records_upload_time(conn):
    print("\n[修正] file_records.upload_time 字段...")
    # 查找所有upload_time为1970-01-01的记录
    rows = conn.execute(text("SELECT id FROM file_records WHERE upload_time <= '1970-01-02'")).fetchall()
    if not rows:
        print("  无需修正，未发现异常upload_time。")
        return
    now = datetime.now()
    for row in rows:
        # 随机分布到近7天
        new_time = now - timedelta(days=random.randint(0, 6), hours=random.randint(0, 23))
        conn.execute(text("UPDATE file_records SET upload_time = :t WHERE id = :id"), {"t": new_time, "id": row.id})
    print(f"  已修正 {len(rows)} 条file_records.upload_time异常数据。")

def batch_insert_workload_records(conn):
    print("\n[补充] workload_records 测试数据...")
    # 获取所有项目和员工
    projects = conn.execute(text("SELECT id FROM projects")).fetchall()
    employees = conn.execute(text("SELECT id FROM employee_mappings")).fetchall()
    if not projects or not employees:
        print("  [警告] 无法补充，项目或员工表无数据。")
        return
    now = datetime.now()
    count = 0
    for p in projects:
        for e in employees:
            # 随机生成近7天的工作量
            for i in range(random.randint(2, 5)):
                date = now - timedelta(days=random.randint(0, 6))
                we_value = round(random.uniform(1, 10), 2)
                conn.execute(text(
                    "INSERT INTO workload_records (employee_id, project_id, date, role, output_type, we_value, is_final, is_iteration, iteration_count, created_at) "
                    "VALUES (:eid, :pid, :date, :role, :otype, :we, :is_final, :is_iter, :iter_count, :created_at)"
                ), {
                    "eid": e.id,
                    "pid": p.id,
                    "date": date.date(),
                    "role": "设计",
                    "otype": "最终版-海报",
                    "we": we_value,
                    "is_final": True,
                    "is_iter": False,
                    "iter_count": 1,
                    "created_at": date
                })
                count += 1
    print(f"  已批量插入 {count} 条workload_records测试数据。")
    # 新增：插入后立即查询workload_records表总数
    total = conn.execute(text("SELECT COUNT(*) FROM workload_records")).scalar()
    print(f"workload_records表当前总数: {total}")

if __name__ == "__main__":
    with engine.connect() as conn:
        trans = conn.begin()
        try:
        fix_file_records_upload_time(conn)
        batch_insert_workload_records(conn)
            trans.commit()
        except Exception as e:
            print(f"[ERROR] 数据写入异常: {e}")
            trans.rollback()
    print("\n[完成] 数据修复与补充已执行。")