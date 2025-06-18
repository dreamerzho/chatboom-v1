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
  Alert
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  UserOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { employeeAPI } from '../../lib/api';

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

function EmployeesPage() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<Employee | null>(null);
  const [form] = Form.useForm();

  // 获取员工列表
  const fetchEmployees = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await employeeAPI.getEmployees();
      
      if (response.success) {
        setEmployees(response.data || []);
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

  // 组件加载时获取数据
  useEffect(() => {
    fetchEmployees();
  }, []);

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
      render: (_, record: Employee) => (
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
    </div>
  );
}

export default EmployeesPage;