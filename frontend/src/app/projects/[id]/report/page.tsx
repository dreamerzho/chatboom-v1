// frontend/src/app/projects/[id]/report/page.tsx
// 该文件是项目的报告预览页面，旨在以简洁的表格形式，清晰地展示项目的核心量化信息。
// 主要包括员工贡献统计和高风险文件列表，用于内部复盘和数据核对。

'use client';

import React from 'react';
import { Card, Row, Col, Typography, Table, Tag, Button, Breadcrumb } from 'antd';
import { ArrowLeftOutlined, HomeOutlined } from '@ant-design/icons';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';

const { Title, Text } = Typography;

// --- Mock Data (未来由API提供) ---
const mockProject = {
  id: 1,
  name: '建杭-良渚项目',
};

// 员工贡献统计数据
const mockEmployeeStats = [
  { id: 1, name: '设计师A', position: '主创设计师', weScore: 45.5, files: 12, rework: 3 },
  { id: 2, name: '设计师B', position: '设计师', weScore: 32.0, files: 8, rework: 1 },
  { id: 3, name: '文案A', position: '文案策划', weScore: 28.0, files: 15, rework: 2 },
  { id: 4, name: 'PM小王', position: '项目经理', weScore: 23.0, files: 5, rework: 0, remark: '主要负责沟通协调' },
];

// 高风险文件列表数据
const mockHighReworkFiles = [
  { id: 101, name: '主KV-客户修改.jpg', finalVersion: 'v4', submitter: '设计师A', lastModified: '2025-06-23', reworkCount: 4 },
  { id: 102, name: '项目启动会PPT.pptx', finalVersion: 'v5', submitter: 'PM小王', lastModified: '2025-06-18', reworkCount: 5 },
  { id: 105, name: '活动Slogan-v3.docx', finalVersion: 'v4', submitter: '文案A', lastModified: '2025-06-22', reworkCount: 4 },
];


const ReportPage = () => {
  const router = useRouter();
  const params = useParams();
  const { id } = params;

  const employeeColumns = [
    { title: '员工姓名', dataIndex: 'name', key: 'name', render: (text: string) => <Text strong>{text}</Text> },
    { title: '岗位', dataIndex: 'position', key: 'position' },
    { title: 'WE分数', dataIndex: 'weScore', key: 'weScore', sorter: (a: any, b: any) => a.weScore - b.weScore, render: (score: number) => <Tag color="blue">{score.toFixed(1)}</Tag> },
    { title: '提交文件数', dataIndex: 'files', key: 'files', sorter: (a: any, b: any) => a.files - b.files },
    { title: '返工次数', dataIndex: 'rework', key: 'rework', sorter: (a: any, b: any) => a.rework - b.rework, render: (rework: number) => <Tag color={rework > 2 ? 'red' : 'default'}>{rework}</Tag> },
    { title: '备注', dataIndex: 'remark', key: 'remark' },
  ];

  const fileColumns = [
    { title: '文件名', dataIndex: 'name', key: 'name', render: (text: string) => <Text strong>{text}</Text> },
    { title: '最终版本', dataIndex: 'finalVersion', key: 'finalVersion', render: (v: string) => <Tag color="purple">{v}</Tag> },
    { title: '提交人', dataIndex: 'submitter', key: 'submitter' },
    { title: '返工次数', dataIndex: 'reworkCount', key: 'reworkCount', sorter: (a: any, b: any) => a.reworkCount - b.reworkCount, render: (count: number) => <Tag color="red">{count}</Tag> },
    { title: '最后修改时间', dataIndex: 'lastModified', key: 'lastModified' },
  ];

  return (
    <div style={{ padding: '24px', background: '#f0f2f5', minHeight: '100vh' }}>
      <Row justify="center">
        <Col xs={24} sm={22} md={20} lg={18} xl={16}>
          {/* 页面头部 */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
             <Breadcrumb>
                <Breadcrumb.Item>
                  <Link href="/"><HomeOutlined /></Link>
                </Breadcrumb.Item>
                <Breadcrumb.Item>
                  <Link href="/projects">项目视图</Link>
                </Breadcrumb.Item>
                <Breadcrumb.Item>{mockProject.name}</Breadcrumb.Item>
                <Breadcrumb.Item>报告预览</Breadcrumb.Item>
              </Breadcrumb>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => router.back()}
            >
              返回项目详情
            </Button>
          </div>

          <Card>
            <div style={{ textAlign: 'center', marginBottom: 40 }}>
              <Title level={2}>项目报告: {mockProject.name}</Title>
              <Text type="secondary">报告生成时间: {new Date().toLocaleString()}</Text>
            </div>

            {/* 员工贡献统计 */}
            <Title level={4} style={{ marginBottom: 20 }}>员工贡献统计 (WE)</Title>
            <Table
              columns={employeeColumns}
              dataSource={mockEmployeeStats}
              rowKey="id"
              pagination={false}
              summary={pageData => {
                let totalWeScore = 0;
                pageData.forEach(({ weScore }) => {
                  totalWeScore += weScore;
                });
                return (
                  <Table.Summary.Row>
                    <Table.Summary.Cell index={0}><Text strong>总计</Text></Table.Summary.Cell>
                    <Table.Summary.Cell index={1}></Table.Summary.Cell>
                    <Table.Summary.Cell index={2}><Tag color="blue" style={{fontWeight:'bold'}}>{totalWeScore.toFixed(1)}</Tag></Table.Summary.Cell>
                    <Table.Summary.Cell index={3}></Table.Summary.Cell>
                    <Table.Summary.Cell index={4}></Table.Summary.Cell>
                    <Table.Summary.Cell index={5}></Table.Summary.Cell>
                  </Table.Summary.Row>
                );
              }}
            />

            {/* 高风险文件列表 */}
            <Title level={4} style={{ marginTop: 40, marginBottom: 20 }}>高返工风险文件列表 (返工次数 > 3)</Title>
            <Table
              columns={fileColumns}
              dataSource={mockHighReworkFiles}
              rowKey="id"
              pagination={false}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default ReportPage; 