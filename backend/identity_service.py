from backend.models.employee import EmployeeMapping
import re
from backend.utils.normalizer import Normalizer

def norm(s):
    return Normalizer.normalize_str(s)

class IdentityService:
    def __init__(self, session):
        self.session = session
        self._refresh_cache()

    def _refresh_cache(self):
        employees = self.session.query(EmployeeMapping).all()
        self.real_name_map = {norm(e.real_name): e for e in employees}
        self.nickname_map = {norm(e.wechat_nickname): e for e in employees}
        self.abbr_map = {norm(e.name_abbreviation): e for e in employees}
        self.id_map = {str(e.id): e for e in employees}
        self.all_employees = employees

    def identify_employee(self, sender_name: str):
        if not sender_name:
            return None
        u = norm(sender_name)
        # 1. 精确匹配
        if u in self.nickname_map:
            return self.nickname_map[u]
        if u in self.real_name_map:
            return self.real_name_map[u]
        if u in self.abbr_map:
            return self.abbr_map[u]
        if u in self.id_map:
            return self.id_map[u]
        # 2. 部分匹配（中文、英文、数字混合）
        for e in self.all_employees:
            for field in [e.wechat_nickname, e.real_name, e.name_abbreviation, str(e.id)]:
                if u and norm(u) in norm(field):
                    return e
        # 3. 正则数字匹配（如仅数字）
        if re.fullmatch(r'\d+', u):
            for e in self.all_employees:
                if u == str(e.id):
                    return e
        return None 