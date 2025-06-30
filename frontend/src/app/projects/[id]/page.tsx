// frontend/src/app/projects/[id]/page.tsx
// 该文件是项目详情页，用于深度展示单个项目的健康状况、核心指标、数据图表和详细记录。
// 整体布局遵循"一眼概览，按需钻取"的设计理念。

'use client';

import React, { useState, useEffect, useCallback } from 'react';
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
  Select,
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
  LineChart,
  XAxis,
  YAxis,
  Line,
  Legend,
} from 'recharts';
import { useParams, useRouter } from 'next/navigation';
import { projectAPI } from '@lib/api';

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

// 适配 weData，兼容后端多种结构
const adaptWeData = (raw: any[] | undefined): Array<{ name: string; value: number; color: string }> => {
  if (!raw || raw.length === 0) return [];
  if ('name' in raw[0] && 'value' in raw[0] && 'color' in raw[0]) return raw as any;
  if ('we' in raw[0] && 'author' in raw[0]) {
    const colorList = ['#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#8dd1e1', '#a4de6c'];
    const group: Record<string, { name: string; value: number; color: string }> = {};
    raw.forEach((item, idx) => {
      const key = item.author || '未知';
      if (!group[key]) {
        group[key] = {
          name: key,
          value: 0,
          color: colorList[idx % colorList.length]
        };
      }
      group[key].value += item.we || 0;
    });
    return Object.values(group);
  }
  return [];
};

const ProjectDetailPage: React.FC = () => {
  const params = useParams() as { id: string };
  const router = useRouter();
  const { id } = params;
  // 项目信息、文件列表、加载状态
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [files, setFiles] = useState<FileRecord[]>([]);
  const [healthTrendData, setHealthTrendData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isContextModalVisible, setIsContextModalVisible] = useState(false);
  const [currentFileContext, setCurrentFileContext] = useState<FileRecord | null>(null);
  // 新增周期状态
  const [period, setPeriod] = useState<'7d' | '30d'>('7d');

  // 2. useEffect 拉取项目详情和文件列表
  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError(null);
    // 并发请求项目详情和健康趋势，带period参数
    Promise.all([
      projectAPI.getProjectDetail(id, period),
      fetch(`/api/v1/projects/${id}/health-stats?period=${period}`).then(res => res.json())
    ])
      .then(([detailRes, healthRes]) => {
        if (detailRes.success && detailRes.data) {
          setProject(detailRes.data);
        } else {
          throw new Error(detailRes.error || '未获取到项目信息');
        }
        // 处理健康趋势数据
        if (Array.isArray(healthRes)) {
          const trend = healthRes.reverse().map((item, idx) => ({
            week: `Week ${idx + 1}`,
            health_score: item.health_score,
            risk_count: item.risk_count || 0,
            rework_count: item.warning_count || 0
          }));
          setHealthTrendData(trend);
        } else {
          setHealthTrendData([]);
        }
      })
      .then(() => {
        return projectAPI.getProjectFiles(project?.project_name || '');
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
  }, [id, period]);

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
              {project?.project_name} (ID: {project?.id})
            </Title>
          </Col>
          <Col>
            <Space size="large">
              <Tooltip title={project?.health?.reason || ''}>
                <Badge
                  status={getHealthBadge(project?.health?.status || '').status as any}
                  text={getHealthBadge(project?.health?.status || '').text}
                />
              </Tooltip>
              {/* 周期选择下拉框 */}
              <Select
                value={period}
                style={{ width: 100 }}
                onChange={setPeriod}
                options={[
                  { value: '7d', label: '周' },
                  { value: '30d', label: '月' }
                ]}
              />
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
                    data={adaptWeData(project.weData)}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    innerRadius={60}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {(adaptWeData(project.weData) as Array<{ name: string; value: number; color: string }>).map((entry, index) => (
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
            {healthTrendData && healthTrendData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={healthTrendData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                  <XAxis dataKey="week" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="rework_count" name="返工文件数" stroke="#ff7300" />
                  <Line type="monotone" dataKey="risk_count" name="风险事件数" stroke="#387908" />
                </LineChart>
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