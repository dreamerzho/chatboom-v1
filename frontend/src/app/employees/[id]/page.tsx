// pages/employees/[id]/page.tsx
// 员工个人详情页
// 页面功能：
// 1. 展示员工的基本信息、头像、岗位。
// 2. 根据精准评估模型(V2)，动态展示该员工的详细负荷数据。
//    - 对创意岗，展示产出WE、过程成本WE。
//    - 对管理岗(PM/AE)，展示其对应的多维度WE。
// 3. 以表格形式，展示该员工在各个项目中的具体表现，如迭代次数、与个人基准的对比等。
// 4. 所有数据均为前端模拟，以完整复现V2模型中的所有核心指标。

'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { PageHeader } from '@ant-design/pro-layout';
import { Card, Row, Col, Statistic, Typography, Spin, Alert, Table, Space, Avatar, Descriptions, Tag } from 'antd';
import { UserOutlined } from '@ant-design/icons';
import type { TableProps } from 'antd';

const { Title, Text, Paragraph } = Typography;

// --- 类型定义 ---
interface EmployeeDetails {
  id: number;
  real_name: string;
  position: '设计' | '文案' | 'PM' | 'AE';
  avatar: string;
  personal_avg_revisions: number; // 个人能力基线-平均迭代次数
  load_index: number;
  // 创意岗数据
  final_output_we?: number;
  process_cost_we?: number;
  // PM数据
  management_we?: number;
  communication_we?: number;
  strategy_we?: number;
  // AE数据
  client_facing_we?: number;
  process_contribution_we?: number;

  project_performance: ProjectPerformance[];
}

interface ProjectPerformance {
  key: string;
  project_name: string;
  current_project_revisions: number;
  revision_health_vs_baseline: number; // (当前迭代 - 个人基线) / 个人基线
  time_to_final: number; // 平均定稿周期(小时)
}


// --- 模拟数据 ---
const mockEmployeeDatabase: Record<string, EmployeeDetails> = {
  '1': {
    id: 1,
    real_name: '张三',
    position: '设计',
    avatar: 'https://i.pravatar.cc/150?img=1',
    personal_avg_revisions: 2.5,
    load_index: 15.7,
    final_output_we: 12.5,
    process_cost_we: 3.2,
    project_performance: [
      { key: 'p1', project_name: '越城天地', current_project_revisions: 2, revision_health_vs_baseline: -0.2, time_to_final: 48 },
      { key: 'p2', project_name: '金陵中环', current_project_revisions: 4, revision_health_vs_baseline: 0.6, time_to_final: 96 },
    ]
  },
  '4': {
    id: 4,
    real_name: '赵六',
    position: 'PM',
    avatar: 'https://i.pravatar.cc/150?img=4',
    personal_avg_revisions: 0, // PM不考核迭代
    load_index: 11.0,
    management_we: 4.5,
    communication_we: 5.5,
    strategy_we: 1.0,
    project_performance: [
      { key: 'p1', project_name: '越城天地', current_project_revisions: 0, revision_health_vs_baseline: 0, time_to_final: 48 },
      { key: 'p2', project_name: '金陵中环', current_project_revisions: 0, revision_health_vs_baseline: 0, time_to_final: 96 },
      { key: 'p3', project_name: 'SKP项目', current_project_revisions: 0, revision_health_vs_baseline: 0, time_to_final: 72 },
    ]
  }
};


// 页面组件
export default function EmployeeDetailPage() {
  const router = useRouter();
  const params = useParams();
  const { id } = params;

  const [employee, setEmployee] = useState<EmployeeDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      setLoading(true);
      // 模拟API调用
      setTimeout(() => {
        const data = mockEmployeeDatabase[id as string];
        if (data) {
          setEmployee(data);
        } else {
          setError('找不到该员工的信息');
        }
        setLoading(false);
      }, 500);
    }
  }, [id]);

  const projectColumns: TableProps<ProjectPerformance>['columns'] = [
    { title: '项目名称', dataIndex: 'project_name', key: 'project_name' },
    { title: '平均定稿周期(小时)', dataIndex: 'time_to_final', key: 'time_to_final', sorter: (a,b) => a.time_to_final - b.time_to_final },
    { 
      title: '项目迭代次数', 
      dataIndex: 'current_project_revisions', 
      key: 'current_project_revisions',
      sorter: (a,b) => a.current_project_revisions - b.current_project_revisions
    },
    {
      title: '迭代健康度 (vs 个人基线)',
      dataIndex: 'revision_health_vs_baseline',
      key: 'revision_health_vs_baseline',
      render: (ratio) => {
        if (ratio === 0) return <Tag>符合预期</Tag>;
        const percent = Math.round(ratio * 100);
        const color = percent > 50 ? 'red' : percent > 20 ? 'orange' : 'green';
        const text = percent > 0 ? `高于基线 ${percent}%` : `低于基线 ${-percent}%`;
        if (color === 'red') {
            return <Tag color={color}>【项目难度预警】{text}</Tag>
        }
        return <Tag color={color}>{text}</Tag>;
      }
    }
  ];

  const renderLoadAssessment = () => {
    if (!employee) return null;

    const descriptionsItems = [];
    
    if (employee.position === '设计' || employee.position === '文案') {
      descriptionsItems.push(
        { key: '1', label: '产出价值分 (Final Output WE)', children: <Text strong style={{color: '#1890ff'}}>{employee.final_output_we}</Text> },
        { key: '2', label: '过程成本分 (Process Cost WE)', children: <Text strong style={{color: '#faad14'}}>{employee.process_cost_we}</Text> },
        { key: '3', label: '个人能力基线 (平均迭代)', children: <Text strong>{employee.personal_avg_revisions} 次/稿</Text> },
      );
    } else if (employee.position === 'PM') {
       descriptionsItems.push(
        { key: '1', label: '管理投入分 (Management WE)', children: <Text strong style={{color: '#1890ff'}}>{employee.management_we}</Text> },
        { key: '2', label: '沟通成本分 (Communication WE)', children: <Text strong style={{color: '#52c41a'}}>{employee.communication_we}</Text> },
        { key: '3', label: '策略产出分 (Strategy WE)', children: <Text strong style={{color: '#722ed1'}}>{employee.strategy_we}</Text> },
      );
    } else if (employee.position === 'AE') {
       descriptionsItems.push(
        { key: '1', label: '沟通对接分 (Client-Facing WE)', children: <Text strong style={{color: '#1890ff'}}>{employee.client_facing_we}</Text> },
        { key: '2', label: '流程贡献分 (Process Contribution WE)', children: <Text strong style={{color: '#faad14'}}>{employee.process_contribution_we}</Text> },
      );
    }

    return (
      <Card title="负荷评估详情" bordered={false}>
          <Descriptions bordered items={descriptionsItems} column={1} />
      </Card>
    );
  }

  if (loading) return <div style={{display: 'flex', justifyContent: 'center', paddingTop: 48}}><Spin size="large" /></div>;
  if (error) return <Alert message="错误" description={error} type="error" showIcon />;
  if (!employee) return <Alert message="未找到员工" type="warning" showIcon />;

  return (
    <>
      <PageHeader
        ghost={false}
        onBack={() => router.back()}
        title={
          <Space>
            <Avatar size="large" src={employee.avatar} icon={<UserOutlined />} />
            <div>
                <Title level={4} style={{marginBottom: 0}}>{employee.real_name}</Title>
                <Text type="secondary">{employee.position}</Text>
            </div>
          </Space>
        }
        extra={[
          <Statistic key="1" title="总负荷指数" value={employee.load_index} />
        ]}
      />
      
      <div style={{marginTop: 24}}>
        <Row gutter={[24, 24]}>
          <Col xs={24} md={8}>
            {renderLoadAssessment()}
          </Col>
          <Col xs={24} md={16}>
             <Card title="项目表现详情" bordered={false}>
                 <Paragraph type="secondary">
                     展示该员工在各个项目中的具体表现数据，尤其是&ldquo;迭代健康度&rdquo;指标，可以智能识别出【项目难度预警】。
                 </Paragraph>
                <Table
                  columns={projectColumns}
                  dataSource={employee.project_performance}
                  pagination={false}
                />
             </Card>
          </Col>
        </Row>
      </div>
    </>
  );
} 