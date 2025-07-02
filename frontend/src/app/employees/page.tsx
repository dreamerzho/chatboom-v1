// 员工管理页面 - V2 (样式复刻版)
// 页面功能:
// 1. 顶部显示核心统计指标：员工总数、高负荷员工、核心贡献者、待分配人员。
// 2. 提供员工搜索和添加员工的功能入口。
// 3. 以表格形式展示员工列表，包含头像、岗位、总负荷指数、参与项目、平均迭代等信息。
// 4. 对高负荷员工进行视觉高亮（红色背景和红色指数）。
// 5. 点击"详情"可查看员工详细信息（功能待实现）。
// 6. 点击"添加员工"或编辑时，沿用旧的模态框逻辑。

'use client';

import React, { useState, useEffect, useMemo } from 'react';
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
  Select,
  Avatar,
  Tag,
  Tooltip,
  Upload,
} from 'antd';
import {
  PlusOutlined,
  UserOutlined,
  ReloadOutlined,
  SearchOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons';
import { employeeAPI, unmatchedAPI, projectAPI } from '@lib/api';
import Link from 'next/link';
import { TableProps } from 'antd';
import * as XLSX from 'xlsx'; // 用于Excel解析

const { Title, Text, Paragraph } = Typography;

// 原始员工数据接口 (从API获取)
interface Employee {
  id: number;
  wechat_nickname: string;
  real_name: string;
  position: string;
  name_abbreviation: string;
  created_at: string;
  updated_at: string;
}

// 扩展后的员工数据接口 (用于UI展示)
interface EmployeeStat extends Employee {
  avatar: string; // 头像URL
  load_index: number; // 总负荷指数
  avg_iteration: number; // 平均迭代
  projects: string[]; // 参与项目名称列表
}

// 员工表单数据接口
interface EmployeeFormData {
  wechat_nickname: string;
  real_name: string;
  position: string;
  name_abbreviation: string;
}

// --- 新增：恢复未匹配人员和项目的数据结构 ---
// 未匹配人员类型
interface UnmatchedPerson {
  id: number;
  sender_name: string;
  group_name: string;
  role: string;
  remark: string | null;
  created_at: string;
  updated_at: string;
};

// 项目数据接口
interface Project {
  id: number;
  project_name: string;
}

// 常用角色标签
const ROLE_OPTIONS = [
  '员工', '项目经理', '客户', '老板', '行政', '客户策划', '客户营销', '客户总监', '客户助理', '其他'
];

// --- 新增：恢复智能推荐的辅助函数 ---
/**
 * 智能推荐角色函数
 */
function getRecommendedRoles(person: UnmatchedPerson | null, employees: Employee[]): string[] {
  if (!person) return [];
  const { group_name, sender_name } = person;
  const groupBased: string[] = [];
  if (group_name.includes('客户')) groupBased.push('客户');
  if (group_name.includes('老板')) groupBased.push('老板');
  // ... 其他基于群名的角色推断
  const matched = employees.filter(e => e.wechat_nickname === sender_name);
  if (matched.length > 0) {
    const freq: Record<string, number> = {};
    matched.forEach(e => { freq[e.position] = (freq[e.position] || 0) + 1; });
    const sorted = Object.entries(freq).sort((a, b) => b[1] - a[1]);
    if (sorted.length > 0) groupBased.unshift(sorted[0][0]);
  }
  if (groupBased.length === 0) groupBased.push('员工');
  return Array.from(new Set(groupBased));
}

/**
 * 智能推荐项目函数
 */
function getRecommendedProject(person: UnmatchedPerson | null, projects: Project[]): Project | null {
    if (!person || !projects || projects.length === 0) return null;
    const { group_name } = person;
    if (!group_name) return null;
    // 简单的模糊匹配
    return projects.find(p => group_name.includes(p.project_name)) || null;
}

// 这是一个模拟函数，用于生成随机头像
const getRandomAvatar = (name: string) => {
  // 使用一个简单的哈希算法将名字转换为一个数字，用于选择一个固定的头像
  const hash = name.split('').reduce((acc, char) => char.charCodeAt(0) + ((acc << 5) - acc), 0);
  const avatarId = Math.abs(hash % 70); // 假设有70个头像
  return `https://i.pravatar.cc/150?img=${avatarId}`;
};

// 新增：定义 EmployeeRow 类型
interface EmployeeRow {
  [key: string]: string | number | null | undefined;
}

// 页面主组件
function EmployeesPage() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [employeeStats, setEmployeeStats] = useState<EmployeeStat[]>([]);
  const [filteredEmployeeStats, setFilteredEmployeeStats] = useState<EmployeeStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<Employee | null>(null);
  const [form] = Form.useForm();
  const [unmatchedPersons, setUnmatchedPersons] = useState<UnmatchedPerson[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [unmatchedModal, setUnmatchedModal] = useState<{visible: boolean, person: UnmatchedPerson | null}>({visible: false, person: null});
  const [unmatchedForm] = Form.useForm();
  const [unmatchedLoading, setUnmatchedLoading] = useState(true);
  const [unmatchedListModalVisible, setUnmatchedListModalVisible] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [importModalVisible, setImportModalVisible] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<EmployeeRow[] | null>(null);
  const [importedRows, setImportedRows] = useState<EmployeeRow[]>([]); // 解析后的表格数据
  const [importStep, setImportStep] = useState<'select'|'preview'|'result'>('select');

  // --- 数据获取与处理 ---

  // 获取所有需要的数据
  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // --- 真实的API调用 ---
      // 并行获取员工列表和未匹配人员列表
      const [employeeRes, unmatchedRes, projectsRes] = await Promise.all([
        employeeAPI.getEmployees(),
        unmatchedAPI.getUnmatchedPersons(),
        projectAPI.getProjects()
      ]);

      let processedEmployees: EmployeeStat[] = [];
      if (employeeRes.success && Array.isArray(employeeRes.data)) {
        setEmployees(employeeRes.data);
        // 只用API返回的数据，不再模拟负荷指数、平均迭代、项目等
        processedEmployees = employeeRes.data.map(emp => ({
          ...emp,
          avatar: getRandomAvatar(emp.real_name),
          load_index: emp.load_index || 0,
          avg_iteration: emp.avg_iteration || 0,
          projects: emp.projects || [],
        }));
        setEmployeeStats(processedEmployees);
        setFilteredEmployeeStats(processedEmployees);
      } else {
        setError(employeeRes.error || '获取员工列表失败');
        message.error('获取员工列表失败');
      }

      if (unmatchedRes.success && Array.isArray(unmatchedRes.data)) {
        setUnmatchedPersons(unmatchedRes.data);
      } else {
        setUnmatchedPersons([]);
        if(unmatchedRes.error) message.error('获取未匹配人员列表失败');
      }

      if (projectsRes.success && Array.isArray(projectsRes.data)) {
        setProjects(projectsRes.data);
      } else {
        setProjects([]);
         if(projectsRes.error) message.error('获取项目列表失败');
      }

    } catch (err) {
      console.error('数据获取失败:', err);
      setError('网络请求失败，请稍后重试');
      message.error('网络请求失败');
    } finally {
      setLoading(false);
      setUnmatchedLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);
  
  // --- 搜索与过滤 ---
  useEffect(() => {
    const results = employeeStats.filter(emp =>
      emp.real_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      emp.position.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredEmployeeStats(results);
  }, [searchTerm, employeeStats]);


  // --- 核心指标计算 (使用 useMemo 进行性能优化) ---
  const highLoadEmployeesCount = useMemo(() => {
    const HIGH_LOAD_THRESHOLD = 15.0;
    return employeeStats.filter(e => e.load_index > HIGH_LOAD_THRESHOLD).length;
  }, [employeeStats]);

  const coreContributorsCount = useMemo(() => {
    // 按负荷指数降序排序，取前20%
    const sorted = [...employeeStats].sort((a, b) => b.load_index - a.load_index);
    const top20PercentIndex = Math.ceil(sorted.length * 0.2);
    return top20PercentIndex;
  }, [employeeStats]);


  // --- 表格列定义 ---
  const employeeColumns: TableProps<EmployeeStat>['columns'] = [
    {
      title: '员工',
      dataIndex: 'real_name',
      key: 'employee',
      width: 180,
      fixed: 'left',
      render: (_, record) => (
        <Space>
          <Avatar src={record.avatar} icon={<UserOutlined />} />
          <Text strong>{record.real_name}</Text>
        </Space>
      ),
    },
    {
      title: '岗位',
      dataIndex: 'position',
      key: 'position',
      width: 120,
    },
    {
      title: (
        <Space>
          总负荷指数
          <Tooltip title="综合评估员工在所有项目中的工作饱和度、沟通频次和文件交付量。">
            <QuestionCircleOutlined style={{ color: 'rgba(0,0,0,.45)' }} />
          </Tooltip>
        </Space>
      ),
      dataIndex: 'load_index',
      key: 'load_index',
      width: 120,
      sorter: (a: EmployeeStat, b: EmployeeStat) => a.load_index - b.load_index,
      render: (load_index: number) => (
        <Text style={{ color: load_index > 15.0 ? '#f5222d' : '#3f8600', fontWeight: 'bold' }}>
          {load_index}
        </Text>
      ),
    },
    {
      title: '参与项目',
      dataIndex: 'projects',
      key: 'projects',
      render: (projects: string[]) => (
        <>
          {projects.map(project => (
            <Tag color="blue" key={project} style={{ margin: '2px' }}>
              {project}
            </Tag>
          ))}
        </>
      ),
    },
    {
      title: (
        <Space>
          平均迭代
          <Tooltip title="员工在项目中交付文件的平均版本次数，反映其工作的细致和迭代程度。">
            <QuestionCircleOutlined style={{ color: 'rgba(0,0,0,.45)' }} />
          </Tooltip>
        </Space>
      ),
      dataIndex: 'avg_iteration',
      key: 'avg_iteration',
      width: 120,
      sorter: (a: EmployeeStat, b: EmployeeStat) => a.avg_iteration - b.avg_iteration,
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space size="middle">
          <Link href={`/employees/${record.id}`}>
            <Button type="link">详情</Button>
          </Link>
          <Button type="link" onClick={() => handleEdit(record)}>编辑</Button>
          <Popconfirm
            title={`确定删除员工 ${record.real_name} 吗?`}
            onConfirm={() => handleDeleteEmployee(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // --- 新增：恢复未匹配人员表格列定义 ---
  const unmatchedColumns: TableProps<UnmatchedPerson>['columns'] = [
    {
      title: '发言人昵称',
      dataIndex: 'sender_name',
      key: 'sender_name',
    },
    {
      title: '所在群聊',
      dataIndex: 'group_name',
      key: 'group_name',
    },
    {
      title: '当前角色',
      dataIndex: 'role',
      key: 'role',
      render: (text: string) => <Text type={text === '未知' ? 'danger' : 'success'}>{text as 'danger' | 'success'}</Text>
    },
    {
        title: '备注',
        dataIndex: 'remark',
        key: 'remark'
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button type="primary" onClick={() => handleAssignRole(record)}>
          分配角色
        </Button>
      ),
    },
  ];


  // --- CRUD (增删改) 逻辑 (沿用旧逻辑) ---
  const handleAddEmployee = async (values: EmployeeFormData) => {
    try {
      const response = await employeeAPI.addEmployee(values);
      if (response.success) {
        message.success('员工添加成功');
        setModalVisible(false);
        form.resetFields();
        fetchData(); // 重新获取所有数据
      } else {
        message.error(response.error || '添加员工失败');
      }
    } catch (err) {
      console.error('添加员工失败:', err);
      message.error('添加员工失败');
    }
  };

  const handleUpdateEmployee = async (values: EmployeeFormData) => {
    if (!editingEmployee) return;
    try {
      const response = await employeeAPI.updateEmployee(editingEmployee.id, values);
      if (response.success) {
        message.success('员工更新成功');
        setModalVisible(false);
        form.resetFields();
        setEditingEmployee(null);
        fetchData(); // 重新获取所有数据
      } else {
        message.error(response.error || '更新员工失败');
      }
    } catch (err) {
      console.error('更新员工失败:', err);
      message.error('更新员工失败');
    }
  };

  const handleDeleteEmployee = async (id: number) => {
    try {
      const response = await employeeAPI.deleteEmployee(id);
      if (response.success) {
        message.success('员工删除成功');
        fetchData(); // 重新获取所有数据
      } else {
        message.error(response.error || '删除员工失败');
      }
    } catch (err) {
      console.error('删除员工失败:', err);
      message.error('删除员工失败');
    }
  };

  // --- 模态框控制 ---
  const handleEdit = (record: Employee) => {
    setEditingEmployee(record);
    form.setFieldsValue(record);
    setModalVisible(true);
  };

  const handleAdd = () => {
    setEditingEmployee(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleCancel = () => {
    setModalVisible(false);
    setEditingEmployee(null);
    form.resetFields();
  };

  const handleSubmit = () => {
    form.validateFields().then(values => {
      if (editingEmployee) {
        handleUpdateEmployee(values as EmployeeFormData);
      } else {
        handleAddEmployee(values as EmployeeFormData);
      }
    });
  };

  // --- 新增：未匹配人员列表弹窗控制 ---
  const showUnmatchedListModal = () => {
    setUnmatchedListModalVisible(true);
  };

  const handleUnmatchedListModalCancel = () => {
    setUnmatchedListModalVisible(false);
  };

  // --- 新增：恢复未匹配人员处理逻辑 ---
  const handleAssignRole = (person: UnmatchedPerson) => {
    const recommendedRoles = getRecommendedRoles(person, employees);
    const recommendedProject = getRecommendedProject(person, projects);
    unmatchedForm.setFieldsValue({
        role: recommendedRoles.length > 0 ? recommendedRoles[0] : '员工',
        project_id: recommendedProject?.id,
        wechat_nickname: person.sender_name,
        remark: person.remark,
    });
    setUnmatchedModal({ visible: true, person });
  };

  const handleUnmatchedModalCancel = () => {
    setUnmatchedModal({ visible: false, person: null });
    unmatchedForm.resetFields();
  };

  const handleUnmatchedModalSubmit = () => {
    unmatchedForm.validateFields().then(async values => {
        if (!unmatchedModal.person) return;

        const { real_name, position, name_abbreviation, project_id, remark } = values;
        
        // 步骤1: 创建新员工
        const addEmployeeRes = await employeeAPI.addEmployee({
            real_name,
            position,
            name_abbreviation,
            wechat_nickname: unmatchedModal.person.sender_name,
        });

        if (!addEmployeeRes.success) {
            message.error('创建新员工失败: ' + addEmployeeRes.error);
            return;
        }
        message.success('新员工创建成功！');

        // 步骤2: 更新未匹配人员记录（标记为已处理）
        const updateUnmatchedRes = await unmatchedAPI.updateUnmatchedPerson(unmatchedModal.person.id, {
            role: position,
            remark: `已分配为员工: ${real_name}，归属项目ID: ${project_id}。` + (remark || ''),
        });

        if (updateUnmatchedRes.success) {
            message.success('未匹配人员状态更新成功！');
        } else {
            message.warning('未匹配人员状态更新失败: ' + updateUnmatchedRes.error);
        }
        
        // 刷新所有数据
        fetchData();
        handleUnmatchedModalCancel();
    });
  };

  // 新增：批量导入按钮点击事件
  const handleOpenImportModal = () => {
    setImportModalVisible(true);
    setImportResult(null);
    setImportedRows([]);
  };
  // 新增：关闭批量导入弹窗
  const handleCloseImportModal = () => {
    setImportModalVisible(false);
    setImportResult(null);
    setImportedRows([]);
  };

  // 处理文件上传
  const handleFileUpload = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const data = new Uint8Array(e.target?.result as ArrayBuffer);
      const workbook = XLSX.read(data, { type: 'array' });
      const sheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[sheetName];
      const jsonData = XLSX.utils.sheet_to_json(worksheet, { defval: '' });
      setImportedRows(jsonData as EmployeeRow[]);
      setImportStep('preview');
    };
    reader.readAsArrayBuffer(file);
    return false; // 阻止Upload自动上传
  };

  // 处理表格粘贴
  const handlePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    const text = e.clipboardData.getData('text');
    // 按行分割
    const rows = text.split(/\r?\n/).filter(row => row.trim() !== '');
    // 按制表符或逗号分割
    const data = rows.map(row => row.split(/\t|,/));
    // 第一行为表头
    const headers = data[0];
    const jsonData = data.slice(1).map(row => {
      const obj: EmployeeRow = {};
      headers.forEach((h, i) => {
        obj[h.trim()] = row[i] ? row[i].trim() : '';
      });
      return obj;
    });
    setImportedRows(jsonData);
    setImportStep('preview');
  };

  // --- 新增：确认导入逻辑 ---
  const handleImportConfirm = async (rows: EmployeeRow[]) => {
    if (!rows || rows.length === 0) {
      message.error('没有可导入的数据');
      return;
    }
    setImporting(true);
    try {
      // 字段映射：英文表头转为后端要求的中文表头
      const fieldMap: Record<string, string> = {
        wechat_nickname: '微信昵称',
        real_name: '真实姓名',
        position: '岗位',
        name_abbr: '姓名缩写',
        name_abbreviation: '姓名缩写', // 兼容部分导入
      };
      const mappedRows = rows.map((row: EmployeeRow) => {
        const newRow: Record<string, string> = {};
        Object.keys(fieldMap).forEach(key => {
          if (row[key] !== undefined) {
            newRow[fieldMap[key]] = String(row[key] ?? '');
          }
        });
        // 保证所有字段都存在
        Object.values(fieldMap).forEach(cnKey => {
          if (!newRow[cnKey]) newRow[cnKey] = '';
        });
        return newRow;
      });
      // 发送POST请求到后端批量导入API
      const res = await fetch('/api/v1/employees/batch-import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rows: mappedRows }),
      });
      const result = await res.json();
      if (result.success) {
        message.success('导入成功');
        setImportResult(result.results || []);
        setImportStep('result');
        fetchData(); // 刷新员工列表
      } else {
        message.error(result.error || '导入失败');
      }
    } catch {
      message.error('网络错误');
    }
    setImporting(false);
  };

  // --- 渲染 ---
  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" tip="正在加载员工数据..." />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="加载失败"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" type="primary" onClick={fetchData}>
              点击重试
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div>
      <Title level={2}>员工视图</Title>
      <Paragraph type="secondary">在此视图中，您可以全面了解团队成员的工作负荷、核心贡献及参与的项目情况。</Paragraph>
      
      {/* 顶部操作区 */}
      <Card style={{ marginBottom: 24 }}>
         <Row justify="space-between" align="middle">
            <Col xs={24} sm={12} md={10} lg={8}>
              <Input
                  prefix={<SearchOutlined />}
                  placeholder="搜索员工姓名、岗位..."
                  onChange={e => setSearchTerm(e.target.value)}
                  style={{ width: '100%' }}
                  allowClear
              />
            </Col>
            <Col>
              <Space>
                <Button icon={<ReloadOutlined />} onClick={fetchData}>刷新</Button>
                <Button type="default" onClick={handleOpenImportModal}>
                  批量导入
                </Button>
                <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
                  添加员工
                </Button>
              </Space>
            </Col>
         </Row>
      </Card>
      
      {/* 核心指标统计 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="员工总数" value={employeeStats.length} prefix={<UserOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="高负荷员工"
              value={highLoadEmployeesCount}
              valueStyle={{ color: '#cf1322' }}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="核心贡献者 (Top 20%)"
              value={coreContributorsCount}
              valueStyle={{ color: '#3f8600' }}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card hoverable onClick={showUnmatchedListModal}>
             <Statistic
                title="待分配人员"
                value={unmatchedPersons.length}
                valueStyle={{ color: '#faad14' }}
                prefix={<UserOutlined />}
              />
          </Card>
        </Col>
      </Row>

      {/* 员工列表 */}
      <Card>
        <Table
          columns={employeeColumns}
          dataSource={filteredEmployeeStats}
          rowKey="id"
          scroll={{ x: 1200 }}
          rowClassName={(record: EmployeeStat) => {
            return record.load_index > 15.0 ? 'high-load-row' : '';
          }}
          pagination={false}
        />
      </Card>

      {/* --- 修改：将未匹配人员列表移入新弹窗 --- */}
      <Modal
        title="未匹配人员 (需人工分配角色)"
        open={unmatchedListModalVisible}
        onCancel={handleUnmatchedListModalCancel}
        footer={[
            <Button key="close" onClick={handleUnmatchedListModalCancel}>
                关闭
            </Button>
        ]}
        width={1000}
      >
          <Paragraph type="secondary" style={{ marginBottom: 24 }}>
              以下是在聊天记录中出现，但尚未在系统中创建档案的用户。请为他们分配角色和项目，以确保数据统计的完整性。
          </Paragraph>
          <Table
            columns={unmatchedColumns}
            dataSource={unmatchedPersons}
            rowKey="id"
            loading={unmatchedLoading}
            pagination={{ pageSize: 5 }}
           />
      </Modal>

      {/* 添加/编辑员工模态框 */}
      <Modal
        title={editingEmployee ? '编辑员工' : '添加新员工'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={handleCancel}
        confirmLoading={loading}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" name="employee_form">
          <Form.Item
            name="real_name"
            label="真实姓名"
            rules={[{ required: true, message: '请输入员工的真实姓名' }]}
          >
            <Input placeholder="例如：张三" />
          </Form.Item>
          <Form.Item
            name="wechat_nickname"
            label="微信昵称"
            rules={[{ required: true, message: '请输入员工的微信昵称' }]}
          >
            <Input placeholder="员工在工作群中使用的昵称" />
          </Form.Item>
          <Form.Item
            name="position"
            label="岗位"
            rules={[{ required: true, message: '请输入员工的岗位' }]}
          >
            <Input placeholder="例如：设计、文案、项目经理" />
          </Form.Item>
          <Form.Item
            name="name_abbreviation"
            label="姓名缩写"
            rules={[{ required: true, message: '请输入员工的姓名缩写' }]}
          >
            <Input placeholder="用于文件命名，例如：zs" />
          </Form.Item>
        </Form>
      </Modal>

      {/* --- 新增：恢复分配角色模态框 --- */}
       <Modal
        title={`为 "${unmatchedModal.person?.sender_name}" 分配角色`}
        open={unmatchedModal.visible}
        onOk={handleUnmatchedModalSubmit}
        onCancel={handleUnmatchedModalCancel}
        width={600}
        okText="创建并分配"
        cancelText="取消"
        destroyOnClose
      >
        <Form form={unmatchedForm} layout="vertical" name="unmatched_form">
           <Alert
            message="智能识别与分配"
            description="系统将根据您填写的信息，自动创建一个新的员工档案，并将此用户标记为已分配。"
            type="info"
            showIcon
            style={{ marginBottom: 24 }}
           />
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="real_name"
                label="真实姓名"
                rules={[{ required: true, message: '必须为新员工指定真实姓名' }]}
              >
                <Input placeholder="例如：李四" />
              </Form.Item>
            </Col>
            <Col span={12}>
                <Form.Item
                    name="wechat_nickname"
                    label="微信昵称 (自动填充)"
                >
                    <Input readOnly />
                </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
                <Form.Item
                    name="position"
                    label="岗位"
                    rules={[{ required: true, message: '必须为新员工指定岗位' }]}
                >
                    <Select
                        showSearch
                        placeholder="选择或输入岗位"
                        options={ROLE_OPTIONS.map(r => ({label: r, value: r}))}
                    />
                </Form.Item>
            </Col>
            <Col span={12}>
                 <Form.Item
                    name="name_abbreviation"
                    label="姓名缩写"
                    rules={[{ required: true, message: '必须输入姓名缩写 (用于文件名)' }]}
                 >
                    <Input placeholder="例如：ls" />
                </Form.Item>
            </Col>
          </Row>
           <Form.Item
                name="project_id"
                label="归属项目 (可选)"
                extra="系统会根据群聊名称自动推荐"
            >
                <Select
                    allowClear
                    showSearch
                    placeholder="选择一个项目"
                    options={projects.map(p => ({label: p.project_name, value: p.id}))}
                    optionFilterProp="label"
                />
            </Form.Item>
            <Form.Item
                name="remark"
                label="备注 (可选)"
            >
                <Input.TextArea rows={2} placeholder="可填写更多备注信息" />
            </Form.Item>
        </Form>
      </Modal>

      {/* 新增：批量导入弹窗 */}
      <Modal
        title="批量导入员工"
        open={importModalVisible}
        onCancel={handleCloseImportModal}
        footer={null}
        width={600}
        destroyOnClose
      >
        <Alert
          message="功能说明"
          description="您可以上传Excel/CSV文件，或直接粘贴表格数据，批量导入员工信息。支持字段：微信昵称、真实姓名、岗位、姓名缩写。"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        {/* 文件上传区 */}
        {importStep === 'select' && (
          <div style={{ marginBottom: 16 }}>
            <Upload
              accept=".xlsx,.xls,.csv"
              showUploadList={false}
              beforeUpload={handleFileUpload}
            >
              <Button type="primary">选择Excel/CSV文件上传</Button>
            </Upload>
            <div style={{ margin: '16px 0', color: '#888' }}>或</div>
            <textarea
              style={{ width: '100%', minHeight: 80, resize: 'vertical', padding: 8, borderColor: '#d9d9d9' }}
              placeholder="可直接粘贴表格（如从Excel复制）"
              onPaste={handlePaste}
            />
            <div style={{ marginTop: 16, textAlign: 'right' }}>
              <Button onClick={handleCloseImportModal}>取消</Button>
            </div>
          </div>
        )}
        {/* 预览区 */}
        {importStep === 'preview' && (
          <div>
            <Alert message="请确认导入数据" type="info" showIcon style={{ marginBottom: 8 }} />
            <div style={{ maxHeight: 240, overflow: 'auto', border: '1px solid #eee', marginBottom: 16 }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    {importedRows.length > 0 && Object.keys(importedRows[0]).map(key => (
                      <th key={key} style={{ border: '1px solid #eee', padding: 4, background: '#fafafa' }}>{key}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {importedRows.map((row, idx) => (
                    <tr key={idx}>
                      {Object.values(row).map((val, i) => (
                        <td key={i} style={{ border: '1px solid #eee', padding: 4 }}>{String(val)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Space>
              <Button onClick={() => setImportStep('select')}>返回</Button>
              <Button type="primary" onClick={() => handleImportConfirm(importedRows)} loading={importing}>
                确认导入
              </Button>
            </Space>
          </div>
        )}
        {/* 导入结果区 */}
        {importStep === 'result' && (
          <div>
            <Alert message="导入结果" type="success" showIcon style={{ marginBottom: 8 }} />
            <div style={{ maxHeight: 240, overflow: 'auto', border: '1px solid #eee', marginBottom: 16 }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th>微信昵称</th>
                    <th>状态</th>
                    <th>原因</th>
                  </tr>
                </thead>
                <tbody>
                  {importResult && (importResult as Record<string, string>[]).map((row, idx: number) => (
                    <tr key={idx}>
                      <td>{row['微信昵称']}</td>
                      <td>{row['状态']}</td>
                      <td>{row['原因'] || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ textAlign: 'right' }}>
              <Button type="primary" onClick={handleCloseImportModal}>关闭</Button>
            </div>
          </div>
        )}
      </Modal>

      {/* 全局样式，用于高亮行 */}
      <style jsx global>{`
        .high-load-row td {
          background: #fff1f0 !important;
        }
      `}</style>
    </div>
  );
}

export default EmployeesPage;