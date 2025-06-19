// 项目页面
// 该页面用于管理项目信息，包括项目的增删改查、群聊配置、数据同步等功能

'use client';

import React, { useState, useEffect } from 'react';
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
  Badge
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  SyncOutlined, 
  EyeOutlined, 
  BarChartOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined
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
  // 新增字段：健康状态和负面关键词统计
  health_status?: 'good' | 'warning' | 'danger';
  negative_keywords_count?: number;
  total_files?: number;
}

// 项目表单数据接口
interface ProjectFormData {
  project_name: string;
  description: string;
  internal_chat_groups?: string[];
  external_chat_groups?: string[];
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
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [projectStats, setProjectStats] = useState<Record<number, number>>({});
  const [form] = Form.useForm();
  const [chatGroups, setChatGroups] = useState<string[]>([]);

  // 同步相关状态
  const [syncModalVisible, setSyncModalVisible] = useState(false);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [syncForm] = Form.useForm();
  const [syncLoading, setSyncLoading] = useState(false);
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [syncResult, setSyncResult] = useState<SyncResult | null>(null);
  const [syncLog, setSyncLog] = useState<string[]>([]);

  // 获取项目列表
  const fetchProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await projectAPI.getProjects();
      if (response.success && response.data) {
        const projectsWithHealth = response.data.map((project: Project) => ({
          ...project,
          health_status: calculateHealthStatus(project)
        }));
        setProjects(projectsWithHealth);
        await fetchProjectStats(projectsWithHealth);
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

  // 获取项目统计信息
  const fetchProjectStats = async (projectList: Project[]) => {
    try {
      const stats: Record<number, number> = {};
      // 这里可以调用后端API获取每个项目的文件统计
      // 暂时使用模拟数据
      projectList.forEach(project => {
        stats[project.id] = Math.floor(Math.random() * 50) + 10; // 模拟文件数量
      });
      setProjectStats(stats);
    } catch (error) {
      console.error('获取项目统计失败:', error);
    }
  };

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
        message.success('项目删除成功');
        fetchProjects();
      } else {
        message.error(response.error || '项目删除失败');
      }
    } catch (error) {
      console.error('删除项目失败:', error);
      message.error('删除项目失败');
    }
  };

  // 编辑项目
  const handleEdit = (record: Project) => {
    setEditingProject(record);
    form.setFieldsValue({
      project_name: record.project_name,
      description: record.description,
      internal_chat_groups: record.internal_chat_groups,
      external_chat_groups: record.external_chat_groups
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

  // 同步数据
  const handleSyncData = (project: Project) => {
    setCurrentProject(project);
    setSyncModalVisible(true);
    setSyncResult(null);
    setSyncLog([]);
    syncForm.resetFields();
    
    // 设置默认值
    syncForm.setFieldsValue({
      date_range: [dayjs().subtract(7, 'day'), dayjs()],
      sync_type: 'all',
      chatroom_names: []
    });
    
    // 检查同步状态
    checkSyncStatus();
  };

  // 预设时间段选项
  const getPresetDateRanges = () => {
    const now = dayjs();
    const startOfMonth = now.startOf('month');
    const startOfQuarter = now.startOf('quarter' as any);
    
    return [
      {
        label: '最近7天',
        value: 'last7days',
        range: [now.subtract(7, 'day'), now]
      },
      {
        label: '最近30天',
        value: 'last30days',
        range: [now.subtract(30, 'day'), now]
      },
      {
        label: '本月',
        value: 'thisMonth',
        range: [startOfMonth, now]
      },
      {
        label: '上月',
        value: 'lastMonth',
        range: [startOfMonth.subtract(1, 'month'), startOfMonth.subtract(1, 'day')]
      },
      {
        label: '本季度',
        value: 'thisQuarter',
        range: [startOfQuarter, now]
      },
      {
        label: '上个季度',
        value: 'lastQuarter',
        range: [startOfQuarter.subtract(3, 'month'), startOfQuarter.subtract(1, 'day')]
      },
      {
        label: '最近半年',
        value: 'last6months',
        range: [now.subtract(6, 'month'), now]
      },
      {
        label: '最近一年',
        value: 'lastYear',
        range: [now.subtract(1, 'year'), now]
      }
    ];
  };

  // 处理预设时间段选择
  const handlePresetDateChange = (presetValue: string) => {
    const presets = getPresetDateRanges();
    const selectedPreset = presets.find(preset => preset.value === presetValue);
    
    if (selectedPreset) {
      syncForm.setFieldsValue({
        date_range: selectedPreset.range
      });
    }
  };

  // 检查同步状态
  const checkSyncStatus = async () => {
    try {
      // 先检查Chatlog健康
      const chatlogRes = await chatlogAPI.getStatus();
      setSyncStatus({
        status: chatlogRes.success ? 'running' : 'error',
        message: chatlogRes.success ? 'Chatlog服务正常' : (chatlogRes.error || 'Chatlog服务异常'),
        timestamp: new Date().toISOString(),
        api_base: ''
      });
    } catch (error) {
      setSyncStatus({
        status: 'error',
        message: 'Chatlog服务异常',
        timestamp: new Date().toISOString(),
        api_base: ''
      });
      console.error('检查Chatlog健康失败:', error);
    }
  };

  // 执行同步
  const handleExecuteSync = async () => {
    try {
      setSyncLoading(true);
      setSyncLog([]);
      setSyncResult(null);

      const values = await syncForm.validateFields();
      const [startDate, endDate] = values.date_range;
      
      const syncRequest = {
        start_date: startDate.format('YYYY-MM-DD'),
        end_date: endDate.format('YYYY-MM-DD'),
        sync_type: values.sync_type,
        chatroom_names: values.chatroom_names || []
      };

      setSyncLog([`开始同步项目：${currentProject?.project_name}`]);
      setSyncLog(prev => [...prev, `时间范围：${syncRequest.start_date} ~ ${syncRequest.end_date}`]);
      setSyncLog(prev => [...prev, `同步类型：${syncRequest.sync_type}`]);

      const response = await syncAPI.syncProject(currentProject!.id, syncRequest);
      
      if (response.success && response.data) {
        setSyncResult(response.data.results);
        setSyncLog(response.data.log);
        message.success('同步完成！');
      } else {
        setSyncLog(prev => [...prev, `同步失败：${response.error}`]);
        message.error(response.error || '同步失败');
      }
    } catch (error) {
      console.error('同步失败:', error);
      setSyncLog(prev => [...prev, `同步失败：${error}`]);
      message.error('同步失败');
    } finally {
      setSyncLoading(false);
    }
  };

  // 查看项目详情
  const handleViewDetails = (project: Project) => {
    message.info(`查看项目详情：${project.project_name}（功能开发中）`);
    // TODO: 跳转到项目详情页 /projects/[id]
  };

  // 生成报告
  const handleGenerateReport = (project: Project) => {
    message.info(`生成项目报告：${project.project_name}（功能开发中）`);
    // TODO: 生成项目报告功能
  };

  // 加载群聊列表
  useEffect(() => {
    fetchChatGroups().then(setChatGroups);
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
            icon={<ReloadOutlined />} 
            onClick={fetchProjects}
            loading={loading}
          >
            刷新
          </Button>
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={handleAdd}
          >
            添加项目
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

      {/* 项目统计 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="项目总数"
              value={projects.length}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃项目"
              value={projects.filter(p => p.status === 'active').length}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="文件总数"
              value={Object.values(projectStats).reduce((sum, count) => sum + count, 0)}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="健康项目"
              value={projects.filter(p => p.health_status === 'good').length}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 项目列表 */}
      {projects.length > 0 ? (
        <List
          grid={{ gutter: 16, xs: 1, sm: 2, md: 2, lg: 3, xl: 4, xxl: 4 }}
          dataSource={projects}
          renderItem={(project) => {
            const healthConfig = getHealthStatusConfig(project.health_status || 'warning');
            return (
              <List.Item>
                <Card
                  hoverable
                  actions={[
                    <Tooltip title="生成报告">
                      <Button 
                        type="text" 
                        icon={<BarChartOutlined />} 
                        onClick={() => handleGenerateReport(project)}
                      >
                        报告
                      </Button>
                    </Tooltip>,
                    <Tooltip title="查看详情">
                      <Button 
                        type="text" 
                        icon={<EyeOutlined />} 
                        onClick={() => handleViewDetails(project)}
                      >
                        详情
                      </Button>
                    </Tooltip>,
                    <Tooltip title="编辑项目">
                      <Button 
                        type="text" 
                        icon={<EditOutlined />} 
                        onClick={() => handleEdit(project)}
                      >
                        编辑
                      </Button>
                    </Tooltip>,
                    <Tooltip title="同步数据">
                      <Button 
                        type="text" 
                        icon={<SyncOutlined />} 
                        onClick={() => handleSyncData(project)}
                      >
                        同步
                      </Button>
                    </Tooltip>,
                    <Popconfirm
                      title="确定要删除这个项目吗？"
                      description="删除后无法恢复，相关文件将失去项目关联。"
                      onConfirm={() => handleDeleteProject(project.id)}
                      okText="确定"
                      cancelText="取消"
                    >
                      <Tooltip title="删除项目">
                        <Button 
                          type="text" 
                          danger 
                          icon={<DeleteOutlined />}
                        >
                          删除
                        </Button>
                      </Tooltip>
                    </Popconfirm>
                  ]}
                >
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                      <Title level={4} style={{ margin: 0, flex: 1 }}>
                        {project.project_name}
                      </Title>
                      <Badge 
                        status={project.health_status === 'good' ? 'success' : project.health_status === 'warning' ? 'warning' : 'error'} 
                        text={healthConfig.text}
                      />
                    </div>
                    <Paragraph ellipsis={{ rows: 2 }} style={{ margin: 0, color: '#666' }}>
                      {project.description || '暂无描述'}
                    </Paragraph>
                  </div>

                  <div style={{ marginBottom: 16 }}>
                    <Space wrap>
                      <Tag color="blue">{project.status}</Tag>
                      <Tag color="green">{projectStats[project.id] || 0} 个文件</Tag>
                      {project.negative_keywords_count && project.negative_keywords_count > 0 && (
                        <Tag color="red">{project.negative_keywords_count} 个负面关键词</Tag>
                      )}
                    </Space>
                  </div>

                  <div style={{ fontSize: '12px', color: '#999' }}>
                    <div>创建时间：{new Date(project.created_at).toLocaleDateString()}</div>
                    <div>更新时间：{new Date(project.updated_at).toLocaleDateString()}</div>
                  </div>
                </Card>
              </List.Item>
            );
          }}
        />
      ) : (
        <Card>
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Text type="secondary">暂无项目数据</Text>
            <br />
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd} style={{ marginTop: 16 }}>
              添加第一个项目
            </Button>
          </div>
        </Card>
      )}

      {/* 项目编辑/添加模态框 */}
      <Modal
        title={editingProject ? '编辑项目' : '添加项目'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={handleCancel}
        width={600}
        okText="确定"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            internal_chat_groups: [],
            external_chat_groups: []
          }}
        >
          <Form.Item
            name="project_name"
            label="项目名称"
            rules={[{ required: true, message: '请输入项目名称' }]}
          >
            <Input placeholder="请输入项目名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="项目描述"
          >
            <Input.TextArea rows={3} placeholder="请输入项目描述" />
          </Form.Item>

          <Form.Item
            name="internal_chat_groups"
            label="内部群聊"
          >
            <Select
              mode="tags"
              placeholder="选择或输入内部群聊名称"
              options={chatGroups.map(group => ({ label: group, value: group }))}
            />
          </Form.Item>

          <Form.Item
            name="external_chat_groups"
            label="外部群聊"
          >
            <Select
              mode="tags"
              placeholder="选择或输入外部群聊名称"
              options={chatGroups.map(group => ({ label: group, value: group }))}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 同步数据模态框 */}
      <Modal
        title={`同步数据 - ${currentProject?.project_name}`}
        open={syncModalVisible}
        onCancel={() => setSyncModalVisible(false)}
        width={800}
        footer={[
          <Button key="cancel" onClick={() => setSyncModalVisible(false)}>
            关闭
          </Button>,
          <Button 
            key="sync" 
            type="primary" 
            icon={<SyncOutlined />}
            loading={syncLoading}
            onClick={handleExecuteSync}
            disabled={!syncStatus || syncStatus.status !== 'running'}
          >
            开始同步
          </Button>
        ]}
      >
        <div style={{ marginBottom: 24 }}>
          {/* 同步状态 */}
          {syncStatus && (
            <Alert
              message={`Chatlog 服务状态：${syncStatus.status === 'running' ? '正常运行' : '异常'}`}
              description={syncStatus.message}
              type={syncStatus.status === 'running' ? 'success' : 'error'}
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}

          {/* 同步表单 */}
          <Form
            form={syncForm}
            layout="vertical"
            initialValues={{
              date_range: [dayjs().subtract(7, 'day'), dayjs()],
              sync_type: 'all',
              chatroom_names: []
            }}
          >
            {/* 预设时间段选择 */}
            <Form.Item
              label="快速选择时间段"
            >
              <Select
                placeholder="选择预设时间段或自定义"
                onChange={handlePresetDateChange}
                allowClear
                style={{ marginBottom: 8 }}
              >
                {getPresetDateRanges().map(preset => (
                  <Option key={preset.value} value={preset.value}>
                    {preset.label}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              name="date_range"
              label="时间范围"
              rules={[{ required: true, message: '请选择时间范围' }]}
            >
              <RangePicker 
                style={{ width: '100%' }}
                format="YYYY-MM-DD"
                placeholder={['开始日期', '结束日期']}
                showTime={false}
                allowClear={true}
              />
            </Form.Item>

            <Form.Item
              name="sync_type"
              label="同步类型"
            >
              <Select>
                <Option value="all">全部数据</Option>
                <Option value="chat">仅聊天记录</Option>
                <Option value="files">仅文件数据</Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="chatroom_names"
              label="指定群聊（可选）"
            >
              <Select
                mode="multiple"
                placeholder="不选择则同步项目所有群聊"
                options={chatGroups.map(group => ({ label: group, value: group }))}
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                }
                allowClear
              />
            </Form.Item>
          </Form>
        </div>

        {/* 同步结果 */}
        {syncResult && (
          <div style={{ marginBottom: 24 }}>
            <Divider>同步结果</Divider>
            <Descriptions bordered size="small" column={2}>
              <Descriptions.Item label="项目名称">{syncResult.project_name}</Descriptions.Item>
              <Descriptions.Item label="时间范围">{syncResult.start_date} ~ {syncResult.end_date}</Descriptions.Item>
              <Descriptions.Item label="目标群聊">{syncResult.total_chatrooms} 个</Descriptions.Item>
              <Descriptions.Item label="成功群聊">{syncResult.success_count} 个</Descriptions.Item>
              <Descriptions.Item label="失败群聊">{syncResult.failed_count} 个</Descriptions.Item>
              <Descriptions.Item label="总消息数">{syncResult.total_messages} 条</Descriptions.Item>
              <Descriptions.Item label="总文件数">{syncResult.total_files} 个</Descriptions.Item>
              <Descriptions.Item label="同步时间">{new Date(syncResult.timestamp).toLocaleString()}</Descriptions.Item>
            </Descriptions>

            {/* 详细结果 */}
            {syncResult.details.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <Text strong>详细结果：</Text>
                <List
                  size="small"
                  dataSource={syncResult.details}
                  renderItem={(detail) => (
                    <List.Item key={detail.chatroom_name}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                        <Text>{detail.chatroom_name}</Text>
                        <Space>
                          {detail.status === 'success' ? (
                            <>
                              <Tag color="green" icon={<CheckCircleOutlined />}>成功</Tag>
                              <Text type="secondary">{detail.message_count} 条消息</Text>
                            </>
                          ) : (
                            <>
                              <Tag color="red" icon={<CloseCircleOutlined />}>失败</Tag>
                              <Text type="danger">{detail.error}</Text>
                            </>
                          )}
                        </Space>
                      </div>
                    </List.Item>
                  )}
                />
              </div>
            )}
          </div>
        )}

        {/* 同步日志 */}
        {syncLog.length > 0 && (
          <div>
            <Divider>同步日志</Divider>
            <div style={{ 
              maxHeight: 200, 
              overflowY: 'auto', 
              backgroundColor: '#f5f5f5', 
              padding: 12, 
              borderRadius: 4,
              fontFamily: 'monospace',
              fontSize: '12px'
            }}>
              {syncLog.map((log, index) => (
                <div key={index} style={{ marginBottom: 4 }}>
                  <Text type="secondary">[{new Date().toLocaleTimeString()}]</Text> {log}
                </div>
              ))}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

export default ProjectsPage; 