// 员工管理页面
// 展示所有员工及其岗位，支持增删改查操作
// 集成后端API，实现真实数据管理

'use client';

import React, { useState, useEffect } from 'react';
import { 
  Table, 
  Typography, 
  Button, 
  Modal, 
  Form, 
  Input, 
  message, 
  Space, 
  Popconfirm,
  Card,
  Statistic,
  Row,
  Col,
  Spin,
  Alert,
  Select
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  UserOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { employeeAPI, unmatchedAPI, projectAPI } from '../../lib/api';

const { Title, Text } = Typography;

// 员工数据接口
interface Employee {
  id: number;
  wechat_nickname: string;
  real_name: string;
  position: string;
  name_abbreviation: string;
  created_at: string;
  updated_at: string;
}

// 员工表单数据接口
interface EmployeeFormData {
  wechat_nickname: string;
  real_name: string;
  position: string;
  name_abbreviation: string;
}

// 未匹配人员类型
type UnmatchedPerson = {
  id: number;
  sender_name: string;
  group_name: string;
  role: string;
  remark: string;
  created_at: string;
  updated_at: string;
};

// 项目数据接口
interface Project {
  id: number;
  project_name: string;
  external_group_name?: string;
  internal_group_name?: string;
}

// 常用角色标签
const ROLE_OPTIONS = [
  '员工', '项目经理', '客户', '老板', '行政', '客户策划', '客户营销', '客户总监', '客户助理', '其他'
];

/**
 * 智能推荐角色函数
 * 根据群聊名、发言人昵称、历史岗位统计等，返回推荐角色列表
 * @param person 未匹配人员对象
 * @param employees 员工列表
 * @returns 推荐角色数组
 */
function getRecommendedRoles(person: UnmatchedPerson | null, employees: Employee[]): string[] {
  if (!person) return [];
  const { group_name, sender_name } = person;
  // 1. 根据群聊名关键词推荐
  const groupBased: string[] = [];
  if (group_name.includes('客户')) groupBased.push('客户');
  if (group_name.includes('老板')) groupBased.push('老板');
  if (group_name.includes('行政')) groupBased.push('行政');
  if (group_name.includes('策划')) groupBased.push('客户策划');
  if (group_name.includes('营销')) groupBased.push('客户营销');
  if (group_name.includes('总监')) groupBased.push('客户总监');
  // 2. 历史岗位统计（同昵称员工出现频率最高的岗位）
  const matched = employees.filter(e => e.wechat_nickname === sender_name);
  if (matched.length > 0) {
    const freq: Record<string, number> = {};
    matched.forEach(e => { freq[e.position] = (freq[e.position] || 0) + 1; });
    const sorted = Object.entries(freq).sort((a, b) => b[1] - a[1]);
    if (sorted.length > 0) groupBased.unshift(sorted[0][0]);
  }
  // 3. 默认推荐"员工"
  if (groupBased.length === 0) groupBased.push('员工');
  // 4. 去重
  return Array.from(new Set(groupBased));
}

function EmployeesPage() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<Employee | null>(null);
  const [form] = Form.useForm();
  const [unmatchedPersons, setUnmatchedPersons] = useState<UnmatchedPerson[]>([]);
  const [unmatchedLoading, setUnmatchedLoading] = useState(true);
  const [unmatchedModal, setUnmatchedModal] = useState<{visible: boolean, person: UnmatchedPerson | null, recommendedProject?: Project | null}>({visible: false, person: null, recommendedProject: null});
  const [projects, setProjects] = useState<Project[]>([]);

  // 获取员工列表
  const fetchEmployees = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await employeeAPI.getEmployees();
      
      if (response.success) {
        setEmployees(Array.isArray(response.data) ? response.data : []);
      } else {
        setError(response.error || '获取员工列表失败');
        message.error('获取员工列表失败');
      }
    } catch (err) {
      console.error('获取员工列表失败:', err);
      setError('网络请求失败');
      message.error('网络请求失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取未匹配人员
  const fetchUnmatchedPersons = async () => {
    try {
      setUnmatchedLoading(true);
      const response = await unmatchedAPI.getUnmatchedPersons();
      if (response.success) {
        setUnmatchedPersons(Array.isArray(response.data) ? response.data : []);
      } else {
        message.error('获取未匹配人员失败');
      }
    } catch {
      message.error('获取未匹配人员失败');
    } finally {
      setUnmatchedLoading(false);
    }
  };

  // 获取项目列表
  const fetchProjects = async () => {
    try {
      const res = await projectAPI.getProjects();
      if (res.success && Array.isArray(res.data)) {
        setProjects(res.data);
      } else {
        setProjects([]);
      }
    } catch {
      setProjects([]);
    }
  };

  // 添加员工
  const handleAddEmployee = async (values: EmployeeFormData) => {
    try {
      const response = await employeeAPI.addEmployee(values);
      
      if (response.success) {
        message.success('员工添加成功');
        setModalVisible(false);
        form.resetFields();
        fetchEmployees(); // 刷新列表
      } else {
        message.error(response.error || '添加员工失败');
      }
    } catch (err) {
      console.error('添加员工失败:', err);
      message.error('添加员工失败');
    }
  };

  // 更新员工
  const handleUpdateEmployee = async (values: EmployeeFormData) => {
    if (!editingEmployee) return;
    
    try {
      const response = await employeeAPI.updateEmployee(editingEmployee.id, values);
      
      if (response.success) {
        message.success('员工信息更新成功');
        setModalVisible(false);
        setEditingEmployee(null);
        form.resetFields();
        fetchEmployees(); // 刷新列表
      } else {
        message.error(response.error || '更新员工失败');
      }
    } catch (err) {
      console.error('更新员工失败:', err);
      message.error('更新员工失败');
    }
  };

  // 删除员工
  const handleDeleteEmployee = async (id: number) => {
    console.log('Attempting to delete employee with ID:', id);
    try {
      const response = await employeeAPI.deleteEmployee(id);
      
      if (response.success) {
        message.success('员工删除成功');
        fetchEmployees(); // 刷新列表
      } else {
        message.error(response.error || '删除员工失败');
      }
    } catch (err) {
      console.error('删除员工失败:', err);
      message.error('删除员工失败');
    }
  };

  // 打开编辑模态框
  const handleEdit = (record: Employee) => {
    setEditingEmployee(record);
    form.setFieldsValue({
      wechat_nickname: record.wechat_nickname,
      real_name: record.real_name,
      position: record.position,
      name_abbreviation: record.name_abbreviation
    });
    setModalVisible(true);
  };

  // 打开添加模态框
  const handleAdd = () => {
    setEditingEmployee(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 关闭模态框
  const handleCancel = () => {
    setModalVisible(false);
    setEditingEmployee(null);
    form.resetFields();
  };

  // 提交表单
  const handleSubmit = () => {
    form.validateFields().then(values => {
      if (editingEmployee) {
        handleUpdateEmployee(values);
      } else {
        handleAddEmployee(values);
      }
    });
  };

  // 分配角色
  const handleAssignRole = (person: UnmatchedPerson) => {
    const recommendedProject = getRecommendedProject(person, projects);
    setUnmatchedModal({visible: true, person, recommendedProject});
  };
  const handleUnmatchedModalOk = async (values: {role: string, remark: string, project_id?: number}) => {
    if (!unmatchedModal.person) return;
    const groupType = unmatchedModal.person.group_name.includes('内部') ? 'internal' : 'external';
    try {
      const res = await unmatchedAPI.updateUnmatchedPerson(unmatchedModal.person.id, {
        ...values,
        group_type: groupType
      } as Partial<UnmatchedPerson>);
      if (res.success) {
        message.success('角色分配成功');
        setUnmatchedModal({visible: false, person: null, recommendedProject: undefined});
        fetchUnmatchedPersons();
        fetchEmployees();
      } else {
        message.error('角色分配失败');
      }
    } catch {
      message.error('角色分配失败');
    }
  };
  const handleUnmatchedModalCancel = () => {
    setUnmatchedModal({visible: false, person: null, recommendedProject: undefined});
  };

  // 页面加载时获取员工、未匹配人员、项目
  useEffect(() => {
    fetchEmployees();
    fetchUnmatchedPersons();
    fetchProjects();
  }, []);

  // 推荐项目函数：根据群聊名模糊匹配项目名/群聊名
  function getRecommendedProject(person: UnmatchedPerson | null, projects: Project[]): Project | null {
    if (!person || projects.length === 0) return null;
    const { group_name } = person;
    // 优先项目名包含群聊名
    let match = projects.find(p => group_name && p.project_name && group_name.includes(p.project_name));
    if (match) return match;
    // 其次项目的external_group_name/internal_group_name包含群聊名
    match = projects.find(p => (p.external_group_name && group_name && group_name.includes(p.external_group_name)) || (p.internal_group_name && group_name && group_name.includes(p.internal_group_name)));
    if (match) return match;
    // 反向：项目名包含群聊名
    match = projects.find(p => p.project_name && group_name && p.project_name.includes(group_name));
    if (match) return match;
    return null;
  }

  // 表格列定义
const columns = [
    {
      title: '真实姓名',
      dataIndex: 'real_name',
      key: 'real_name',
      render: (text: string) => (
        <Space>
          <UserOutlined style={{ color: '#1890ff' }} />
          <Text strong>{text}</Text>
        </Space>
      ),
    },
    {
      title: '微信昵称',
      dataIndex: 'wechat_nickname',
      key: 'wechat_nickname',
    },
    {
      title: '岗位',
      dataIndex: 'position',
      key: 'position',
    },
    {
      title: '姓名缩写',
      dataIndex: 'name_abbreviation',
      key: 'name_abbreviation',
      render: (text: string) => (
        <span style={{ 
          background: '#1890ff', 
          color: 'white', 
          padding: '2px 8px', 
          borderRadius: 4,
          fontSize: 12
        }}>
          {text}
        </span>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => new Date(text).toLocaleDateString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: Employee) => (
        <Space size="middle">
          <Button 
            type="link" 
            icon={<EditOutlined />} 
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个员工吗？"
            description="删除后无法恢复，请谨慎操作。"
            onConfirm={() => handleDeleteEmployee(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button 
              type="link" 
              danger 
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 加载状态
  if (loading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text>正在加载员工数据...</Text>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      {/* 页面标题和操作按钮 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>员工视图</Title>
        <Space>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={fetchEmployees}
            loading={loading}
          >
            刷新
          </Button>
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={handleAdd}
          >
            添加员工
          </Button>
        </Space>
      </div>

      {/* 错误提示 */}
      {error && (
        <Alert
          message="数据加载失败"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: 24 }}
          action={
            <Button size="small" onClick={fetchEmployees}>
              重试
            </Button>
          }
        />
      )}

      {/* 员工统计 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="员工总数"
              value={employees.length}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="设计师"
              value={employees.filter(emp => emp.position.includes('设计')).length}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="开发人员"
              value={employees.filter(emp => emp.position.includes('开发')).length}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="其他岗位"
              value={employees.filter(emp => !emp.position.includes('设计') && !emp.position.includes('开发')).length}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 员工列表 */}
      <Card>
        <Table
          columns={columns}
          dataSource={employees}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
        />
      </Card>

      {/* 未匹配人员分区 */}
      <Card title="未匹配人员（需人工分配角色）" style={{ marginTop: 32, marginBottom: 24 }}>
        <Table
          dataSource={unmatchedPersons}
          loading={unmatchedLoading}
          rowKey="id"
          pagination={{ pageSize: 8 }}
          columns={[
            { title: '发言人昵称', dataIndex: 'sender_name', key: 'sender_name' },
            { title: '群聊名称', dataIndex: 'group_name', key: 'group_name' },
            { title: '当前角色', dataIndex: 'role', key: 'role', render: (text: string) => <Text type={text==='未知'?'danger':'success'}>{text}</Text> },
            { title: '备注', dataIndex: 'remark', key: 'remark' },
            { title: '操作', key: 'action', render: (_: unknown, record: UnmatchedPerson) => (
              <Button type="link" onClick={() => handleAssignRole(record)}>分配角色</Button>
            ) },
          ]}
        />
      </Card>

      {/* 添加/编辑员工模态框 */}
      <Modal
        title={editingEmployee ? '编辑员工' : '添加员工'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={handleCancel}
        okText="确定"
        cancelText="取消"
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          style={{ marginTop: 16 }}
        >
          <Form.Item
            name="real_name"
            label="真实姓名"
            rules={[
              { required: true, message: '请输入真实姓名' },
              { max: 20, message: '姓名不能超过20个字符' }
            ]}
          >
            <Input placeholder="请输入真实姓名" />
          </Form.Item>
          
          <Form.Item
            name="wechat_nickname"
            label="微信昵称"
            rules={[
              { required: true, message: '请输入微信昵称' },
              { max: 50, message: '微信昵称不能超过50个字符' }
            ]}
          >
            <Input placeholder="请输入微信昵称" />
          </Form.Item>
          
          <Form.Item
            name="position"
            label="岗位"
            rules={[
              { required: true, message: '请输入岗位' },
              { max: 30, message: '岗位不能超过30个字符' }
            ]}
          >
            <Input placeholder="请输入岗位，如：设计师、开发工程师等" />
          </Form.Item>
          
          <Form.Item
            name="name_abbreviation"
            label="姓名缩写"
            rules={[
              { required: true, message: '请输入姓名缩写' },
              { max: 10, message: '姓名缩写不能超过10个字符' },
              { pattern: /^[A-Za-z]+$/, message: '姓名缩写只能包含英文字母' }
            ]}
          >
            <Input placeholder="请输入姓名缩写，如：ZS、LJ等" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 分配角色弹窗 */}
      <Modal
        title="分配/修改角色"
        open={unmatchedModal.visible}
        onCancel={handleUnmatchedModalCancel}
        onOk={() => {
          (document.getElementById('unmatched-role-form-submit') as HTMLElement)?.click();
        }}
        okText="确定"
        cancelText="取消"
        destroyOnClose
      >
        {/* 智能推荐提示 */}
        {unmatchedModal.visible && (
          <Alert
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
            message={
              <span>
                推荐角色：
                <span style={{ color: '#1890ff', fontWeight: 600 }}>
                  {getRecommendedRoles(unmatchedModal.person, employees).join(' / ') || '员工'}
                </span>
                <span style={{ marginLeft: 8, color: '#888', fontSize: 12 }}>
                  （可直接选择或自定义输入）
                </span>
                {unmatchedModal.recommendedProject && (
                  <span style={{ marginLeft: 16, color: '#52c41a', fontWeight: 600 }}>
                    推荐项目：{unmatchedModal.recommendedProject.project_name}
                  </span>
                )}
              </span>
            }
          />
        )}
        <Form
          initialValues={{
            role: unmatchedModal.person?.role || getRecommendedRoles(unmatchedModal.person, employees)[0] || '',
            remark: unmatchedModal.person?.remark || '',
            project_id: unmatchedModal.recommendedProject?.id || undefined
          }}
          onFinish={handleUnmatchedModalOk}
          layout="vertical"
        >
          <Form.Item 
            name="role" 
            label={<span>角色 <span style={{ color: 'red' }}>*</span></span>} 
            rules={[{ required: true, message: '请选择或输入角色（必填）' }]}
            extra={<span style={{ color: '#888', fontSize: 12 }}>支持多标签，优先选择推荐项</span>}
          > 
            <Select
              mode="tags"
              style={{ width: '100%' }}
              placeholder="请选择或输入角色"
              options={ROLE_OPTIONS.map(opt => ({ label: opt, value: opt, style: getRecommendedRoles(unmatchedModal.person, employees).includes(opt) ? { fontWeight: 700, color: '#1890ff' } : {} }))}
              maxTagCount={3}
              showSearch
              allowClear
            />
          </Form.Item>
          <Form.Item
            name="project_id"
            label={<span>归属项目 <span style={{ color: 'red' }}>*</span></span>}
            rules={[{ required: true, message: '请选择归属项目（必填）' }]}
            extra={<span style={{ color: '#888', fontSize: 12 }}>系统已自动推荐，支持手动修改</span>}
          >
            <Select
              showSearch
              placeholder="请选择归属项目"
              optionFilterProp="children"
              options={projects.map(p => ({ label: p.project_name, value: p.id }))}
              value={unmatchedModal.recommendedProject?.id}
              allowClear
            />
          </Form.Item>
          <Form.Item name="remark" label="备注">
            <Input.TextArea placeholder="可填写推测依据或其他说明" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" id="unmatched-role-form-submit" style={{ display: 'none' }}>提交</Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default EmployeesPage;