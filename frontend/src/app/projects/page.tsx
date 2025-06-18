// 项目管理页面
// 展示所有项目的卡片或列表，支持增删改查操作
// 集成后端API，实现真实数据管理

'use client';

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  List, 
  Typography, 
  Button, 
  Modal, 
  Form, 
  Input, 
  message, 
  Space, 
  Popconfirm,
  Row,
  Col,
  Statistic,
  Spin,
  Alert,
  Tag,
  Empty
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined, ProjectOutlined, FileOutlined, EyeOutlined, SyncOutlined, BarChartOutlined } from '@ant-design/icons';
import { projectAPI, fileAPI } from '../../lib/api';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

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
}

// 项目表单数据接口
interface ProjectFormData {
  project_name: string;
  description: string;
  internal_chat_groups?: string[];
  external_chat_groups?: string[];
}

function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [projectStats, setProjectStats] = useState<{[key: string]: number}>({});
  const [form] = Form.useForm();

  // 获取项目列表
  const fetchProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await projectAPI.getProjects();
      
      if (response.success) {
        setProjects(response.data || []);
        // 获取每个项目的文件统计
        await fetchProjectStats(response.data || []);
      } else {
        setError(response.error || '获取项目列表失败');
        message.error('获取项目列表失败');
      }
    } catch (err) {
      console.error('获取项目列表失败:', err);
      setError('网络请求失败');
      message.error('网络请求失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取项目文件统计
  const fetchProjectStats = async (projectList: Project[]) => {
    try {
      const stats: {[key: string]: number} = {};
      
      // 获取所有文件
      const filesResponse = await fileAPI.getFiles();
      if (filesResponse.success && filesResponse.data) {
        const files = filesResponse.data;
        
        // 统计每个项目的文件数量
        projectList.forEach(project => {
          stats[project.project_name] = files.filter(
            (file: any) => file.project_name === project.project_name
          ).length;
        });
      }
      
      setProjectStats(stats);
    } catch (err) {
      console.error('获取项目统计失败:', err);
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
        fetchProjects(); // 刷新列表
      } else {
        message.error(response.error || '添加项目失败');
      }
    } catch (err) {
      console.error('添加项目失败:', err);
      message.error('添加项目失败');
    }
  };

  // 更新项目
  const handleUpdateProject = async (values: ProjectFormData) => {
    if (!editingProject) return;
    try {
      await projectAPI.updateProject(editingProject.id, values);
      message.success('项目更新成功');
      fetchProjects();
      setIsModalVisible(false);
    } catch (error) {
      message.error('项目更新失败');
      console.error('Failed to update project:', error);
    }
  };


  // 删除项目
  const handleDeleteProject = async (id: number) => {
    try {
      const response = await projectAPI.deleteProject(id);
      
      if (response.success) {
        message.success('项目删除成功');
        fetchProjects(); // 刷新列表
      } else {
        message.error(response.error || '删除项目失败');
      }
    } catch (err) {
      console.error('删除项目失败:', err);
      message.error('删除项目失败');
    }
  };

  // 打开编辑模态框
  const handleEdit = (record: Project) => {
    setEditingProject(record);
    form.setFieldsValue({
      project_name: record.project_name,
      description: record.description,
      internal_chat_groups: record.internal_chat_groups?.join(', ') || '',
      external_chat_groups: record.external_chat_groups?.join(', ') || ''
    });
    setModalVisible(true);
  };

  // 打开添加模态框
  const handleAdd = () => {
    setEditingProject(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 关闭模态框
  const handleCancel = () => {
    setModalVisible(false);
    setEditingProject(null);
    form.resetFields();
  };

  // 提交表单
  const handleSubmit = () => {
    form.validateFields().then(values => {
      // Process chat group strings into arrays
      const processedValues: ProjectFormData = {
        ...values,
        internal_chat_groups: values.internal_chat_groups
          ? values.internal_chat_groups.split(',').map((s: string) => s.trim()).filter((s: string) => s)
          : undefined,
        external_chat_groups: values.external_chat_groups
          ? values.external_chat_groups.split(',').map((s: string) => s.trim()).filter((s: string) => s)
          : undefined,
      };

      if (editingProject) {
        handleUpdateProject(processedValues);
      } else {
        handleAddProject(processedValues);
      }
    });
  };

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
              prefix={<ProjectOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃项目"
              value={projects.filter(p => p.status === 'active').length}
              prefix={<ProjectOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="文件总数"
              value={Object.values(projectStats).reduce((sum, count) => sum + count, 0)}
              prefix={<FileOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="平均文件数"
              value={projects.length > 0 ? Math.round(Object.values(projectStats).reduce((sum, count) => sum + count, 0) / projects.length) : 0}
              prefix={<FileOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 项目列表 */}
      {projects.length > 0 ? (
      <List
          grid={{ gutter: 16, xs: 1, sm: 2, md: 2, lg: 3, xl: 4, xxl: 4 }}
        dataSource={projects}
          renderItem={(project) => (
          <List.Item>
              <Card
                hoverable
                actions={[
                  <Button 
                    type="text" 
                    icon={<BarChartOutlined />} 
                    onClick={() => message.info('报告功能待实现')}
                  >
                    报告
                  </Button>,
                  <Button 
                    type="text" 
                    icon={<EyeOutlined />} 
                    onClick={() => message.info('查看详情功能待实现')}
                  >
                    查看详情
                  </Button>,
                  <Button 
                    type="text" 
                    icon={<EditOutlined />} 
                    onClick={() => handleEdit(project)}
                  >
                    编辑
                  </Button>,
                  <Button 
                    type="text" 
                    icon={<SyncOutlined />} 
                    onClick={() => message.info('同步数据功能待实现')}
                  >
                    同步数据
                  </Button>,
                  <Popconfirm
                    title="确定要删除这个项目吗？"
                    description="删除后无法恢复，相关文件将失去项目关联。"
                    onConfirm={() => handleDeleteProject(project.id)}
                    okText="确定"
                    cancelText="取消"
                  >
                    <Button 
                      type="text" 
                      danger 
                      icon={<DeleteOutlined />} 
                    >
                      删除
                    </Button>
                  </Popconfirm>
                ]}
              >
                <Card.Meta
                  avatar={<ProjectOutlined style={{ fontSize: 24, color: '#1890ff' }} />} 
                  title={
                    <Space>
                      <Text strong>{project.project_name}</Text>
                      <Tag color={project.status === 'active' ? 'green' : 'orange'}>
                        {project.status === 'active' ? '活跃' : '暂停'}
                      </Tag>
                    </Space>
                  }
                  description={
                    <div>
                      <Paragraph ellipsis={{ rows: 2 }}>
                        {project.description || '暂无描述'}
                      </Paragraph>
                      <div style={{ marginTop: 8 }}>
                        <Text type="secondary">
                          文件数量: {projectStats[project.project_name] || 0}
                        </Text>
                      </div>
                      <div style={{ marginTop: 4 }}>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          创建时间: {new Date(project.created_at).toLocaleDateString()}
                        </Text>
                      </div>
                    </div>
                  }
                />
            </Card>
          </List.Item>
        )}
      />
      ) : (
        <Empty
          description="暂无项目数据"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        >
          <Button type="primary" onClick={handleAdd}>
            添加第一个项目
          </Button>
        </Empty>
      )}

      {/* 添加/编辑项目模态框 */}
      <Modal
        title={editingProject ? '编辑项目' : '添加项目'}
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
            name="project_name"
            label="项目名称"
            rules={[
              { required: true, message: '请输入项目名称' },
              { max: 50, message: '项目名称不能超过50个字符' }
            ]}
          >
            <Input placeholder="请输入项目名称" />
          </Form.Item>
          <Form.Item
            name="description"
            label="项目描述"
            rules={[
              { max: 200, message: '项目描述不能超过200个字符' }
            ]}
          >
            <TextArea
              rows={4}
              placeholder="请输入项目描述（可选）"
            />
          </Form.Item>
          <Form.Item
            name="internal_chat_groups"
            label="内部群聊"
          >
            <TextArea
              rows={2}
              placeholder="多个群聊请用逗号分隔"
            />
          </Form.Item>
          <Form.Item
            name="external_chat_groups"
            label="外部群聊"
          >
            <TextArea
              rows={2}
              placeholder="多个群聊请用逗号分隔"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default ProjectsPage;