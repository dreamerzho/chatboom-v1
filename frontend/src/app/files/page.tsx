// 文件管理页面
// 用于管理项目文件，验证文件命名规范，查看文件统计信息

'use client';

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Upload, 
  Modal, 
  Form, 
  Input,
  message, 
  Space,
  Row,
  Col,
  Statistic,
  Typography
} from 'antd';
import { 
  UploadOutlined, 
  FileTextOutlined, 
  CheckCircleOutlined, 
  ExclamationCircleOutlined 
} from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { fileAPI } from '../../lib/api';

const { Title } = Typography;

// 文件记录接口定义
interface FileRecord {
  id: number;
  original_name: string;
  standardized_name: string;
  project_name: string;
  work_order: string;
  workload: string;
  author_abbreviation: string;
  version: string;
  file_extension: string;
  upload_time: string;
  uploader: string;
  file_size: string;
  status: string;
}

// 文件统计接口定义
interface FileStats {
  total_files: number;
  compliant_files: number;
  non_compliant_files: number;
  compliance_rate: number;
  recent_uploads: number;
}

// 验证结果接口定义 - 与API文件保持一致
interface ValidationResult {
  is_compliant: boolean;
  parsed_info?: Record<string, unknown>;
  errors?: string[];
}

function FilesPage() {
  const [files, setFiles] = useState<FileRecord[]>([]);
  const [stats, setStats] = useState<FileStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [validationModalVisible, setValidationModalVisible] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [form] = Form.useForm();

  // 表格列定义
  const columns = [
    {
      title: '文件名',
      dataIndex: 'original_name',
      key: 'original_name',
      render: (text: string) => (
        <span style={{ fontWeight: 'bold' }}>{text}</span>
      ),
    },
    {
      title: '项目',
      dataIndex: 'project_name',
      key: 'project_name',
    },
    {
      title: '工单',
      dataIndex: 'work_order',
      key: 'work_order',
    },
    {
      title: '工作量',
      dataIndex: 'workload',
      key: 'workload',
    },
    {
      title: '作者',
      dataIndex: 'author_abbreviation',
      key: 'author_abbreviation',
      render: (text: string) => (
        <span style={{ 
          background: '#1890ff', 
          color: 'white', 
          padding: '2px 8px', 
          borderRadius: 4,
          fontSize: 12
        }}>
          {text}
        </span>
      ),
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = status === 'compliant' ? '#52c41a' : '#ff4d4f';
        const text = status === 'compliant' ? '合规' : '不合规';
        return (
          <span style={{ color, fontWeight: 'bold' }}>
            {text}
          </span>
        );
      },
    },
    {
      title: '上传时间',
      dataIndex: 'upload_time',
      key: 'upload_time',
      render: (text: string) => new Date(text).toLocaleString(),
    },
    {
      title: '上传者',
      dataIndex: 'uploader',
      key: 'uploader',
    },
  ];

  useEffect(() => {
    fetchFiles();
    fetchStats();
  }, []);

  // 获取文件列表
  const fetchFiles = async () => {
    try {
      setLoading(true);
      const response = await fileAPI.getFiles();
      
      if (response.success) {
        setFiles(response.data || []);
      } else {
        message.error('获取文件列表失败');
      }
    } catch (error) {
      message.error('网络请求失败');
      console.error('获取文件列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取文件统计
  const fetchStats = async () => {
    try {
      const response = await fileAPI.getFileStats();
      
      if (response.success) {
        setStats(response.data || null);
      }
    } catch (error) {
      console.error('获取统计信息失败:', error);
    }
  };

  // 文件上传处理
  const handleUpload = async (file: File) => {
    setSelectedFile(file);
    setUploadModalVisible(true);
    return false; // 阻止自动上传
  };

  // 验证文件名
  const validateFilename = async (filename: string) => {
    try {
      const response = await fileAPI.validateFilename(filename);
      setValidationResult(response.data || null);
      setValidationModalVisible(true);
    } catch {
      message.error('验证失败');
    }
  };

  // 提交上传
  const handleSubmitUpload = async (values: { uploader: string }) => {
    if (!selectedFile) return;

    try {
    const formData = new FormData();
    formData.append('file', selectedFile);
      formData.append('uploader', values.uploader);

      const response = await fileAPI.uploadFile(formData);

      if (response.success) {
        message.success('文件上传成功');
        setUploadModalVisible(false);
        setSelectedFile(null);
        form.resetFields();
        fetchFiles();
        fetchStats();
      } else {
        message.error(response.error || '上传失败');
      }
    } catch (error) {
      message.error('上传失败');
      console.error('文件上传失败:', error);
    }
  };

  // 上传配置
  const uploadProps: UploadProps = {
    beforeUpload: handleUpload,
    showUploadList: false,
  };

  return (
    <div style={{ padding: 24 }}>
      <Title level={2}>文件视图</Title>

      {/* 文件统计 */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="文件总数"
                value={stats.total_files}
                prefix={<FileTextOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="规范文件"
                value={stats.compliant_files}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="非规范文件"
                value={stats.non_compliant_files}
                prefix={<ExclamationCircleOutlined />}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="规范率"
                value={stats.compliance_rate}
                suffix="%"
                valueStyle={{ color: stats.compliance_rate >= 80 ? '#52c41a' : '#faad14' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 操作按钮 */}
      <Card style={{ marginBottom: 24 }}>
        <Space>
          <Upload {...uploadProps}>
            <Button icon={<UploadOutlined />} type="primary">
              上传文件
            </Button>
          </Upload>
          <Button onClick={() => fetchFiles()}>
            刷新列表
          </Button>
        </Space>
      </Card>

      {/* 文件列表 */}
      <Card>
        <Table
          columns={columns}
          dataSource={files}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
        />
      </Card>

      {/* 上传文件模态框 */}
      <Modal
        title="上传文件"
        open={uploadModalVisible}
        onCancel={() => {
          setUploadModalVisible(false);
          setSelectedFile(null);
          form.resetFields();
        }}
        footer={null}
        width={500}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmitUpload}
        >
          <Form.Item label="选择的文件">
            <div style={{ 
              padding: 12, 
              background: '#f5f5f5', 
              borderRadius: 4,
              border: '1px dashed #d9d9d9'
            }}>
              {selectedFile?.name}
            </div>
          </Form.Item>
          
          <Form.Item
            name="uploader"
            label="上传者"
            rules={[{ required: true, message: '请输入上传者姓名' }]}
          >
            <Input placeholder="请输入上传者姓名" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                确认上传
              </Button>
              <Button onClick={() => validateFilename(selectedFile?.name || '')}>
                验证文件名
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 验证结果模态框 */}
      <Modal
        title="文件名验证结果"
        open={validationModalVisible}
        onCancel={() => setValidationModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setValidationModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={600}
      >
        {validationResult && (
          <div>
            <div style={{ 
              padding: 12, 
              background: validationResult.is_compliant ? '#f6ffed' : '#fff2f0',
              border: `1px solid ${validationResult.is_compliant ? '#b7eb8f' : '#ffccc7'}`,
              borderRadius: 4,
              marginBottom: 16
            }}>
              <div style={{ 
                color: validationResult.is_compliant ? '#52c41a' : '#ff4d4f',
                fontWeight: 'bold',
                marginBottom: 8
              }}>
                {validationResult.is_compliant ? '✅ 文件名符合规范' : '❌ 文件名不符合规范'}
                  </div>
            
            {validationResult.errors && validationResult.errors.length > 0 && (
                  <div>
                  <div style={{ fontWeight: 'bold', marginBottom: 4 }}>错误信息：</div>
                  <ul style={{ margin: 0, paddingLeft: 20 }}>
                  {validationResult.errors.map((error, index) => (
                    <li key={index} style={{ color: '#ff4d4f' }}>{error}</li>
                  ))}
                </ul>
                </div>
              )}
            </div>
            
            {validationResult.parsed_info && (
              <div>
                <div style={{ fontWeight: 'bold', marginBottom: 8 }}>解析结果：</div>
                <div style={{ 
                  background: '#f5f5f5', 
                  padding: 12, 
                  borderRadius: 4,
                  fontSize: 12
                }}>
                  <pre style={{ margin: 0 }}>
                    {JSON.stringify(validationResult.parsed_info, null, 2)}
                  </pre>
                </div>
                  </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}

export default FilesPage; 