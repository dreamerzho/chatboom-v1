// frontend/src/app/projects/[id]/page.tsx
// 该文件是项目详情页，用于深度展示单个项目的健康状况、核心指标、数据图表和详细记录。
// 整体布局遵循"一眼概览，按需钻取"的设计理念。

'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Typography,
  Badge,
  Button,
  Statistic,
  Tooltip,
  Tabs,
  Space,
} from 'antd';
import {
  InfoCircleOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  SyncOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useParams, useRouter } from 'next/navigation';
import { projectAPI } from '../../../lib/api';
import type { TableProps } from 'antd';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

// --- Helper Functions & Components ---
const getHealthBadge = (status: string) => {
  switch (status) {
    case 'good': return { status: 'success', text: '健康' };
    case 'warning': return { status: 'warning', text: '警告' };
    case 'danger': return { status: 'error', text: '危险' };
    default: return { status: 'default', text: '未知' };
  }
};

const MetricCard = ({ metric }: { metric: any }) => (
  <Card>
    <Statistic
      title={
        <Space>
          {metric.title}
          <Tooltip title={metric.formula}>
            <InfoCircleOutlined style={{ color: 'rgba(0,0,0,.45)', cursor: 'pointer' }} />
          </Tooltip>
        </Space>
      }
      value={metric.value}
      precision={1}
      suffix={metric.unit}
      valueStyle={ metric.changeType === 'increase' ? { color: '#3f8600' } : { color: '#cf1322' }}
      prefix={ metric.changeType === 'increase' ? <ArrowUpOutlined /> : <ArrowDownOutlined /> }
    />
    <Text type="secondary" style={{ fontSize: '12px' }}>
      {metric.change}% vs last period
    </Text>
  </Card>
);

interface FileRecord {
  id: number;
  original_name: string;
  version: string;
  uploader: string;
  upload_time: string;
  status: string;
}

interface ProjectDetail {
  id: number;
  project_name: string;
  metrics?: any[];
  weData?: { name: string; value: number; color: string }[];
  health?: { status: string; reason: string };
  healthTrendData?: any[];
  chatContext?: { sender: string; time: string; content: string }[];
}

const ProjectDetailPage = () => {
  const params = useParams() as { id: string };
  const router = useRouter();
  const { id } = params;
  // 项目信息、文件列表、加载状态
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [files, setFiles] = useState<FileRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isContextModalVisible, setIsContextModalVisible] = useState(false);
  const [currentFileContext, setCurrentFileContext] = useState<FileRecord | null>(null);

  // 2. useEffect 拉取项目详情和文件列表
  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError(null);
    // 获取项目详情
    projectAPI.getProjectDetail(id)
      .then(res => {
        if (res.success && res.data) {
          setProject(res.data as ProjectDetail);
          // 获取文件列表
          return projectAPI.getProjectFiles((res.data as ProjectDetail).project_name);
        } else {
          throw new Error(res.error || '未获取到项目信息');
        }
      })
      .then(res => {
        if (res && res.success && res.data && Array.isArray((res.data as any).items)) {
          setFiles((res.data as any).items as FileRecord[]);
        } else {
          setFiles([]);
        }
      })
      .catch(e => {
        setError(e.message || '加载失败');
      })
      .finally(() => setLoading(false));
  }, [id]);

  // 3. 渲染逻辑：全部用API返回数据
  if (loading) return <div style={{padding: 32}}>加载中...</div>;
  if (error) return <div style={{padding: 32, color: 'red'}}>加载失败：{error}</div>;
  if (!project) return <div style={{padding: 32}}>未找到项目信息</div>;

  const showContextModal = (file: any) => {
    setCurrentFileContext(file);
    setIsContextModalVisible(true);
  };

  const handleContextModalCancel = () => {
    setIsContextModalVisible(false);
    setCurrentFileContext(null);
  };

  const handleGenerateReport = () => {
    router.push(`/projects/${id}/report`);
  };

  // 文件表格列
  const fileTableColumns = [
    { title: '文件名', dataIndex: 'original_name', key: 'original_name' },
    { title: '版本', dataIndex: 'version', key: 'version' },
    { title: '提交人', dataIndex: 'uploader', key: 'uploader' },
    { title: '提交时间', dataIndex: 'upload_time', key: 'upload_time' },
    {
      title: '合规状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Badge status={status === 'compliant' ? 'success' : 'error'} text={status === 'compliant' ? '合规' : '不合规'} />
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Button size="small" onClick={() => showContextModal(record)}>
          追溯上下文
        </Button>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* 1. 项目顶栏 */}
      <Card style={{ marginBottom: 24 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={2} style={{ margin: 0 }}>
              {project.project_name} (ID: {project.id})
            </Title>
          </Col>
          <Col>
            <Space size="large">
              <Tooltip title={project.health?.reason || ''}>
                <Badge
                  status={getHealthBadge(project.health?.status || '').status as any}
                  text={getHealthBadge(project.health?.status || '').text}
                />
              </Tooltip>
              <Button icon={<SyncOutlined />}>同步数据</Button>
              <Button type="primary" icon={<FileTextOutlined />} onClick={handleGenerateReport}>生成报告</Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 2. 核心指标栏 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        {project.metrics?.map((metric: any) => (
          <Col xs={24} sm={12} md={12} lg={8} xl={4} key={metric.title}>
            <MetricCard metric={metric} />
          </Col>
        ))}
      </Row>

      {/* 3. 数据可视化区 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="工作量贡献分布 (WE)">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={project.weData || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  outerRadius={80}
                  innerRadius={60}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {(project.weData || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default ProjectDetailPage;