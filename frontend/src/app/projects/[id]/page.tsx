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
  Space,
  Empty,
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

const { Title, Text } = Typography;

// --- Helper Functions & Components ---
const getHealthBadge = (status: string) => {
  switch (status) {
    case 'good': return { status: 'success', text: '健康' };
    case 'warning': return { status: 'warning', text: '警告' };
    case 'danger': return { status: 'error', text: '危险' };
    default: return { status: 'default', text: '未知' };
  }
};

interface Metric {
  title: string;
  value: number;
  unit?: string;
  formula?: string;
  change?: number;
  changeType?: 'increase' | 'decrease';
}

const MetricCard = ({ metric }: { metric: Metric }) => (
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
  metrics?: Metric[];
  weData?: Array<{ name: string; value: number; color: string }>;
  health?: { status: string; reason: string };
  healthTrendData?: any[];
  chatContext?: { sender: string; time: string; content: string }[];
  recent_activities?: { type: string; title: string; description: string; time: string }[];
  risks?: { event_type: string; description: string; event_time: string }[];
}

const ProjectDetailPage: React.FC = () => {
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
      .then((res: { success: boolean; data?: ProjectDetail; error?: string }) => {
        if (res.success && res.data) {
          setProject(res.data);
          // 获取文件列表
          return projectAPI.getProjectFiles(res.data.project_name);
        } else {
          throw new Error(res.error || '未获取到项目信息');
        }
      })
      .then((res?: { success: boolean; data?: { items: FileRecord[] }; error?: string }) => {
        if (res && res.success && res.data && Array.isArray(res.data.items)) {
          setFiles(res.data.items);
        } else {
          setFiles([]);
        }
      })
      .catch((e: Error) => {
        setError(e.message || '加载失败');
      })
      .finally(() => setLoading(false));
  }, [id]);

  // 3. 渲染逻辑：全部用API返回数据
  if (loading) return <div style={{padding: 32}}>加载中...</div>;
  if (error) return <div style={{padding: 32, color: 'red'}}>加载失败：{error}</div>;
  if (!project) return <div style={{padding: 32}}>未找到项目信息</div>;

  const showContextModal = (file: FileRecord) => {
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
        {project.metrics && project.metrics.length > 0 ? (
          (project.metrics as Metric[]).map((metric: Metric) => (
            <Col xs={24} sm={12} md={12} lg={8} xl={4} key={metric.title}>
              <MetricCard metric={metric} />
            </Col>
          ))
        ) : (
          <Col span={24}><Empty description="暂无核心指标" /></Col>
        )}
      </Row>

      {/* 3. 数据可视化区 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="工作量贡献分布 (WE)">
            {project.weData && project.weData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={project.weData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    innerRadius={60}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {(project.weData as Array<{ name: string; value: number; color: string }>).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="暂无数据" />
            )}
          </Card>
        </Col>
        {/* 健康趋势卡片 */}
        <Col xs={24} lg={12}>
          <Card title="健康趋势">
            {/* 健康趋势折线图 */}
            {project.healthTrendData && project.healthTrendData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <div>TODO: 健康趋势折线图</div>
              </ResponsiveContainer>
            ) : (
              <Empty description="暂无健康趋势数据" />
            )}
          </Card>
        </Col>
      </Row>

      {/* 4. 文件列表卡片 */}
      <Card title="项目文件列表" style={{ marginBottom: 24 }}>
        {files && files.length > 0 ? (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th>文件名</th>
                <th>版本</th>
                <th>提交人</th>
                <th>提交时间</th>
                <th>合规状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {files.map(file => (
                <tr key={file.id} style={{ borderBottom: '1px solid #eee' }}>
                  <td>{file.original_name}</td>
                  <td>{file.version}</td>
                  <td>{file.uploader}</td>
                  <td>{file.upload_time}</td>
                  <td>
                    <Badge status={file.status === 'compliant' ? 'success' : 'error'} text={file.status === 'compliant' ? '合规' : '不合规'} />
                  </td>
                  <td>
                    <Button size="small" onClick={() => showContextModal(file)}>追溯上下文</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <Empty description="暂无文件" />
        )}
      </Card>

      {/* 5. 上下文追溯弹窗 */}
      {isContextModalVisible && currentFileContext && (
        <Card title={`文件上下文 - ${currentFileContext.original_name}`} style={{ marginBottom: 24 }}>
          <div>TODO: 文件上下文追溯内容</div>
          <Button onClick={handleContextModalCancel}>关闭</Button>
        </Card>
      )}

      {/* 6. 近期动态/风险事件卡片 */}
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <Card title="近期动态">
            {project.recent_activities && project.recent_activities.length > 0 ? (
              <ul style={{ paddingLeft: 16 }}>
                {project.recent_activities.map((act, idx) => (
                  <li key={idx} style={{ marginBottom: 8 }}>
                    <b>{act.type === 'file_upload' ? '文件上传' : '消息'}</b>：{act.title} <span style={{ color: '#888' }}>{act.description}</span> <span style={{ color: '#aaa' }}>{act.time}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <Empty description="暂无近期动态" />
            )}
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="风险事件">
            {project.risks && project.risks.length > 0 ? (
              <ul style={{ paddingLeft: 16 }}>
                {project.risks.map((risk, idx) => (
                  <li key={idx} style={{ marginBottom: 8 }}>
                    <b>{risk.event_type || '风险'}</b>：{risk.description} <span style={{ color: '#aaa' }}>{risk.event_time}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <Empty description="暂无风险事件" />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default ProjectDetailPage;