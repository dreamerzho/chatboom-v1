// frontend/src/app/projects/[id]/report/page.tsx
// 该文件是项目的报告预览页面，旨在以简洁的表格形式，清晰地展示项目的核心量化信息。
// 主要包括员工贡献统计和高风险文件列表，用于内部复盘和数据核对。

'use client';

import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Typography, Table, Tag, Button, Breadcrumb } from 'antd';
import { ArrowLeftOutlined, HomeOutlined } from '@ant-design/icons';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { projectAPI } from '@lib/api';

const { Title, Text } = Typography;

export default function ProjectReportPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params?.id;
  const [project, setProject] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId) return;
    setLoading(true);
    projectAPI.getProjectDetail(projectId)
      .then(res => {
        if (res.success && res.data) {
          setProject(res.data);
        } else {
          setError(res.error || '未找到项目详情');
        }
      })
      .catch(() => setError('获取项目详情失败'))
      .finally(() => setLoading(false));
  }, [projectId]);

  if (loading) return <div>加载中...</div>;
  if (error) return <div style={{color:'red'}}>{error}</div>;
  if (!project) return <div>未找到项目</div>;

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
                <Breadcrumb.Item>{project.project_name}</Breadcrumb.Item>
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
              <Title level={2}>项目报告: {project.project_name}</Title>
              <Text type="secondary">报告生成时间: {new Date().toLocaleString()}</Text>
            </div>

            {/* 员工贡献统计 */}
            <Title level={4} style={{ marginBottom: 20 }}>员工贡献统计 (WE)</Title>
            <Table
              columns={employeeColumns}
              dataSource={project.employee_stats}
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
              dataSource={project.high_rework_files}
              rowKey="id"
              pagination={false}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
} 