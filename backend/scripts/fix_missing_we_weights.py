import re
from backend.app import create_app
from backend.db import db
from backend.models.workload import WorkloadWeights

app = create_app()

# 请将你的同步日志文件路径替换为实际路径
LOG_PATH = 'sync_warning.log'

missing = set()
with open(LOG_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        m = re.search(r'WE权重未配置: (.+?)-(.+?)-(.+?)-final=(True|False)', line)
        if m:
            role, output_type, business_unit, is_final = m.groups()
            missing.add((role, output_type, business_unit, is_final == 'True'))

with app.app_context():
    count = 0
    for role, output_type, business_unit, is_final in missing:
        exists = WorkloadWeights.query.filter_by(
            role=role, output_type=output_type, business_unit=business_unit, is_final=is_final
        ).first()
        if not exists:
            w = WorkloadWeights(
                role=role,
                output_type=output_type,
                business_unit=business_unit,
                is_final=is_final,
                we_per_unit=1.0,
                iteration_multiplier=0.25,
                is_active=True
            )
            db.session.add(w)
            count += 1
    db.session.commit()
    print(f"已补全 {count} 条缺失的 WE 权重配置。") 