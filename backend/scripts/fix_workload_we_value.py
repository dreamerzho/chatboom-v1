from backend.app import create_app
from backend.db import db
from backend.models.workload import WorkloadRecord, WorkloadWeights

app = create_app()

with app.app_context():
    count = 0
    for record in WorkloadRecord.query.filter_by(we_value=0).all():
        weight = WorkloadWeights.query.filter_by(
            role=record.role,
            output_type=record.output_type,
            business_unit=record.business_unit,
            is_final=record.is_final,
            is_active=True
        ).first()
        if weight:
            record.we_value = weight.we_per_unit * (weight.iteration_multiplier if record.is_iteration else 1.0) * (record.quantity or 1.0)
            count += 1
    db.session.commit()
    print(f'已修复 {count} 条 WorkloadRecord 的 we_value') 