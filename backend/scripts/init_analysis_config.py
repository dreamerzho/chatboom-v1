import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.models import AnalysisConfig
from backend.db import db
from app import app

def init_analysis_config():
    params = [
        {'key': 'rework_warning_delta', 'value': '1.0', 'description': '项目迭代次数高于基线多少算预警'},
        {'key': 'high_baseline_threshold', 'value': '4.0', 'description': '个人基线高于多少算技能错配'}
    ]
    with app.app_context():
        for p in params:
            config = AnalysisConfig.query.filter_by(key=p['key']).first()
            if not config:
                config = AnalysisConfig(**p)
                db.session.add(config)
            else:
                config.value = p['value']
                config.description = p['description']
        db.session.commit()
        print('AnalysisConfig参数初始化完成')

if __name__ == '__main__':
    init_analysis_config()
 