// API接口文件
// 这个文件包含了前端与后端通信的所有API函数
// 使用fetch API进行HTTP请求，统一处理响应格式

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

// 通用响应接口
interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
}

// 员工映射接口
interface EmployeeMapping {
  id: number;
  wechat_nickname: string;
  real_name: string;
  position: string;
  name_abbreviation: string;
  created_at: string;
  updated_at: string;
}

// 项目接口
interface Project {
  id: number;
  project_name: string;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
}

// 文件记录接口
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

// 文件统计接口
interface FileStats {
  total_files: number;
  compliant_files: number;
  non_compliant_files: number;
  compliance_rate: number;
  recent_uploads: number;
}

// 仪表盘统计接口
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

// 验证结果接口
interface ValidationResult {
  is_compliant: boolean;
  parsed_info?: Record<string, unknown>;
  errors?: string[];
}

// 同步相关接口
interface SyncStatus {
  status: string;
  message: string;
  timestamp: string;
  api_base: string;
}

interface Chatroom {
  id: string;
  name: string;
  member_count?: number;
  created_at?: string;
}

interface SyncRequest {
  start_date: string;
  end_date: string;
  sync_type?: 'all' | 'chat' | 'files';
  chatroom_names?: string[];
}

interface SyncResult {
  project_id?: number;
  project_name?: string;
  start_date: string;
  end_date: string;
  sync_type: string;
  total_chatrooms: number;
  success_count: number;
  failed_count: number;
  total_messages: number;
  total_files: number;
  details: Array<{
    chatroom_name: string;
    message_count?: number;
    status: string;
    error?: string;
    first_message_time?: string;
    last_message_time?: string;
  }>;
  timestamp: string;
}

interface SyncResponse {
  results: SyncResult;
  log: string[];
}

// 通用API请求函数
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    // 保证所有endpoint以/结尾，防止Flask 308重定向
    const fixedEndpoint = endpoint;
    const url = `${API_BASE_URL}${fixedEndpoint}`;
    const response = await fetch(url, {
      redirect: 'follow',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('API请求失败:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : '未知错误',
    };
  }
}

// 员工管理API
export const employeeAPI = {
  // 获取员工列表
  getEmployees: () => apiRequest<EmployeeMapping[]>('/api/v1/employees/'),

  // 添加员工
  addEmployee: (employee: {
    wechat_nickname: string;
    real_name: string;
    position?: string;
    name_abbreviation: string;
  }) =>
    apiRequest('/api/v1/employees/', {
      method: 'POST',
      body: JSON.stringify(employee),
    }),

  // 更新员工
  updateEmployee: (id: number, employee: Partial<EmployeeMapping>) =>
    apiRequest(`/api/v1/employees/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(employee),
    }),

  // 删除员工
  deleteEmployee: (id: number) =>
    apiRequest(`/api/v1/employees/${id}`, {
      method: 'DELETE',
    }),
};

// 项目管理API
export const projectAPI = {
  // 获取项目列表
  getProjects: () => apiRequest<Project[]>('/api/v1/projects/'),

  // 添加项目
  addProject: (project: {
    project_name: string;
    description?: string;
  }) =>
    apiRequest('/api/v1/projects/', {
      method: 'POST',
      body: JSON.stringify(project),
    }),

  // 更新项目
  updateProject: (id: number, project: Partial<Project>) =>
    apiRequest(`/api/v1/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(project),
    }),

  // 删除项目
  deleteProject: (id: number) =>
    apiRequest(`/api/v1/projects/${id}`, {
      method: 'DELETE',
    }),
};

// 文件管理API
export const fileAPI = {
  // 获取文件列表
  getFiles: () => apiRequest<FileRecord[]>('/api/v1/files/'),

  // 获取文件统计
  getFileStats: () => apiRequest<FileStats>('/api/v1/files/stats'),

  // 验证文件名
  validateFilename: (filename: string) =>
    apiRequest<ValidationResult>('/api/v1/files/validate', {
      method: 'POST',
      body: JSON.stringify({ filename }),
    }),

  // 批量验证文件名
  validateFilenames: (filenames: string[]) =>
    apiRequest<ValidationResult[]>('/api/v1/files/validate-batch', {
      method: 'POST',
      body: JSON.stringify({ filenames }),
    }),

  // 上传文件
  uploadFile: (formData: FormData) => {
    const url = `${API_BASE_URL}/api/v1/files/upload`;
    return fetch(url, {
      method: 'POST',
      body: formData,
    }).then(response => response.json());
  },
};

// 仪表盘API
export const dashboardAPI = {
  // 获取仪表盘统计
  getStats: () => apiRequest<DashboardStats>('/api/v1/dashboard/stats'),

  // 获取健康状态
  getHealth: () => apiRequest('/api/health'),

  // 获取员工排行榜
  getEmployeeRanking: () => apiRequest<EmployeeRanking[]>('/api/v1/dashboard/employee-ranking'),

  // 获取负面反馈
  getNegativeFeedback: () => apiRequest<NegativeFeedback[]>('/api/v1/dashboard/negative-feedback'),

  // 获取近期动态
  getRecentActivity: () => apiRequest<RecentActivity[]>('/api/v1/dashboard/recent-activities'),
};

// 同步管理API
export const syncAPI = {
  // 获取同步状态
  getStatus: () => apiRequest<SyncStatus>('/api/v1/sync/status'),

  // 获取群聊列表
  getChatrooms: () => apiRequest<Chatroom[]>('/api/v1/sync/chatrooms'),

  // 测试 chatlog 连接
  testConnection: () => apiRequest('/api/v1/sync/test'),

  // 同步指定项目数据
  syncProject: (projectId: number, syncRequest: SyncRequest) =>
    apiRequest<SyncResponse>(`/api/v1/sync/project/${projectId}`, {
      method: 'POST',
      body: JSON.stringify(syncRequest),
    }),

  // 通用数据同步
  syncData: (syncRequest: SyncRequest) =>
    apiRequest<SyncResponse>('/api/v1/sync/', {
      method: 'POST',
      body: JSON.stringify(syncRequest),
    }),
};

// 聊天记录API
export const chatlogAPI = {
  // 获取聊天记录状态
  getStatus: () => apiRequest('/api/v1/chatlog/status'),

  // 获取聊天室列表
  getChatrooms: () => apiRequest('/api/v1/chatroom'),

  // 获取联系人列表
  getContacts: () => apiRequest('/api/v1/chatlog/contacts'),

  // 获取会话列表
  getSessions: () => apiRequest('/api/v1/chatlog/sessions'),

  // 获取消息列表
  getMessages: (params?: {
    group_name?: string;
    sender_name?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.group_name) searchParams.append('group_name', params.group_name);
    if (params?.sender_name) searchParams.append('sender_name', params.sender_name);
    if (params?.start_date) searchParams.append('start_date', params.start_date);
    if (params?.end_date) searchParams.append('end_date', params.end_date);
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    
    const queryString = searchParams.toString();
    const endpoint = `/api/v1/chatlog/messages${queryString ? `?${queryString}` : ''}`;
    return apiRequest(endpoint);
  },

  // 同步聊天记录
  syncChatlogs: () =>
    apiRequest('/api/v1/chatlog/sync', {
      method: 'POST',
    }),
};