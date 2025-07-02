'use client';

import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Button, Typography, Space, Spin, Alert } from 'antd';
import { UserOutlined, ProjectOutlined, FileOutlined, MessageOutlined, ReloadOutlined } from '@ant-design/icons';
import Link from 'next/link';
import { employeeAPI, projectAPI, fileAPI } from '@lib/api';

const { Title, Paragraph, Text } = Typography;

// 首页统计数据接口
interface HomeStats {
  total_employees: number;
  total_projects: number;
  total_files: number;
  today_messages: number;
}

function Home() {
  const [stats, setStats] = useState<HomeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // 获取首页统计数据
  const fetchHomeStats = async () => {
    try {
      setLoading(true);
      setError(null);

      // 并行获取各项数据
      const [employeesRes, projectsRes, filesRes] = await Promise.all([
        employeeAPI.getEmployees(),
        projectAPI.getProjects(),
        fileAPI.getFiles()
      ]);

      // 构建统计数据
      const homeStats: HomeStats = {
        total_employees: employeesRes.success && Array.isArray(employeesRes.data) ? employeesRes.data.length : 0,
        total_projects: projectsRes.success && Array.isArray(projectsRes.data) ? projectsRes.data.length : 0,
        total_files: filesRes.success && Array.isArray(filesRes.data) ? filesRes.data.length : 0,
        today_messages: 0 // 暂时设为0，后续可以从聊天API获取
      };

      setStats(homeStats);
    } catch (err) {
      console.error('获取首页数据失败:', err);
      setError('获取数据失败，请检查网络连接');
    } finally {
      setLoading(false);
    }
  };

  // 刷新数据
  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchHomeStats();
    setRefreshing(false);
  };

  // 组件加载时获取数据
  useEffect(() => {
    fetchHomeStats();
  }, []);

  // 加载状态
  if (loading && !stats) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text>正在加载系统数据...</Text>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* 页面标题和刷新按钮 */}
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <Title level={1}>广告公司服务监测系统</Title>
        <Paragraph style={{ fontSize: '16px', color: '#666' }}>
          专为广告公司设计的智能服务监测平台，实现工作量化、质量监控和数字资产管理
        </Paragraph>
        <Button 
          icon={<ReloadOutlined />} 
          onClick={handleRefresh}
          loading={refreshing}
          style={{ marginTop: 16 }}
        >
          刷新数据
        </Button>
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
            <Button size="small" onClick={fetchHomeStats}>
              重试
            </Button>
          }
        />
      )}

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '32px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="员工总数"
              value={stats?.total_employees || 0}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="项目总数"
              value={stats?.total_projects || 0}
              prefix={<ProjectOutlined />}
              valueStyle={{ color: '#1890ff' }}
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
              title="今日消息"
              value={stats?.today_messages || 0}
              prefix={<MessageOutlined />}
              valueStyle={{ color: '#eb2f96' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 功能模块 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} md={12}>
          <Card 
            title={<Space><span style={{ fontSize: '20px' }}>📊</span>工作量化</Space>} 
            style={{ height: '200px' }}
            hoverable
          >
            <Paragraph>
              自动统计员工在微信群中的沟通和文件交付情况，实现工作量的可视化展示。
            </Paragraph>
            <Link href="/dashboard">
              <Button type="primary">查看数据概览</Button>
            </Link>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card 
            title={<Space><span style={{ fontSize: '20px' }}>🔍</span>质量监控</Space>} 
            style={{ height: '200px' }}
            hoverable
          >
            <Paragraph>
              通过关键词分析，初步评估沟通质量，帮助提升团队协作效率。
            </Paragraph>
            <Link href="/projects">
              <Button type="primary">项目视图</Button>
            </Link>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card 
            title={<Space><span style={{ fontSize: '20px' }}>📁</span>数字资产管理</Space>} 
            style={{ height: '200px' }}
            hoverable
          >
            <Paragraph>
              将群聊中的文件根据规范自动归档，确保文件命名和存储的标准化。
            </Paragraph>
            <Link href="/files">
              <Button type="primary">文件视图</Button>
            </Link>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card 
            title={<Space><span style={{ fontSize: '20px' }}>⚙️</span>系统管理</Space>} 
            style={{ height: '200px' }}
            hoverable
          >
            <Paragraph>
              员工映射管理、系统配置、数据统计等管理功能，确保系统高效运行。
            </Paragraph>
            <Link href="/settings">
              <Button type="primary">系统设置</Button>
            </Link>
          </Card>
        </Col>
      </Row>

      {/* 快速入口 */}
      <Row gutter={[16, 16]} style={{ marginTop: '32px' }}>
        <Col span={24}>
          <Card title="快速入口">
        <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} md={6}>
                <Link href="/employees">
                  <Button type="default" block size="large">
                    <UserOutlined />
                    员工视图
                  </Button>
                </Link>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Link href="/projects">
                  <Button type="default" block size="large">
                    <ProjectOutlined />
                    项目视图
                  </Button>
                </Link>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Link href="/files">
                  <Button type="default" block size="large">
                    <FileOutlined />
                    文件视图
                  </Button>
                </Link>
          </Col>
              <Col xs={24} sm={12} md={6}>
                <Link href="/dashboard">
                  <Button type="default" block size="large">
                    <MessageOutlined />
                    数据概览
                  </Button>
                </Link>
          </Col>
        </Row>
      </Card>
        </Col>
      </Row>
    </div>
  );
}

export default Home;
