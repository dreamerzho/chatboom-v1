// 项目页面
// 该页面用于管理项目信息，包括项目的增删改查、群聊配置、数据同步等功能

'use client';

import React, { useState, useEffect, useRef } from 'react';
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
  Tooltip, 
  Tag, 
  Statistic, 
  Row, 
  Col,
  DatePicker,
  Badge,
  notification,
  Drawer,
  Descriptions,
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  SyncOutlined, 
  EyeOutlined, 
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  CloseOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { projectAPI, syncAPI, employeeAPI } from '@lib/api';
import dayjs from 'dayjs';
import Link from 'next/link';

const { Title, Text } = Typography;
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
  rework_rate?: number;
  total_messages?: number;
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
  status: 'active' | 'archived'; // 明确添加 status 字段
  internal_chat_groups?: string[];
  external_chat_groups?: string[];
  employee_ids?: number[];
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

// 定义项目详情类型
interface ProjectDetail {
  id: number;
  project_name: string;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
  stats?: {
    total_files?: number;
    total_messages?: number;
    rework_rate?: number;
  };
  health?: {
    health_score?: number;
  };
  keywords?: {
    negative_score?: number;
  };
}

// 新增类型声明
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

interface EmployeeMapping {
  id: number;
  real_name: string;
}

interface SyncDetail {
  chatroom_name: string;
  message_count?: number;
  status: string;
  error?: string;
  first_message_time?: string;
  last_message_time?: string;
}

// 获取健康状态配置
const getHealthStatusConfig = (status: 'good' | 'warning' | 'danger') => {
  const configs = {
    good: { color: '#52c41a', icon: <CheckCircleOutlined />, text: '健康' },
    warning: { color: '#faad14', icon: <ExclamationCircleOutlined />, text: '注意' },
    danger: { color: '#ff4d4f', icon: <CloseCircleOutlined />, text: '异常' }
  };
  return configs[status];
};

// 1. 群聊下拉数据结构调整，支持 nickname
// chatGroups: [{ name: string, nickname: string }]
// 2. 群聊下拉选择项，显示 nickname，存储 nickname
// TODO: 后续细化类型
 
const fetchChatGroups = async (): Promise<{ name: string, nickname: string }[]> => {
  try {
    const response = await syncAPI.getChatrooms();
    // 兼容后端返回结构
    if (response.success && Array.isArray(response.data)) {
      return response.data.map((room: { name: string; nickname?: string }) => ({
        name: room.name || '',
        nickname: room.nickname || room.name || '',
      }));
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
  const [form] = Form.useForm();
  const [chatGroups, setChatGroups] = useState<{ name: string, nickname: string }[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);

  // 新增状态：控制显示'active'（执行中）或'archived'（已结束）项目
  const [displayStatus, setDisplayStatus] = useState('active'); 

  // 新增状态：用于搜索、过滤和排序
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all'); // all, good, warning, danger
  const [sortOrder, setSortOrder] = useState('health'); // health, name, activity

  // 同步项目ID状态
  const [syncingProjectId, setSyncingProjectId] = useState<number | null>(null);

  // 新增：同步结果抽屉相关状态
  const [syncDrawerVisible, setSyncDrawerVisible] = useState(false);
  const [syncResult, setSyncResult] = useState<SyncResult | null>(null);
  const [syncLog, setSyncLog] = useState<string[]>([]);
  const [currentSyncProject, setCurrentSyncProject] = useState<Project | null>(null);

  // 1. 新增同步弹窗相关状态变量
  const [syncModalVisible, setSyncModalVisible] = useState(false); // 控制同步确认弹窗显示
  const [syncRange, setSyncRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null); // 同步时间区间
  const [syncTargetProject, setSyncTargetProject] = useState<Project | null>(null); // 当前待同步的项目

  // 新增：用于记录当前正在删除的项目ID，实现删除按钮loading
  const [deletingProjectId, setDeletingProjectId] = useState<number | null>(null);

  // 1. 新增受控 Modal 状态
  const [deleteModalVisible, setDeleteModalVisible] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);

  const logEndRef = useRef<HTMLDivElement>(null);

  // 获取项目列表并批量加载详情
  const fetchProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await projectAPI.getProjects();
      if (res.success && Array.isArray(res.data)) {
        // 并发请求每个项目详情
        const detailResults: ApiResponse<ProjectDetail>[] = await Promise.all(
          (res.data as Project[]).map((proj) => projectAPI.getProjectDetail(proj.id) as Promise<ApiResponse<ProjectDetail>>)
        );
        // 合并统计字段到项目卡片
        const projectsWithStats: Project[] = (res.data as Project[]).map((proj, idx) => {
          const detail = detailResults[idx];
          if (detail.success && detail.data && detail.data.stats) {
            const health_score = detail.data.health?.health_score;
            let health_status: 'good' | 'warning' | 'danger' | undefined = undefined;
            if (typeof health_score === 'number') {
              if (health_score > 80) health_status = 'good';
              else if (health_score > 60) health_status = 'warning';
              else health_status = 'danger';
            }
            return {
              ...proj,
              ...detail.data.stats,
              health_status,
              negative_keywords_count: detail.data.keywords?.negative_score || 0,
              rework_rate: detail.data.stats?.rework_rate || 0,
              total_files: detail.data.stats?.total_files || 0,
              total_messages: detail.data.stats?.total_messages || 0,
            };
          }
          return proj;
        });
        setProjects(projectsWithStats);
      } else {
        setProjects([]);
        setError(res.error || '获取项目列表失败');
      }
    } catch {
      setError('获取项目数据失败');
      setProjects([]);
    } finally {
      setLoading(false);
    }
  };

  // 获取员工列表 (新增)
  const fetchEmployees = async () => {
    const response = await employeeAPI.getEmployees();
    if (response.success && response.data) {
      // 后端返回的是EmployeeMapping[], 前端需要的是{id, name}
      const formattedEmployees = (response.data as EmployeeMapping[]).map((emp) => ({
        id: emp.id,
        name: emp.real_name,
      }));
      setEmployees(formattedEmployees);
    }
  };

  // Memoized: 过滤和排序项目列表
  const filteredAndSortedProjects = React.useMemo(() => {
    // 根据选择的视图（执行中/已结束）过滤项目
    let result = projects.filter(p => {
      if (displayStatus === 'active') {
        return p.status === 'active';
      } else {
        return p.status !== 'active';
      }
    });

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
  }, [projects, searchQuery, statusFilter, sortOrder, displayStatus]);

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
        
        // 如果项目状态从"已结束"变更为"执行中"，则自动切换视图
        if (editingProject.status !== 'active' && values.status === 'active') {
          setDisplayStatus('active');
          notification.info({
            message: '项目状态已更新',
            description: `项目 "${values.project_name}" 已移至"执行中"列表。`,
            placement: 'topRight',
          });
        }

      } else {
        message.error(response.error || '项目更新失败');
      }
    } catch (error) {
      console.error('更新项目失败:', error);
      message.error('更新项目失败');
    }
  };

  // 删除项目（增加loading和详细错误提示）
  const handleDeleteProject = async (id: number) => {
    setDeletingProjectId(id); // 设置loading
    try {
      const response = await projectAPI.deleteProject(id);
      if (response.success) {
        message.success('项目已成功删除');
        fetchProjects();
      } else {
        // 删除失败，弹窗详细提示
        Modal.error({
          title: '删除失败',
          content: response.error || '项目删除失败',
        });
      }
    } catch (error: unknown) {
      console.error('删除项目失败:', error);
      Modal.error({
        title: '删除失败',
        content: (error instanceof Error ? error.message : '项目删除失败'),
      });
    } finally {
      setDeletingProjectId(null); // 取消loading
    }
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
    form.validateFields().then((values: ProjectFormData) => {
      // 确保 status 字段存在
      const processedValues = {
        ...values,
        status: values.status || (editingProject ? editingProject.status : 'active'),
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

  // 2. 修改同步按钮逻辑：点击后弹窗，确认后再发起同步
  const handleSyncClick = (project: Project) => {
    setSyncTargetProject(project);
    // 默认时间区间：最近7天
    setSyncRange([dayjs().subtract(7, 'day'), dayjs()]);
    setSyncModalVisible(true);
  };

  /**
   * 同步数据主函数
   * @param project 当前同步的项目对象
   * @param range 时间区间 [开始, 结束]
   */
  const handleSyncData = async (project: Project, range: [dayjs.Dayjs, dayjs.Dayjs]) => {
    setSyncingProjectId(project.id);
    setCurrentSyncProject(project);
    setSyncDrawerVisible(true);
    setSyncLog([`[${dayjs().format('HH:mm:ss')}] 开始为项目 "${project.project_name}" 同步 ${range[0].format('YYYY-MM-DD')} ~ ${range[1].format('YYYY-MM-DD')} 的数据...`]);
    setSyncResult(null);

    try {
      // 发起流式同步请求
      const response = await fetch(`/api/v1/sync/project/${project.id}/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start_date: range[0].format('YYYY-MM-DD'),
          end_date: range[1].format('YYYY-MM-DD'),
          sync_type: 'all',
          chatroom_names: [],
        }),
      });
      if (!response.ok || !response.body) {
        throw new Error(`服务器响应错误: ${response.status} ${response.statusText}`);
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          setSyncLog(prev => [...prev, `[${dayjs().format('HH:mm:ss')}] 数据同步完成。`]);
          break;
        }
        const chunk = decoder.decode(value, { stream: true });
        // 解析后端流式日志
        const lines = chunk.split('\n').filter(line => line.startsWith('data:'));
        for (const line of lines) {
          const jsonString = line.substring(5);
          if (jsonString.trim()) {
            try {
              const data = JSON.parse(jsonString);
              if (data.type === 'log') {
                const logLines = data.message.split('\n');
                setSyncLog(prev => [...prev, ...logLines.map((l: string) => `[${dayjs().format('HH:mm:ss')}] ${l}`)]);
                setTimeout(() => { if (logEndRef.current) logEndRef.current.scrollIntoView({ behavior: 'smooth' }); }, 100);
              } else if (data.type === 'result') {
                setSyncResult(data.data);
                notification.success({
                  message: '同步成功',
                  description: `项目「${project.project_name}」数据已更新。`,
                  placement: 'topRight',
                });
                fetchProjects(); // 同步完成后刷新项目列表
              }
            } catch (err) {
              setSyncLog(prev => [...prev, `[${dayjs().format('HH:mm:ss')}] 日志解析异常: ${err}`]);
            }
          }
        }
      }
    } catch (error) {
      // 所有异常都详细输出到日志区和notification
      const errorMessage = `[${dayjs().format('HH:mm:ss')}] 同步失败: ${error instanceof Error ? error.message : '未知错误'}`;
      setSyncLog(prev => [...prev, errorMessage]);
      notification.error({
        message: '同步失败',
        description: errorMessage,
        placement: 'topRight',
        duration: 0,
      });
    } finally {
      setSyncingProjectId(null);
    }
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

  // 1. 同步失败时日志区和抽屉顶部都显示明显错误提示
  {syncResult === null && syncLog.some(log => log.includes('同步失败')) && (
    <Alert
      type="error"
      showIcon
      message="同步失败"
      description="请检查网络或后端服务，详细错误见下方日志。"
      style={{ marginBottom: 16 }}
    />
  )}

  // 2. 同步成功后支持一键复制日志
  {syncResult && (
    <Button
      style={{ marginBottom: 16 }}
      onClick={() => {
        navigator.clipboard.writeText(syncLog.join('\n'));
        message.success('日志已复制到剪贴板');
      }}
    >
      复制全部日志
    </Button>
  )}

  // 1. 同步结果区支持导出为JSON
  {syncResult && (
    <Button
      style={{ marginBottom: 16, marginLeft: 8 }}
      onClick={() => {
        const blob = new Blob([JSON.stringify(syncResult, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `sync_result_${syncResult.project_id || 'project'}.json`;
        a.click();
        URL.revokeObjectURL(url);
        message.success('同步结果已导出为JSON');
      }}
    >
      导出同步结果(JSON)
    </Button>
  )}

  // 2. 同步完成后自动滚动到结果区
  useEffect(() => {
    if (syncResult && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [syncResult]);

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
          <Card 
            hoverable
            onClick={() => setDisplayStatus('active')}
            style={{ border: displayStatus === 'active' ? '2px solid #52c41a' : '', cursor: 'pointer' }}
          >
            <Statistic
              title="执行中项目数"
              value={projects.filter(p => p.status === 'active').length}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card 
            hoverable
            onClick={() => setDisplayStatus('archived')}
            style={{ border: displayStatus === 'archived' ? '2px solid #faad14' : '', cursor: 'pointer' }}
          >
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
              placeholder={displayStatus === 'active' ? "搜索执行中的项目..." : "搜索已结束的项目..."}
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
                    onClick={() => {
                      setProjectToDelete(project);
                      setDeleteModalVisible(true);
                    }}
                    loading={deletingProjectId === project.id}
                    aria-label="删除项目"
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
                    <Tooltip title="编辑项目">
                      <Button icon={<EditOutlined />} onClick={() => handleEdit(project)} />
                    </Tooltip>
                    <Tooltip title="同步数据">
                      <Button 
                        icon={<SyncOutlined />} 
                        onClick={() => handleSyncClick(project)}
                        loading={syncingProjectId === project.id}
                      />
                    </Tooltip>
                    <Link href={`/projects/${project.id}`} passHref>
                      <Button type="primary" icon={<EyeOutlined />}>
                        查看详情
                      </Button>
                    </Link>
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
        onOk={handleSubmit || (() => {})}
        onCancel={handleCancel || (() => {})}
        width={600}
        okText={editingProject ? '保存' : '创建项目'}
        cancelText="取消"
        destroyOnHidden
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
            status: editingProject?.status || 'active', // 确保 status 有初始值
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
            rules={[{ required: true, message: '请至少关联一个内部群聊' }]}
          >
            <Select
              mode="tags"
              showSearch
              allowClear
              style={{ width: '100%' }}
              placeholder="输入或选择内部群聊昵称，可输入多个"
              tokenSeparators={[',']}
              options={chatGroups.map(group => ({ value: group.nickname, label: group.nickname }))}
              onChange={vals => {
                // 校验输入的群昵称是否在 chatGroups 列表中
                const notFound = (vals as string[]).filter(val => !chatGroups.some(g => g.nickname === val));
                if (notFound.length > 0) {
                  message.warning(`群聊不存在：${notFound.join('，')}，请检查拼写或先在微信创建该群聊`);
                }
              }}
            />
          </Form.Item>

          <Form.Item
            name="external_chat_groups"
            label="关联外部群聊"
          >
            <Select
              mode="tags"
              showSearch
              allowClear
              style={{ width: '100%' }}
              placeholder="输入或选择外部群聊昵称，可输入多个"
              tokenSeparators={[',']}
              options={chatGroups.map(group => ({ value: group.nickname, label: group.nickname }))}
              onChange={vals => {
                const notFound = (vals as string[]).filter(val => !chatGroups.some(g => g.nickname === val));
                if (notFound.length > 0) {
                  message.warning(`群聊不存在：${notFound.join('，')}，请检查拼写或先在微信创建该群聊`);
                }
              }}
            />
          </Form.Item>

          <Form.Item
            name="status"
            label="项目状态"
            rules={[{ required: true, message: '请选择项目状态' }]}
          >
            <Select placeholder="请选择项目状态">
              <Option value="active">执行中</Option>
              <Option value="archived">已结束</Option>
            </Select>
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

      {/* 同步数据结果抽屉 */}
      <Drawer
        title={`项目同步详情: ${currentSyncProject?.project_name}`}
        open={syncDrawerVisible}
        onClose={() => setSyncDrawerVisible(false)}
        width={600}
      >
        <Title level={5}>同步结果</Title>
        {syncResult ? (
          <Descriptions bordered column={1}>
            <Descriptions.Item label="同步状态">
              <Badge status="success" text="成功" />
            </Descriptions.Item>
            <Descriptions.Item label="同步范围">{`${syncResult.start_date} ~ ${syncResult.end_date}`}</Descriptions.Item>
            <Descriptions.Item label="总计处理群聊">{syncResult.total_chatrooms}</Descriptions.Item>
            <Descriptions.Item label="成功群聊数">{syncResult.success_count}</Descriptions.Item>
            <Descriptions.Item label="失败群聊数">{syncResult.failed_count > 0 ? <Text type="danger">{syncResult.failed_count}</Text> : 0}</Descriptions.Item>
            <Descriptions.Item label="新增消息数">{syncResult.total_messages}</Descriptions.Item>
            <Descriptions.Item label="新增文件数">{syncResult.total_files}</Descriptions.Item>
            <Descriptions.Item label="详细结果">
              {(syncResult.details || []).map((detail: SyncDetail, i: number) => (
                <Tag key={i} color={detail.status === 'success' ? 'green' : 'red'}>
                  {detail.chatroom_name}: {detail.status}
                </Tag>
              ))}
            </Descriptions.Item>
          </Descriptions>
        ) : (
          <Text type="secondary">同步完成后将在此处显示结果...</Text>
        )}
      </Drawer>

      {/* 同步弹窗交互优化 */}
      <Modal
        title={`同步数据 - ${syncTargetProject?.project_name || ''}`}
        open={syncModalVisible}
        onOk={async () => {
          if (syncTargetProject && syncRange) {
            setSyncModalVisible(false);
            setSyncingProjectId(syncTargetProject.id); // 按钮loading
            await handleSyncData(syncTargetProject, syncRange);
            setSyncingProjectId(null);
          } else {
            message.warning('请先选择同步时间范围');
          }
        }}
        onCancel={() => setSyncModalVisible(false)}
        okText="开始同步"
        cancelText="取消"
        confirmLoading={!!syncingProjectId}
        destroyOnHidden
      >
        <div style={{ marginBottom: 16 }}>
          <span>请选择同步时间范围：</span>
          <RangePicker
            value={syncRange}
            onChange={val => setSyncRange(val as [dayjs.Dayjs, dayjs.Dayjs])}
            allowClear={false}
            style={{ marginLeft: 8 }}
            format="YYYY-MM-DD"
            disabledDate={current => current && current > dayjs().endOf('day')}
          />
        </div>
        <Alert
          type="info"
          showIcon
          message="同步说明"
          description="同步将根据所选时间段，抓取该项目关联群聊的所有聊天记录和文件。建议每次同步时间段不宜过长。"
        />
      </Modal>

      {/* 日志区自动滚动到底部 */}
      <Card style={{ marginBottom: 24, background: '#222', color: '#fff', height: 300, overflowY: 'auto' }}>
        {syncLog.map((log: string, index: number) => (
          <p key={index} style={{ margin: 0, fontFamily: 'monospace', fontSize: 12 }}>{log}</p>
        ))}
        {syncingProjectId && <Spin size="small" />}
        <div ref={logEndRef} />
      </Card>

      {/* 受控 Modal */}
      <Modal
        title="您确定要删除吗？"
        open={deleteModalVisible}
        onOk={async () => {
          if (projectToDelete) {
            await handleDeleteProject(projectToDelete.id);
            setDeleteModalVisible(false);
            setProjectToDelete(null);
          }
        }}
        onCancel={() => {
          setDeleteModalVisible(false);
          setProjectToDelete(null);
        }}
        okText="确认删除"
        okType="danger"
        cancelText="取消"
        confirmLoading={deletingProjectId === projectToDelete?.id}
      >
        <div>
          <p>正在删除项目「{projectToDelete?.project_name}」。此操作将会永久删除该项目及其所有关联的统计数据、文件和聊天记录。</p>
          <Typography.Text strong style={{ color: '#ff4d4f' }}>
            此操作无法撤销。
          </Typography.Text>
        </div>
      </Modal>
    </div>
  );
}

export default ProjectsPage;