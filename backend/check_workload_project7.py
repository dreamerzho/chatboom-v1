# 检查 WorkloadRecord 表中 project_id=7 的所有数据
# 用于定位数据链路断点

from app import app
from db import db
from models.workload import WorkloadRecord

with app.app_context():
    records = db.session.query(WorkloadRecord).filter_by(project_id=7).all()
    print(f'WorkloadRecord 表中 project_id=7 的数据条数: {len(records)}')
    for r in records:
        print({k: v for k, v in r.__dict__.items() if not k.startswith('_')}) 