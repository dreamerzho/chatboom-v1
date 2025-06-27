# test_asset_model.py
# 测试 Asset 数据模型的基本增删查
import pytest
from models.asset import Asset
from db import db

def test_asset_create_and_query(app):
    with app.app_context():
        asset = Asset(
            original_name="240601-金陵中环-海报-3p-ZY-V1.psd",
            file_extension="psd",
            task_identifier="金陵中环-海报",
            submission_date="2024-06-01",
            version=1,
            workload_amount="3p",
            author_abbreviation="ZY",
            uploader="张三",
            upload_time="2024-06-01 10:00:00",
            status="compliant"
        )
        db.session.add(asset)
        db.session.commit()
        found = Asset.query.filter_by(original_name="240601-金陵中环-海报-3p-ZY-V1.psd").first()
        assert found is not None
        assert found.version == 1
        assert found.status == "compliant" 