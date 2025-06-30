// 员工详情页面
// 展示单个员工的详细信息、工作统计、文件记录等，暂时使用模拟数据

'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { employeeAPI } from '@lib/api';

// 定义员工详情类型
interface EmployeeDetail {
  id: number;
  real_name: string;
  position: string;
  wechat_nickname: string;
  name_abbreviation: string;
  join_date: string;
  total_messages: number;
  total_files: number;
  compliant_files: number;
  recent_activities: Activity[];
}

interface Activity {
  id: number;
  type: 'message' | 'file';
  content: string;
  time: string;
  project_name?: string;
}

function EmployeePage() {
  const params = useParams();
  const employeeId = params?.id ? Number(params.id) : null;
  const [employee, setEmployee] = useState<EmployeeDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!employeeId) {
      setError('未指定员工ID');
      setLoading(false);
      return;
    }
    setLoading(true);
    employeeAPI.getEmployee(employeeId)
      .then((res: { success: boolean; data?: any; error?: string }) => {
        if (res.success && res.data) {
          setEmployee({
            id: res.data.id,
            real_name: res.data.real_name,
            position: res.data.position,
            wechat_nickname: res.data.wechat_nickname,
            name_abbreviation: res.data.name_abbreviation,
            join_date: res.data.created_at || '',
            total_messages: typeof res.data.total_messages === 'number' ? res.data.total_messages : 0,
            total_files: typeof res.data.total_files === 'number' ? res.data.total_files : 0,
            compliant_files: typeof res.data.compliant_files === 'number' ? res.data.compliant_files : 0,
            recent_activities: Array.isArray(res.data.recent_activities) ? res.data.recent_activities : [],
          });
          setError(null);
        } else {
          setError(res.error || '未找到员工信息');
        }
        setLoading(false);
      })
      .catch((e: Error) => {
        setError(e.message || '获取员工信息失败');
      setLoading(false);
      });
  }, [employeeId]);

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ marginBottom: 32, color: '#1890ff' }}>员工详情</h1>
      
      {loading && (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <div style={{ fontSize: 16, color: '#666' }}>加载中...</div>
        </div>
      )}
      
      {error && (
        <div style={{ 
          background: '#fff2f0', 
          border: '1px solid #ffccc7', 
          padding: 16, 
          borderRadius: 6,
          marginBottom: 24
        }}>
          <div style={{ color: '#cf1322', fontWeight: 'bold' }}>加载失败</div>
          <div style={{ color: '#666' }}>{error}</div>
        </div>
      )}
      
      {!loading && !error && employee && (
        <>
          {/* 员工基本信息 */}
          <div style={{ 
            background: 'white', 
            padding: 24, 
            borderRadius: 8, 
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            marginBottom: 24
          }}>
            <h2 style={{ marginBottom: 24, color: '#1890ff' }}>基本信息</h2>
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
              gap: 16 
            }}>
              <div>
                <div style={{ color: '#666', fontSize: 14 }}>姓名</div>
                <div style={{ fontSize: 18, fontWeight: 'bold', marginTop: 4 }}>
                  {employee.real_name}
                </div>
              </div>
              <div>
                <div style={{ color: '#666', fontSize: 14 }}>岗位</div>
                <div style={{ fontSize: 18, fontWeight: 'bold', marginTop: 4 }}>
                  {employee.position}
                </div>
              </div>
              <div>
                <div style={{ color: '#666', fontSize: 14 }}>微信昵称</div>
                <div style={{ fontSize: 18, fontWeight: 'bold', marginTop: 4 }}>
                  {employee.wechat_nickname}
                </div>
              </div>
              <div>
                <div style={{ color: '#666', fontSize: 14 }}>姓名缩写</div>
                <div style={{ fontSize: 18, fontWeight: 'bold', marginTop: 4 }}>
                  <span style={{ 
                    background: '#52c41a', 
                    color: 'white', 
                    padding: '4px 8px', 
                    borderRadius: 4,
                    fontSize: 14
                  }}>
                    {employee.name_abbreviation}
                  </span>
                </div>
              </div>
              <div>
                <div style={{ color: '#666', fontSize: 14 }}>入职时间</div>
                <div style={{ fontSize: 18, fontWeight: 'bold', marginTop: 4 }}>
                  {employee.join_date}
                </div>
              </div>
            </div>
          </div>

          {/* 工作统计 */}
          <div style={{ 
            background: 'white', 
            padding: 24, 
            borderRadius: 8, 
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            marginBottom: 24
          }}>
            <h2 style={{ marginBottom: 24, color: '#1890ff' }}>工作统计</h2>
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
              gap: 16 
            }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 32, fontWeight: 'bold', color: '#1890ff' }}>
                  {employee.total_messages}
                </div>
                <div style={{ color: '#666', marginTop: 8 }}>总消息数</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 32, fontWeight: 'bold', color: '#52c41a' }}>
                  {employee.total_files}
                </div>
                <div style={{ color: '#666', marginTop: 8 }}>总文件数</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 32, fontWeight: 'bold', color: '#fa8c16' }}>
                  {employee.compliant_files}
                </div>
                <div style={{ color: '#666', marginTop: 8 }}>合规文件</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 32, fontWeight: 'bold', color: '#722ed1' }}>
                  {Math.round((employee.compliant_files / employee.total_files) * 100)}%
                </div>
                <div style={{ color: '#666', marginTop: 8 }}>合规率</div>
              </div>
            </div>
          </div>

          {/* 近期活动 */}
          <div style={{ 
            background: 'white', 
            padding: 24, 
            borderRadius: 8, 
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}>
            <h2 style={{ marginBottom: 24, color: '#1890ff' }}>近期活动</h2>
            <div>
              {employee.recent_activities.map((activity) => (
                  <div key={activity.id} style={{ 
                  display: 'flex', 
                  alignItems: 'flex-start',
                    padding: '16px 0', 
                  borderBottom: '1px solid #f0f0f0'
                  }}>
                    <div style={{ 
                      width: 40, 
                      height: 40, 
                      borderRadius: '50%', 
                      background: activity.type === 'file' ? '#52c41a' : '#1890ff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      marginRight: 16,
                      flexShrink: 0
                    }}>
                    <span style={{ color: 'white', fontSize: 16 }}>
                      {activity.type === 'file' ? '📁' : '💬'}
                    </span>
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 'bold', marginBottom: 4 }}>
                        {activity.content}
                      </div>
                    <div style={{ color: '#666', fontSize: 12 }}>
                        {activity.time}
                        {activity.project_name && (
                        <span style={{ marginLeft: 8, color: '#1890ff' }}>
                          [{activity.project_name}]
                          </span>
                        )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default EmployeePage; 