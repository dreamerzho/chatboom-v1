from app import app
from db import db

with app.app_context():
    for table in db.metadata.sorted_tables:
        print(f"表名: {table.name}")
        for column in table.columns:
            print(f"  字段: {column.name} 类型: {column.type}")
        print("-" * 40)
        