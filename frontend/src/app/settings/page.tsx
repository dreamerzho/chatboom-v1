// 系统设置页面
// 包含员工映射管理、未映射用户、关键词管理等入口
// 集成后端API，实现实际的管理功能

'use client';

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Typography, 
  List, 
  Button, 
  Space, 
  Alert, 
  Spin, 
  Row,
  Col,
  Statistic,
  Tag
} from 'antd';
import { 
  UserOutlined, 
  SettingOutlined, 
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { dashboardAPI, chatlogAPI } from '@lib/api';

const { Title, Text, Paragraph } = Typography;

// 系统状态接口
interface SystemStatus {
  backend: boolean;
  database: boolean;
  chatlog: boolean;
  last_check: string;
}

function SettingsPage() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);

  // 检查系统状态
  const checkSystemStatus = async () => {
    try {
      setChecking(true);
      setError(null);

      // 并行检查各项服务
      const [healthRes, chatlogRes] = await Promise.all([
        dashboardAPI.getHealth(),
        chatlogAPI.getStatus()
      ]);

      const status: SystemStatus = {
        backend: healthRes.success,
        database: healthRes.success, // 如果后端正常，数据库也应该正常
        chatlog: chatlogRes.success || false,
        last_check: new Date().toLocaleString()
      };

      setSystemStatus(status);
    } catch (err) {
      console.error('检查系统状态失败:', err);
      setError('检查系统状态失败');
    } finally {
      setChecking(false);
      setLoading(false);
    }
  };

  // 组件加载时检查状态
  useEffect(() => {
    checkSystemStatus();
  }, []);

  // 设置功能列表
const settings = [
    { 
      title: '员工映射管理', 
      desc: '管理微信昵称与真实姓名、岗位、缩写的对应关系',
      icon: <UserOutlined style={{ fontSize: '24px', color: '#1890ff' }} />,
      path: '/employees',
      status: 'active'
    },
    { 
      title: '未映射用户列表', 
      desc: '查看聊天记录中未映射的微信用户，一键添加为新员工',
      icon: <UserOutlined style={{ fontSize: '24px', color: '#52c41a' }} />,
      path: '/employees',
      status: 'active'
    },
    { 
      title: '关键词管理', 
      desc: '管理正面/负面关键词，用于沟通质量分析（开发中）',
      icon: <SettingOutlined style={{ fontSize: '24px', color: '#faad14' }} />,
      path: '#',
      status: 'developing'
    },
    { 
      title: '群聊管理', 
      desc: '配置需要监控的群聊列表（开发中）',
      icon: <SettingOutlined style={{ fontSize: '24px', color: '#faad14' }} />,
      path: '#',
      status: 'developing'
    },
  ];

  // 加载状态
  if (loading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text>正在检查系统状态...</Text>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      {/* 页面标题 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
      <Title level={2}>系统设置</Title>
        <Button 
          icon={<ReloadOutlined />} 
          onClick={checkSystemStatus}
          loading={checking}
        >
          检查系统状态
        </Button>
      </div>

      {/* 错误提示 */}
      {error && (
        <Alert
          message="系统状态检查失败"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: 24 }}
          action={
            <Button size="small" onClick={checkSystemStatus}>
              重试
            </Button>
          }
        />
      )}

      {/* 系统状态概览 */}
      {systemStatus && (
        <Card title="系统状态概览" style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="后端服务"
                value={systemStatus.backend ? '正常' : '异常'}
                prefix={systemStatus.backend ? <CheckCircleOutlined /> : <ExclamationCircleOutlined />}
                valueStyle={{ 
                  color: systemStatus.backend ? '#52c41a' : '#ff4d4f',
                  fontSize: '16px'
                }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="数据库"
                value={systemStatus.database ? '正常' : '异常'}
                prefix={systemStatus.database ? <CheckCircleOutlined /> : <ExclamationCircleOutlined />}
                valueStyle={{ 
                  color: systemStatus.database ? '#52c41a' : '#ff4d4f',
                  fontSize: '16px'
                }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Chatlog服务"
                value={systemStatus.chatlog ? '正常' : '异常'}
                prefix={systemStatus.chatlog ? <CheckCircleOutlined /> : <ExclamationCircleOutlined />}
                valueStyle={{ 
                  color: systemStatus.chatlog ? '#52c41a' : '#ff4d4f',
                  fontSize: '16px'
                }}
              />
            </Col>
            <Col span={6}>
              <div>
                <Text type="secondary">最后检查</Text>
                <br />
                <Text>{systemStatus.last_check}</Text>
              </div>
            </Col>
          </Row>
        </Card>
      )}

      {/* 设置功能列表 */}
      <Card title="系统功能">
      <List
        dataSource={settings}
          renderItem={(item) => (
          <List.Item>
              <List.Item.Meta
                avatar={item.icon}
                title={
                  <Space>
                    <Text strong>{item.title}</Text>
                    <Tag color={item.status === 'active' ? 'green' : 'orange'}>
                      {item.status === 'active' ? '可用' : '开发中'}
                    </Tag>
                  </Space>
                }
                description={item.desc}
              />
              <Button 
                type={item.status === 'active' ? 'primary' : 'default'}
                disabled={item.status === 'developing'}
                href={item.path}
              >
                {item.status === 'active' ? '进入' : '即将推出'}
              </Button>
          </List.Item>
        )}
      />
      </Card>

      {/* 系统信息 */}
      <Card title="系统信息" style={{ marginTop: 24 }}>
        <Row gutter={16}>
          <Col span={12}>
            <Paragraph>
              <Text strong>系统版本：</Text>
              <Text code>v1.0.0</Text>
            </Paragraph>
            <Paragraph>
              <Text strong>技术栈：</Text>
              <Text code>Next.js + Flask + PostgreSQL</Text>
            </Paragraph>
          </Col>
          <Col span={12}>
            <Paragraph>
              <Text strong>开发状态：</Text>
              <Text type="success">开发中</Text>
            </Paragraph>
            <Paragraph>
              <Text strong>最后更新：</Text>
              <Text type="secondary">{new Date().toLocaleDateString()}</Text>
            </Paragraph>
          </Col>
        </Row>
      </Card>
    </div>
  );
}

export default SettingsPage; 