from backend.app import app
from backend.analysis_service import update_all_project_summaries

if __name__ == '__main__':
    with app.app_context():
        print('开始刷新 project_summary...')
        update_all_project_summaries()
        print('刷新完成！') 