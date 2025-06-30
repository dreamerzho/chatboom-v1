# 未匹配人员角色管理API
# 支持分配角色时自动归集到员工表

from flask import Blueprint, request, jsonify
from backend.models.unmatched_person import UnmatchedPerson
from backend.models.employee import EmployeeMapping
from backend.db import db
from datetime import datetime

unmatched_bp = Blueprint('unmatched', __name__, url_prefix='/api/v1/unmatched')

@unmatched_bp.route('/', methods=['GET'])
def list_unmatched():
    """
    查询所有未匹配人员及其角色
    """
    persons = UnmatchedPerson.query.all()
    return jsonify({'success': True, 'data': [p.to_dict() for p in persons]})

@unmatched_bp.route('/<int:person_id>', methods=['PUT'])
def update_unmatched(person_id):
    """
    修改未匹配人员角色或备注，并支持自动归集到员工表
    """
    person = UnmatchedPerson.query.get(person_id)
    if not person:
        return jsonify({'success': False, 'error': '未找到该人员'}), 404
    data = request.json
    role = data.get('role', person.role)
    remark = data.get('remark', person.remark)
    group_type = data.get('group_type', 'external')
    person.role = role
    person.remark = remark
    person.updated_at = datetime.utcnow()
    # 判断是否需要自动归集到员工表
    employee_roles = ['员工', '项目经理', '设计师', '开发', '文案', '行政', '总监', '助理']
    if group_type == 'internal' and any(r in role for r in employee_roles):
        # 自动写入员工映射表（如已存在则跳过）
        exists = EmployeeMapping.query.filter_by(wechat_nickname=person.sender_name).first()
        if not exists:
            new_emp = EmployeeMapping(
                wechat_nickname=person.sender_name,
                real_name=person.sender_name,  # 默认用昵称，后续可手动完善
                position=role,
                name_abbreviation=''.join([w[0].upper() for w in person.sender_name if w.isalpha()][:2]) or 'XX',
                role='内部员工'
            )
            db.session.add(new_emp)
        # 从未匹配表中移除
        db.session.delete(person)
        db.session.commit()
        return jsonify({'success': True, 'data': '已归集为员工并移除未匹配人员'})
    db.session.commit()
    return jsonify({'success': True, 'data': person.to_dict()}) 