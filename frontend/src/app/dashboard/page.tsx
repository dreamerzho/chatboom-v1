// 数据概览页面 - V2 (样式复刻版 - 参照新设计图)
// 页面功能:
// 1. 顶部Header，包含页面标题、时间筛选和用户头像。
// 2. 四个核心KPI统计卡片，样式完全复刻设计图。
// 3. 团队工作量趋势图和实时风险流。
// 4. 新增"团队效能榜"模块，按岗位分类展示员工效能。
// 5. 新增"项目风险榜"模块，展示各项目健康分与风险。

'use client';

import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Typography, Spin, List, Table, Tabs, Space, Avatar, Dropdown, Menu } from 'antd';
import { DownOutlined, ExclamationCircleFilled, CheckCircleFilled, ClockCircleFilled } from '@ant-design/icons';
import { Bar, Line } from '@ant-design/plots';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

// --- 组件定义 ---

// 团队效能榜表格列定义
const performanceColumns = [
  { title: '设计师', dataIndex: 'employee', key: 'employee' },
  { title: '产出WE', dataIndex: 'output_we', key: 'output_we', render: (val:number) => <Text style={{color: val > 10 ? '#3f8600' : 'inherit'}}>{val}</Text> },
  { title: '过程成本WE', dataIndex: 'process_we', key: 'process_we', render: (val:number) => <Text style={{color: val > 3.0 ? '#cf1322' : 'inherit'}}>{val}</Text> },
  { title: '平均迭代', dataIndex: 'avg_iteration', key: 'avg_iteration', render: (val:number) => <Text style={{color: val > 4.0 ? '#cf1322' : 'inherit'}}>{val}</Text> },
];

// 项目风险榜表格列定义
const riskColumns = [
  { title: '项目', dataIndex: 'project', key: 'project' },
  { 
    title: '健康分', 
    dataIndex: 'health_score', 
    key: 'health_score',
    render: (score: number) => (
      <Text style={{ color: score < 60 ? '#cf1322' : score < 80 ? '#faad14' : '#3f8600', fontWeight: 'bold' }}>
        {score}
      </Text>
    )
  },
  { title: '主要风险', dataIndex: 'main_risk', key: 'main_risk' },
];

// 风险流图标
const riskIcons = {
  danger: <ExclamationCircleFilled style={{ color: '#f5222d', fontSize: '24px' }} />,
  warning: <ClockCircleFilled style={{ color: '#faad14', fontSize: '24px' }} />,
  default: <CheckCircleFilled style={{ color: '#52c41a', fontSize: '24px' }} />,
};

// 时间筛选菜单
const timeMenu: React.ReactElement = (
  <Menu>
    <Menu.Item key="1">最近7天</Menu.Item>
    <Menu.Item key="2">最近30天</Menu.Item>
    <Menu.Item key="3">本月</Menu.Item>
  </Menu>
);


// 主页面组件
function DashboardPageV2() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => { setLoading(false); }, 500);
    return () => clearTimeout(timer);
  }, []);

  // 主图表配置
  const workloadChartConfig = {
    data: [],
    isGroup: true,
    xField: 'date',
    yField: 'value',
    seriesField: 'type',
    dodgePadding: 4,
    color: ['#1890ff', '#52c41a'],
    yAxis: {
      value: { title: { text: '总计工作当量(WE)', style: { fontSize:12 } } },
      processWE: { title: { text: '过程成本(WE)', style: { fontSize:12 } } },
    },
    geometryOptions: [
      { geometry: 'column' },
      { geometry: 'line', point: {}, lineStyle: { lineWidth: 3 } }
    ],
    legend: { position: 'top-right' as const, offsetY: -10 },
    maintainAspectRatio: false,
  };

  // KPI卡片内嵌微型图表配置
  const tinyLineConfig = {
    height: 60,
    autoFit: true,
    data: [],
    smooth: true,
    xAxis: false,
    yAxis: false,
    tooltip: false,
    lineStyle: {
        stroke: '#1890ff',
        lineWidth: 2,
    },
  };


  if (loading) {
  return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 'calc(100vh - 140px)' }}>
        <Spin size="large" tip="正在生成数据概览..." />
      </div>
    );
  }

  return (
    <div>
      {/* 页头 */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={2} style={{ margin: 0 }}>数据概览</Title>
        </Col>
        <Col>
          <Space align="center" size="large">
            <Dropdown overlay={timeMenu}>
              <a onClick={e => e.preventDefault()}>
                <Space>
                  最近7天
                  <DownOutlined />
                </Space>
              </a>
            </Dropdown>
            <Avatar src="https://i.pravatar.cc/150?img=1" />
            <Text>秦若否</Text>
          </Space>
        </Col>
      </Row>

      {/* KPI 卡片 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false}>
            <Statistic 
              title="团队负荷状态"
              valueRender={() => (
                <Space size="small">
                  <Text style={{ fontSize: 30, color: '#cf1322', fontWeight: 600 }}>3</Text>
                  <Text style={{ fontSize: 24, color: '#666' }}>/</Text>
                  <Text style={{ fontSize: 30, fontWeight: 600 }}>75</Text>
                  <Text style={{ fontSize: 24, color: '#666' }}>/</Text>
                  <Text style={{ fontSize: 30, color: '#3f8600', fontWeight: 600 }}>9</Text>
                </Space>
              )}
            />
             <Text type="secondary">高 / 中 / 低</Text>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false}>
            <Statistic 
              title="项目健康度"
              valueRender={() => (
                <Space size="small">
                  <Text style={{ fontSize: 30, color: '#3f8600', fontWeight: 600 }}>1</Text>
                  <Text style={{ fontSize: 24, color: '#666' }}>/</Text>
                  <Text style={{ fontSize: 30, color: '#faad14', fontWeight: 600 }}>1</Text>
                  <Text style={{ fontSize: 24, color: '#666' }}>/</Text>
                  <Text style={{ fontSize: 30, color: '#cf1322', fontWeight: 600 }}>1</Text>
                </Space>
              )}
            />
            <Text type="secondary">健康 / 预警 / 风险</Text>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false}>
            <Statistic 
              title="待处理风险"
              value={7}
              valueStyle={{ fontSize: 30, fontWeight: 600 }}
            />
            <Text type="secondary">个高优先级事项</Text>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false}>
             <Row>
                <Col span={12}>
                    <Statistic
                      title="平均定稿周期"
                      value={48.5}
                      precision={1}
                      valueStyle={{ fontSize: 30, fontWeight: 600 }}
                      suffix="小时"
                    />
                    <Text type="-">-0.05%</Text>
                </Col>
                <Col span={12}>
                    <Line {...tinyLineConfig} />
                </Col>
             </Row>
          </Card>
        </Col>
      </Row>

      {/* 中部图表和信息流 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={16}>
          <Card bordered={false} title={<Title level={4}>团队工作量趋势 (最近7天)</Title>}>
            <div style={{ height: 320 }}>
              <Bar {...workloadChartConfig} />
              </div>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card bordered={false} title={<Title level={4}>实时风险流</Title>} style={{height: '100%'}}>
              <List
                itemLayout="horizontal"
                dataSource={[]}
                renderItem={item => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={riskIcons[item.type as keyof typeof riskIcons]}
                      title={<Text strong>{item.description}</Text>}
                      description={<Text type="secondary">{item.time}</Text>}
                    />
                  </List.Item>
                )}
              />
          </Card>
        </Col>
      </Row>

      {/* 底部榜单 */}
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <Card bordered={false} title={<Title level={4}>团队效能榜</Title>}>
            <Tabs defaultActiveKey="1">
                <TabPane tab="设计" key="1">
                    <Table 
                        columns={performanceColumns.map(c => c.key === 'employee' ? {...c, title: '设计师'} : c)} 
                        dataSource={[]} 
                        pagination={false}
                    />
                </TabPane>
                <TabPane tab="文案" key="2">
                    <Table 
                        columns={performanceColumns.map(c => c.key === 'employee' ? {...c, title: '文案'} : c)} 
                        dataSource={[]} 
                        pagination={false}
                    />
                </TabPane>
                <TabPane tab="PM/AE" key="3">
                     <Table 
                        columns={performanceColumns.map(c => c.key === 'employee' ? {...c, title: 'PM/AE'} : c)} 
                        dataSource={[]} 
                        pagination={false}
                    />
                </TabPane>
            </Tabs>
          </Card>
              </Col>
        <Col xs={24} lg={12}>
          <Card bordered={false} title={<Title level={4}>项目风险榜</Title>}>
             <Table columns={riskColumns} dataSource={[]} pagination={false} />
          </Card>
        </Col>
      </Row>

    </div>
  );
}

export default DashboardPageV2;
