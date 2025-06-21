// 项目页面
// 该页面用于管理项目信息，包括项目的增删改查、群聊配置、数据同步等功能

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Card, 
  List, 
  Button, 
  Modal, 
  Form, 
  Input, 
  Select, 
  Space, 
  Typography, 
  Spin, 
  Alert, 
  message, 
  Popconfirm, 
  Tooltip, 
  Tag, 
  Statistic, 
  Row, 
  Col,
  DatePicker,
  Divider,
  Descriptions,
  Badge,
  notification,
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  SyncOutlined, 
  EyeOutlined, 
  ReloadOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  CloseOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { projectAPI, syncAPI, chatlogAPI } from '../../lib/api';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

// 项目数据接口
interface Project {
  id: number;
  project_name: string;
  description: string;
  status: string;
  internal_chat_groups?: string[];
  external_chat_groups?: string[];
  created_at: string;
  updated_at: string;
  health_status?: 'good' | 'warning' | 'danger';
  negative_keywords_count?: number;
  total_files?: number;
  rework_rate?: number; // 返工率
}

// 员工接口 (新增)
interface Employee {
  id: number;
  name: string;
}

// 项目表单数据接口
interface ProjectFormData {
  project_name: string;
  project_short_name: string;
  description: string;
  internal_chat_groups?: string[];
  external_chat_groups?: string[];
  employee_ids?: number[];
}

// 群聊接口
interface Chatroom {
  id: string;
  name: string;
  member_count?: number;
  created_at?: string;
}

// 同步状态接口
interface SyncStatus {
  status: string;
  message: string;
  timestamp: string;
  api_base: string;
}

// 同步结果接口
interface SyncResult {
  project_id?: number;
  project_name?: string;
  start_date: string;
  end_date: string;
  sync_type: string;
  total_chatrooms: number;
  success_count: number;
  failed_count: number;
  total_messages: number;
  total_files: number;
  details: Array<{
    chatroom_name: string;
    message_count?: number;
    status: string;
    error?: string;
    first_message_time?: string;
    last_message_time?: string;
  }>;
  timestamp: string;
}

// 计算项目健康状态
const calculateHealthStatus = (project: Project): 'good' | 'warning' | 'danger' => {
  if (project.negative_keywords_count && project.negative_keywords_count > 10) {
    return 'danger';
  } else if (project.negative_keywords_count && project.negative_keywords_count > 5) {
    return 'warning';
  }
  return 'good';
};

// 获取健康状态配置
const getHealthStatusConfig = (status: 'good' | 'warning' | 'danger') => {
  const configs = {
    good: { color: '#52c41a', icon: <CheckCircleOutlined />, text: '健康' },
    warning: { color: '#faad14', icon: <ExclamationCircleOutlined />, text: '注意' },
    danger: { color: '#ff4d4f', icon: <CloseCircleOutlined />, text: '异常' }
  };
  return configs[status];
};

// 获取群聊列表
const fetchChatGroups = async (): Promise<string[]> => {
  try {
    const response = await syncAPI.getChatrooms();
    if (response.success && response.data) {
      return response.data.map((room: Chatroom) => room.name);
    }
    return [];
  } catch (error) {
    console.error('获取群聊列表失败:', error);
    return [];
  }
};

function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [form] = Form.useForm();
  const [chatGroups, setChatGroups] = useState<string[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);

  // 新增状态：用于搜索、过滤和排序
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all'); // all, good, warning, danger
  const [sortOrder, setSortOrder] = useState('health'); // health, name, activity

  // 同步项目ID状态
  const [syncingProjectId, setSyncingProjectId] = useState<number | null>(null);

  // 获取项目列表
  const fetchProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await projectAPI.getProjects();
      if (response.success && response.data) {
        const projectsWithMockData = response.data.map((project: Project) => ({
          ...project,
          health_status: calculateHealthStatus(project),
          rework_rate: Math.floor(Math.random() * 25), // 模拟返工率数据
          total_files: project.total_files || Math.floor(Math.random() * 200) + 20, // 模拟文件总数
          negative_keywords_count: project.negative_keywords_count || Math.floor(Math.random() * 40), // 模拟负面关键词
        }));
        setProjects(projectsWithMockData);
      } else {
        setError(response.error || '获取项目列表失败');
      }
    } catch (err) {
      console.error('获取项目列表失败:', err);
      setError('获取项目列表失败，请检查网络连接');
    } finally {
      setLoading(false);
    }
  };

  // 获取员工列表 (新增)
  const fetchEmployees = async () => {
    // 实际项目中,这里会调用API
    // const response = await employeeAPI.getEmployees();
    // if (response.success) setEmployees(response.data);
    setEmployees([
      { id: 1, name: '张三' },
      { id: 2, name: '李四' },
      { id: 3, name: '王五' },
      { id: 4, name: '赵六' },
      { id: 5, name: '孙七' },
    ]);
  };

  // Memoized: 过滤和排序项目列表
  const filteredAndSortedProjects = React.useMemo(() => {
    // 根据用户要求，主列表只展示 "执行中" (active) 的项目
    let result = projects.filter(p => p.status === 'active');

    // 根据搜索词过滤
    if (searchQuery) {
      result = result.filter(p => p.project_name.toLowerCase().includes(searchQuery.toLowerCase()));
    }

    // 根据健康状态过滤
    if (statusFilter !== 'all') {
      result = result.filter(p => p.health_status === statusFilter);
    }
    
    // 排序
    result.sort((a, b) => {
      switch (sortOrder) {
        case 'name':
          return a.project_name.localeCompare(b.project_name);
        case 'activity':
          // 按最近更新时间排序
          return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
        case 'health':
        default:
          const healthOrder = { 'good': 1, 'warning': 2, 'danger': 3 };
          return (healthOrder[a.health_status!] || 4) - (healthOrder[b.health_status!] || 4);
      }
    });

    return result;
  }, [projects, searchQuery, statusFilter, sortOrder]);

  // 添加项目
  const handleAddProject = async (values: ProjectFormData) => {
    try {
      const response = await projectAPI.addProject(values);
      if (response.success) {
        message.success('项目添加成功');
        setModalVisible(false);
        form.resetFields();
        fetchProjects();
      } else {
        message.error(response.error || '项目添加失败');
      }
    } catch (error) {
      console.error('添加项目失败:', error);
      message.error('添加项目失败');
    }
  };

  // 更新项目
  const handleUpdateProject = async (values: ProjectFormData) => {
    if (!editingProject) return;
    try {
      const response = await projectAPI.updateProject(editingProject.id, values);
      if (response.success) {
        message.success('项目更新成功');
        setModalVisible(false);
        setEditingProject(null);
        form.resetFields();
        fetchProjects();
      } else {
        message.error(response.error || '项目更新失败');
      }
    } catch (error) {
      console.error('更新项目失败:', error);
      message.error('更新项目失败');
    }
  };

  // 删除项目
  const handleDeleteProject = async (id: number) => {
    try {
      const response = await projectAPI.deleteProject(id);
      if (response.success) {
        message.success('项目已成功删除');
        fetchProjects();
      } else {
        message.error(response.error || '项目删除失败');
      }
    } catch (error) {
      console.error('删除项目失败:', error);
      message.error('删除项目失败');
    }
  };

  // 显示删除确认 (新增)
  const showDeleteConfirm = (project: Project) => {
    Modal.confirm({
      title: '您确定要删除吗？',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p>正在删除项目「{project.project_name}」。此操作将会永久删除该项目及其所有关联的统计数据、文件和聊天记录。</p>
          <Typography.Text strong style={{ color: '#ff4d4f' }}>
            此操作无法撤销。
          </Typography.Text>
        </div>
      ),
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      onOk() {
        return handleDeleteProject(project.id);
      },
    });
  };

  // 编辑项目
  const handleEdit = (record: Project) => {
    setEditingProject(record);
    form.setFieldsValue({
      ...record,
      // 如果有关联员工ID, 也需要在这里设置
    });
    setModalVisible(true);
  };

  // 添加项目
  const handleAdd = () => {
    setEditingProject(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 取消操作
  const handleCancel = () => {
    setModalVisible(false);
    setEditingProject(null);
    form.resetFields();
  };

  // 提交表单
  const handleSubmit = () => {
    form.validateFields().then((values) => {
      const processedValues = {
        ...values,
        internal_chat_groups: values.internal_chat_groups || [],
        external_chat_groups: values.external_chat_groups || []
      };

      if (editingProject) {
        handleUpdateProject(processedValues);
      } else {
        handleAddProject(processedValues);
      }
    });
  };

  // 同步数据 (重构)
  const handleSyncData = async (project: Project) => {
    setSyncingProjectId(project.id);
    // 快速同步默认使用最近7天的数据
    const syncRequest = {
      start_date: dayjs().subtract(7, 'day').format('YYYY-MM-DD'),
      end_date: dayjs().format('YYYY-MM-DD'),
      sync_type: 'all',
      chatroom_names: [],
    };
    try {
      const response = await syncAPI.syncProject(project.id, syncRequest);
      if (response.success && response.data && response.data.results) {
        const { total_messages, total_files } = response.data.results;
        notification.success({
          message: '同步成功',
          description: `项目「${project.project_name}」数据已更新。新增聊天记录 ${total_messages} 条，新识别文件 ${total_files} 个。`,
          placement: 'topRight',
        });
        fetchProjects(); // 重新获取数据以更新卡片信息
      } else {
        notification.error({
          message: '同步失败',
          description: response.error || '无法连接到聊天记录服务器，请检查服务状态或稍后重试。',
          placement: 'topRight',
          duration: 0, // 永久显示直到用户关闭
        });
      }
    } catch (error) {
      console.error('同步失败:', error);
      notification.error({
        message: '同步失败',
        description: '发生未知错误，请联系技术支持。',
        placement: 'topRight',
        duration: 0,
      });
    } finally {
      setSyncingProjectId(null);
    }
  };

  // 查看项目详情 (重构)
  const handleViewDetails = (project: Project) => {
    router.push(`/projects/${project.id}`);
  };

  // 加载群聊列表
  useEffect(() => {
    fetchChatGroups().then(setChatGroups);
    fetchEmployees();
  }, []);

  // 组件加载时获取数据
  useEffect(() => {
    fetchProjects();
  }, []);

  // 加载状态
  if (loading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text>正在加载项目数据...</Text>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      {/* 页面标题和操作按钮 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>项目视图</Title>
        <Space>
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={handleAdd}
          >
            新建项目
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
            <Button size="small" onClick={fetchProjects}>
              重试
            </Button>
          }
        />
      )}

      {/* 项目统计 - 更新为新设计 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="项目总数"
              value={projects.length}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="执行中项目数"
              value={projects.filter(p => p.status === 'active').length}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="已结束项目数"
              value={projects.filter(p => p.status !== 'active').length}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 筛选和排序控件 */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16} justify="space-between" align="middle">
          <Col flex="auto">
            <Input.Search
              placeholder="搜索执行中的项目..."
              onSearch={value => setSearchQuery(value)}
              onChange={e => setSearchQuery(e.target.value)}
              style={{ width: '100%' }}
              allowClear
            />
          </Col>
          <Col>
            <Select value={statusFilter} onChange={setStatusFilter} style={{ width: 160 }}>
              <Option value="all">所有状态</Option>
              <Option value="good">健康 (Green)</Option>
              <Option value="warning">警告 (Yellow)</Option>
              <Option value="danger">风险 (Red)</Option>
            </Select>
          </Col>
          <Col>
            <Select value={sortOrder} onChange={setSortOrder} style={{ width: 160 }}>
              <Option value="health">按健康度排序</Option>
              <Option value="name">按名称排序</Option>
              <Option value="activity">按最近活动排序</Option>
            </Select>
          </Col>
        </Row>
      </Card>

      {/* 项目列表 - 更新为新卡片设计 */}
      {filteredAndSortedProjects.length > 0 ? (
        <List
          grid={{ gutter: 24, xs: 1, sm: 1, md: 2, lg: 3, xl: 3, xxl: 3 }}
          dataSource={filteredAndSortedProjects}
          renderItem={(project) => {
            const healthConfig = getHealthStatusConfig(project.health_status || 'warning');
            return (
              <List.Item>
                <Card
                  hoverable
                  style={{ position: 'relative' }}
                >
                  <Button 
                    shape="circle"
                    icon={<CloseOutlined />}
                    size="small"
                    style={{ position: 'absolute', top: 16, right: 16, border: 'none', background: 'transparent', zIndex: 10 }}
                    onClick={() => showDeleteConfirm(project)}
                  />
                  <Space align="center" style={{ marginBottom: 24 }}>
                    <Badge color={healthConfig.color} />
                    <Title level={4} style={{ margin: 0, flex: 1 }} ellipsis={{ rows: 1, tooltip: project.project_name }}>
                      {project.project_name}
                    </Title>
                  </Space>
                  
                  <Row gutter={16} style={{ marginBottom: 24, textAlign: 'center' }}>
                    <Col span={8}>
                      <Statistic value={project.total_files} title="总文件数" />
                    </Col>
                    <Col span={8}>
                      <Statistic value={project.rework_rate} suffix="%" title="返工率" />
                    </Col>
                    <Col span={8}>
                      <Statistic value={project.negative_keywords_count} title="负面关键词" />
                    </Col>
                  </Row>
                  
                  <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
                    <Button 
                      icon={<SyncOutlined />} 
                      onClick={() => handleSyncData(project)}
                      loading={syncingProjectId === project.id}
                    >
                      {syncingProjectId === project.id ? '同步中...' : '同步数据'}
                    </Button>
                    <Button 
                      type="primary"
                      icon={<EyeOutlined />}
                      onClick={() => handleViewDetails(project)}
                    >
                      查看详情
                    </Button>
                  </Space>
                </Card>
              </List.Item>
            );
          }}
        />
      ) : (
        <Card>
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <InfoCircleOutlined style={{ fontSize: 24, color: '#999', marginBottom: 16 }}/>
            <Text type="secondary">当前筛选条件下没有找到项目</Text>
            <br />
            <Button onClick={() => {
              setSearchQuery('');
              setStatusFilter('all');
            }} style={{ marginTop: 16 }}>
              清空筛选条件
            </Button>
          </div>
        </Card>
      )}

      {/* 项目编辑/添加模态框 (重构) */}
      <Modal
        title={editingProject ? '编辑项目' : '新建项目'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={handleCancel}
        width={600}
        okText={editingProject ? '保存' : '创建项目'}
        cancelText="取消"
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          name="projectForm"
          initialValues={{ 
            project_name: editingProject?.project_name,
            project_short_name: '', // 这里可以根据实际情况填充
            description: editingProject?.description,
            internal_chat_groups: editingProject?.internal_chat_groups || [],
            external_chat_groups: editingProject?.external_chat_groups || [],
            employee_ids: [], // 这里可以根据实际情况填充
          }}
        >
          <Form.Item
            name="project_name"
            label="项目名称"
            rules={[{ required: true, message: '项目名称不能为空' }]}
          >
            <Input placeholder="请输入项目的完整名称" />
          </Form.Item>

          <Form.Item
            name="project_short_name"
            label="项目简称"
            rules={[{ required: true, message: '项目简称不能为空' }]}
            help="*此简称将用于聊天记录的自动匹配, 例如: 输入'良渚', 系统会自动匹配群名为'良渚-设计沟通群'的聊天记录。"
          >
            <Input placeholder="请输入项目简称 (用于内部识别, 建议使用拼音或英文)" />
          </Form.Item>

          <Form.Item
            name="description"
            label="项目描述"
          >
            <Input.TextArea rows={3} placeholder="（选填）请输入项目描述" />
          </Form.Item>

          <Form.Item
            name="internal_chat_groups"
            label="关联内部群聊"
          >
            <Select
              mode="multiple"
              allowClear
              placeholder="搜索或选择内部沟通群"
              options={chatGroups.map(group => ({ label: group, value: group }))}
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
            />
          </Form.Item>

          <Form.Item
            name="external_chat_groups"
            label="关联外部群聊"
          >
            <Select
              mode="multiple"
              allowClear
              placeholder="搜索或选择外部客户群"
              options={chatGroups.map(group => ({ label: group, value: group }))}
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
            />
          </Form.Item>

          <Form.Item
            name="employee_ids"
            label="关联员工"
          >
            <Select
              mode="multiple"
              allowClear
              placeholder="搜索或选择需要参与此项目的员工"
              options={employees.map(emp => ({ label: emp.name, value: emp.id }))}
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default ProjectsPage; 