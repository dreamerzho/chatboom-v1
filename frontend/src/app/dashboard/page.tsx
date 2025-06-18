// 仪表盘页面
// 该页面用于展示系统的核心指标（KPI）、近期动态和快捷入口
// 集成后端API，动态展示真实数据

'use client';

import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Typography, Spin, Alert, Button, List, Tag, Avatar, Space } from 'antd';
import { 
  ReloadOutlined, 
  UserOutlined, 
  FileOutlined, 
  ProjectOutlined, 
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  TrophyOutlined,
  WarningOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { dashboardAPI } from '../../lib/api';

const { Title, Text, Paragraph } = Typography;

// 仪表盘统计数据接口
interface DashboardStats {
  total_employees: number;
  active_projects: number;
  total_files: number;
  compliant_files: number;
  recent_files: Array<{
    date: string;
    count: number;
  }>;
}

// 员工排行榜接口
interface EmployeeRanking {
  rank: number;
  real_name: string;
  position: string;
  name_abbreviation: string;
  file_count: number;
  compliant_count: number;
  compliance_rate: number;
}

// 负面反馈接口
interface NegativeFeedback {
  sender_name: string;
  content: string;
  message_time: string;
  group_name: string;
  negative_keywords: string[];
}

// 近期动态接口
interface RecentActivity {
  type: 'file_upload' | 'project_update';
  title: string;
  description: string;
  time: string;
  status: string;
}

function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [employeeRanking, setEmployeeRanking] = useState<EmployeeRanking[]>([]);
  const [negativeFeedback, setNegativeFeedback] = useState<NegativeFeedback[]>([]);
  const [recentActivities, setRecentActivities] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // 获取仪表盘数据
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // 并行获取所有数据
      const [statsRes, rankingRes, feedbackRes, activitiesRes] = await Promise.all([
        dashboardAPI.getStats(),
        dashboardAPI.getEmployeeRanking(),
        dashboardAPI.getNegativeFeedback(),
        dashboardAPI.getRecentActivity()
      ]);
      
      if (statsRes.success && statsRes.data) {
        setStats(statsRes.data);
      }
      
      if (rankingRes.success && rankingRes.data) {
        setEmployeeRanking(rankingRes.data);
      }
      
      if (feedbackRes.success && feedbackRes.data) {
        setNegativeFeedback(feedbackRes.data);
      }
      
      if (activitiesRes.success && activitiesRes.data) {
        setRecentActivities(activitiesRes.data);
      }
    } catch (err) {
      console.error('获取仪表盘数据失败:', err);
      setError('获取数据失败，请检查网络连接');
    } finally {
      setLoading(false);
    }
  };

  // 刷新数据
  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchDashboardData();
    setRefreshing(false);
  };

  // 组件加载时获取数据
  useEffect(() => {
    fetchDashboardData();
  }, []);

  // 加载状态
  if (loading && !stats) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text>正在加载仪表盘数据...</Text>
        </div>
      </div>
    );
  }

  // 错误状态
  if (error) {
    return (
      <div style={{ padding: 24 }}>
        <Alert
          message="数据加载失败"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" onClick={handleRefresh}>
              重试
            </Button>
          }
        />
      </div>
    );
  }

  // 计算合规率
  const complianceRate = stats?.total_files && stats.total_files > 0 
    ? Math.round((stats.compliant_files / stats.total_files) * 100) 
    : 0;

  return (
    <div style={{ padding: 24 }}>
      {/* 页面标题和刷新按钮 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>数据概览</Title>
        <Button 
          icon={<ReloadOutlined />} 
          onClick={handleRefresh}
          loading={refreshing}
        >
          刷新数据
        </Button>
      </div>

      {/* 关键指标区域 - 四个KPI卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic 
              title="项目总数" 
              value={stats?.active_projects || 0}
              prefix={<ProjectOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic 
              title="员工总数" 
              value={stats?.total_employees || 0}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic 
              title="文件总数" 
              value={stats?.total_files || 0}
              prefix={<FileOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic 
              title="规范文件数" 
              value={stats?.compliant_files || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 动态分析组件区域 */}
      <Row gutter={16}>
        {/* 员工工作量排行榜 */}
        <Col xs={24} lg={8}>
          <Card 
            title={
              <Space>
                <TrophyOutlined style={{ color: '#faad14' }} />
                工作量最高的员工排行榜
              </Space>
            }
            style={{ height: 400 }}
          >
            {employeeRanking.length > 0 ? (
              <List
                dataSource={employeeRanking}
                renderItem={(item) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={
                        <Avatar 
                          style={{ 
                            backgroundColor: item.rank <= 3 ? '#faad14' : '#d9d9d9',
                            color: item.rank <= 3 ? '#fff' : '#666'
                          }}
                        >
                          {item.rank}
                        </Avatar>
                      }
                      title={
                        <Space>
                          <Text strong>{item.real_name}</Text>
                          <Tag color="blue">{item.position}</Tag>
                        </Space>
                      }
                      description={
                        <div>
                          <div>文件数量: {item.file_count} | 规范率: {item.compliance_rate}%</div>
                          <div style={{ fontSize: 12, color: '#999' }}>
                            缩写: {item.name_abbreviation}
                          </div>
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            ) : (
              <div style={{ textAlign: 'center', color: '#999', padding: 40 }}>
                <UserOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                <div>暂无员工工作量数据</div>
              </div>
            )}
          </Card>
        </Col>

        {/* 近期负面反馈 */}
        <Col xs={24} lg={8}>
          <Card 
            title={
              <Space>
                <WarningOutlined style={{ color: '#ff4d4f' }} />
                近期负面反馈
              </Space>
            }
            style={{ height: 400 }}
          >
            {negativeFeedback.length > 0 ? (
              <List
                dataSource={negativeFeedback}
                renderItem={(item) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<Avatar icon={<UserOutlined />} />}
                      title={
                        <Space>
                          <Text strong>{item.sender_name}</Text>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {new Date(item.message_time).toLocaleString()}
                          </Text>
                        </Space>
                      }
                      description={
                        <div>
                          <Paragraph ellipsis={{ rows: 2 }} style={{ marginBottom: 8 }}>
                            {item.content}
                          </Paragraph>
                          <div>
                            {item.negative_keywords.map((keyword, index) => (
                              <Tag key={index} color="red" size="small">
                                {keyword}
                              </Tag>
                            ))}
                          </div>
                          <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                            群聊: {item.group_name}
                          </div>
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            ) : (
              <div style={{ textAlign: 'center', color: '#999', padding: 40 }}>
                <CheckCircleOutlined style={{ fontSize: 48, marginBottom: 16, color: '#52c41a' }} />
                <div>暂无负面反馈</div>
              </div>
            )}
          </Card>
        </Col>

        {/* 近期动态 */}
        <Col xs={24} lg={8}>
          <Card 
            title={
              <Space>
                <ClockCircleOutlined style={{ color: '#1890ff' }} />
                近期动态
              </Space>
            }
            style={{ height: 400 }}
          >
            {recentActivities.length > 0 ? (
              <List
                dataSource={recentActivities}
                renderItem={(item) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={
                        <Avatar 
                          icon={item.type === 'file_upload' ? <FileOutlined /> : <ProjectOutlined />}
                          style={{ backgroundColor: item.type === 'file_upload' ? '#52c41a' : '#1890ff' }}
                        />
                      }
                      title={
                        <Space>
                          <Text strong>{item.title}</Text>
                          <Tag color={item.status === 'compliant' ? 'green' : 'orange'}>
                            {item.status}
                          </Tag>
                        </Space>
                      }
                      description={
                        <div>
                          <Paragraph ellipsis={{ rows: 2 }} style={{ marginBottom: 4 }}>
                            {item.description}
                          </Paragraph>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {new Date(item.time).toLocaleString()}
                          </Text>
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            ) : (
              <div style={{ textAlign: 'center', color: '#999', padding: 40 }}>
                <ClockCircleOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                <div>暂无近期动态</div>
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* 合规率统计 */}
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card>
            <Row gutter={16} align="middle">
              <Col span={12}>
                <Statistic 
                  title="文件规范率" 
                  value={complianceRate}
                  suffix="%"
                  valueStyle={{ 
                    color: complianceRate >= 80 ? '#52c41a' : 
                           complianceRate >= 60 ? '#faad14' : '#ff4d4f',
                    fontSize: '32px'
                  }}
                />
              </Col>
              <Col span={12}>
                <div style={{ textAlign: 'right' }}>
                  <Text type="secondary">
                    规范文件: {stats?.compliant_files || 0} / 总文件: {stats?.total_files || 0}
                  </Text>
                  <br />
                  <Text type="secondary">
                    非规范文件: {(stats?.total_files || 0) - (stats?.compliant_files || 0)}
                  </Text>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* 近期文件上传趋势 */}
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card 
            title="近期文件上传趋势" 
            extra={<Text type="secondary">最近7天</Text>}
          >
            {stats?.recent_files && stats.recent_files.length > 0 ? (
              <Row gutter={16}>
                {stats.recent_files.map((item, index) => (
                  <Col key={index} span={3}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ 
                        fontSize: '24px', 
                        fontWeight: 'bold', 
                        color: '#1890ff' 
                      }}>
                        {item.count}
                      </div>
                      <div style={{ 
                        fontSize: '12px', 
                        color: '#999',
                        marginTop: '4px'
                      }}>
                        {new Date(item.date).toLocaleDateString('zh-CN', {
                          month: 'short',
                          day: 'numeric'
                        })}
                      </div>
                    </div>
                  </Col>
                ))}
              </Row>
            ) : (
              <div style={{ textAlign: 'center', color: '#999', padding: 20 }}>
                <ExclamationCircleOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                <div>暂无近期文件上传记录</div>
              </div>
            )}
      </Card>
        </Col>
      </Row>
    </div>
  );
}

export default DashboardPage; 