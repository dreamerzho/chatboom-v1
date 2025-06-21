// frontend/src/app/projects/[id]/page.tsx
// 该文件是项目详情页，用于深度展示单个项目的健康状况、核心指标、数据图表和详细记录。
// 整体布局遵循"一眼概览，按需钻取"的设计理念。

'use client';

import React, { useState } from 'react';
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
  Table,
  Space,
  Modal,
} from 'antd';
import {
  InfoCircleOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  SyncOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useParams, useRouter } from 'next/navigation';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

// --- Mock Data (未来由API提供) ---
const mockProject = {
  id: 1,
  name: '建杭-良渚项目',
  health: { status: 'warning', reason: '返工率偏高，文件合规性有待提高' },
};

const mockMetrics = [
  { title: '总WE投入', value: 128.5, change: 5, changeType: 'increase', unit: 'WE', formula: '所有参与员工在此项目上投入的有效工作量总和。' },
  { title: '客户返工率', value: 22, change: -3, changeType: 'decrease', unit: '%', formula: '返工文件数 / (有效文件总数 + 返工文件数)' },
  { title: '一次通过率', value: 78, change: 5, changeType: 'increase', unit: '%', formula: '一次性审核通过的文件数 / 有效文件总数' },
  { title: '内部修正率', value: 35, change: -2, changeType: 'decrease', unit: '%', formula: '内部发现并修正的文件数 / 内部审核文件总数' },
  { title: '文件合规率', value: 95, change: 1, changeType: 'increase', unit: '%', formula: '符合命名和存储规范的文件数 / 已归档文件总数' },
];

const weData = [
  { name: '设计师A', value: 40, color: '#0088FE' },
  { name: '设计师B', value: 30, color: '#00C49F' },
  { name: '文案A', value: 30, color: '#FFBB28' },
  { name: 'PM小王', value: 28.5, color: '#FF8042' },
];

const healthTrendData = [
  { name: 'Week 1', '返工文件数': 4, '风险事件数': 2 },
  { name: 'Week 2', '返工文件数': 3, '风险事件数': 5 },
  { name: 'Week 3', '返工文件数': 6, '风险事件数': 3 },
  { name: 'Week 4', '返工文件数': 5, '风险事件数': 1 },
];

const mockFiles = [
  { id: 1, name: '主KV-v1.jpg', version: 'v1', sender: '设计师A', timestamp: '2025-06-20 10:00', compliant: true },
  { id: 2, name: '主KV-v2-客户修改.jpg', version: 'v2-客户修改', sender: '设计师A', timestamp: '2025-06-21 14:00', compliant: false },
  { id: 3, name: '营销活动方案.docx', version: 'v1.0', sender: 'PM-小王', timestamp: '2025-06-19 18:30', compliant: true },
  { id: 4, name: '朋友圈九宫格-v3.zip', version: 'v3', sender: '设计师B', timestamp: '2025-06-21 17:00', compliant: true },
];

const mockChatContext = [
    { sender: 'PM-小王', time: '13:58', content: '@客户李总 这是我们根据新思路出的v2稿，您看下'},
    { sender: '客户李总', time: '14:00', content: '这个方向还是不太对，我们再想想'},
    { sender: '设计师A', time: '14:01', content: '收到，我们内部再碰一下，看看如何调整'},
    { sender: 'PM-小王', time: '14:02', content: '好的，我们尽快给到新方向'},
];

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

const ProjectDetailPage = () => {
  const params = useParams();
  const router = useRouter();
  const { id } = params;
  const [isContextModalVisible, setIsContextModalVisible] = useState(false);
  const [currentFileContext, setCurrentFileContext] = useState<any>(null);

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

  const fileTableColumns = [
    { title: '文件名', dataIndex: 'name', key: 'name' },
    { title: '版本', dataIndex: 'version', key: 'version' },
    { title: '提交人', dataIndex: 'sender', key: 'sender' },
    { title: '提交时间', dataIndex: 'timestamp', key: 'timestamp' },
    {
      title: '合规状态',
      dataIndex: 'compliant',
      key: 'compliant',
      render: (compliant: boolean) => (
        <Badge status={compliant ? 'success' : 'error'} text={compliant ? '合规' : '不合规'} />
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
              {mockProject.name} (ID: {id})
            </Title>
          </Col>
          <Col>
            <Space size="large">
              <Tooltip title={mockProject.health.reason}>
                <Badge
                  status={getHealthBadge(mockProject.health.status).status as any}
                  text={getHealthBadge(mockProject.health.status).text}
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
        {mockMetrics.map((metric) => (
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
                  data={weData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  outerRadius={80}
                  innerRadius={60}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {weData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip />
                <foreignObject x="45%" y="45%" width="100px" height="100px">
                    <div style={{ textAlign: 'center' }}>
                        <Title level={4}>{weData.reduce((acc, cur) => acc + cur.value, 0)}</Title>
                        <Text>Total WE</Text>
                    </div>
                </foreignObject>
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="项目健康度趋势 (近4周)">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={healthTrendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <RechartsTooltip />
                <Legend />
                <Line type="monotone" dataKey="返工文件数" stroke="#ff4d4f" />
                <Line type="monotone" dataKey="风险事件数" stroke="#faad14" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* 4. 深度数据表格区 */}
      <Card>
        <Tabs defaultActiveKey="1">
          <TabPane tab="文件记录" key="1">
            <Table columns={fileTableColumns} dataSource={mockFiles} rowKey="id" />
          </TabPane>
          <TabPane tab="风险事件" key="2">
            <Paragraph>风险事件表格（待开发）...</Paragraph>
          </TabPane>
          <TabPane tab="聊天记录" key="3">
            <Paragraph>聊天记录查看器（待开发）...</Paragraph>
          </TabPane>
        </Tabs>
      </Card>
      
      {/* 追溯上下文 Modal */}
      <Modal
        title={`上下文聊天记录: ${currentFileContext?.name}`}
        open={isContextModalVisible}
        onCancel={handleContextModalCancel}
        footer={[
          <Button key="back" onClick={handleContextModalCancel}>
            关闭
          </Button>,
        ]}
        width={700}
      >
        <div style={{ maxHeight: '60vh', overflowY: 'auto', marginTop: '20px' }}>
          {mockChatContext.map((msg, index) => (
            <div key={index} style={{ marginBottom: '16px' }}>
              <Space>
                <Text strong>{msg.sender}</Text>
                <Text type="secondary">{msg.time}</Text>
              </Space>
              <Paragraph style={{ margin: '4px 0 0 0', background: '#f5f5f5', padding: '8px', borderRadius: '4px' }}>
                {msg.content}
              </Paragraph>
            </div>
          ))}
        </div>
      </Modal>
    </div>
  );
};

export default ProjectDetailPage; 