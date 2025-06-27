import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.app import app
from backend.db import db
# 其余导入保持不变
# ...
# 删除 app = Flask(__name__) 和 db = SQLAlchemy(app) 相关代码
# 其余逻辑保持不变 