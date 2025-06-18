'use client'
import React from 'react';
import { Layout, Menu } from 'antd';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  DashboardOutlined,
  TeamOutlined,
  ProjectOutlined,
  FileOutlined,
  SettingOutlined,
} from '@ant-design/icons';

const { Sider, Content } = Layout;

interface ClientLayoutProps {
  children: React.ReactNode;
}

export default function ClientLayout({ children }: ClientLayoutProps) {
  const pathname = usePathname();
  
  // 侧边栏导航项
  const menuItems = [
    { key: 'dashboard', icon: <DashboardOutlined />, label: <Link href="/dashboard">数据概览</Link> },
    { key: 'employees', icon: <TeamOutlined />, label: <Link href="/employees">员工视图</Link> },
    { key: 'projects', icon: <ProjectOutlined />, label: <Link href="/projects">项目视图</Link> },
    { key: 'files', icon: <FileOutlined />, label: <Link href="/files">文件视图</Link> },
    { key: 'settings', icon: <SettingOutlined />, label: <Link href="/settings">系统设置</Link> },
  ];

  // 根据当前路径确定选中的菜单项
  const getSelectedKey = () => {
    if (pathname === '/' || pathname === '/dashboard') return 'dashboard';
    if (pathname.startsWith('/employees') || pathname.startsWith('/employee/')) return 'employees';
    if (pathname.startsWith('/projects')) return 'projects';
    if (pathname.startsWith('/files')) return 'files';
    if (pathname.startsWith('/settings')) return 'settings';
    return 'dashboard';
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 左侧导航栏 */}
      <Sider width={200} style={{ background: '#fff', boxShadow: '2px 0 8px rgba(0,0,0,0.04)' }}>
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 'bold',
          fontSize: 18,
          color: '#1890ff',
          borderBottom: '1px solid #f0f0f0',
          marginBottom: 8
        }}>
          广告公司服务监测系统
        </div>
        <Menu
          mode="inline"
          selectedKeys={[getSelectedKey()]}
          style={{ height: '100%', borderRight: 0 }}
          items={menuItems}
        />
      </Sider>
      {/* 右侧内容区 */}
      <Layout>
        <Content style={{ margin: 0, padding: 24, minHeight: 280, background: '#fff' }}>
      {children}
        </Content>
      </Layout>
    </Layout>
  );
} 