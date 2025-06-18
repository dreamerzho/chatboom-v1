# 广告公司服务监测软件 - API接口文档

## 📋 概述

本文档记录了广告公司服务监测软件的所有API接口，所有接口均使用v1版本，确保版本统一。

**基础信息：**
- **后端服务地址**: `http://127.0.0.1:5000`
- **API版本**: `v1`
- **数据格式**: JSON
- **字符编码**: UTF-8

---

## 🔧 系统管理接口

### 健康检查
- **接口**: `GET /api/v1/health`
- **描述**: 检查服务运行状态
- **响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "service": "广告公司服务监测系统后端"
}
```

### 根路径信息
- **接口**: `GET /`
- **描述**: 获取服务基本信息
- **响应示例**:
```json
{
  "service": "广告公司服务监测系统后端",
  "version": "1.0.0",
  "status": "running",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "endpoints": {
    "health": "/api/health",
    "employees": "/api/v1/employees",
    "projects": "/api/v1/projects",
    "files": "/api/v1/files",
    "chatlog": "/api/v1/chatlog"
  }
}
```

---

## 👥 员工管理接口

### 获取员工列表
- **接口**: `GET /api/v1/employees`
- **描述**: 获取所有员工映射信息
- **响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "wechat_nickname": "设计师小张",
      "real_name": "张三",
      "position": "设计师",
      "name_abbreviation": "ZS",
      "wechat_id": "wxid_zhangsan",
      "created_at": "2024-01-15T10:30:00.000Z",
      "updated_at": "2024-01-15T10:30:00.000Z"
    }
  ]
}
```

### 添加员工
- **接口**: `POST /api/v1/employees`
- **描述**: 添加新的员工映射
- **请求体**:
```json
{
  "wechat_nickname": "设计师小张",
  "real_name": "张三",
  "position": "设计师",
  "name_abbreviation": "ZS",
  "wechat_id": "wxid_zhangsan"
}
```
- **响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 1
  }
}
```

---

## 📁 项目管理接口

### 获取项目列表
- **接口**: `GET /api/v1/projects`
- **描述**: 获取所有项目信息
- **响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "project_name": "建杭良渚",
      "description": "建杭良渚项目",
      "status": "active",
      "created_at": "2024-01-15T10:30:00.000Z",
      "updated_at": "2024-01-15T10:30:00.000Z",
      "internal_group_name": "建杭良渚内部群",
      "external_group_name": "建杭良渚外部群"
    }
  ]
}
```

---

## 📄 文件管理接口

### 获取文件列表
- **接口**: `GET /api/v1/files/list`
- **描述**: 获取文件记录列表
- **查询参数**:
  - `status`: 文件状态筛选 (compliant/non-compliant/pending/all)
  - `project_name`: 项目名称筛选
  - `uploader`: 上传者筛选
- **响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "original_name": "240115-建杭良渚-设计方案-8h-ZS-v1.0.pdf",
      "standardized_name": "240115-建杭良渚-设计方案-8h-ZS-v1.0.pdf",
      "project_name": "建杭良渚",
      "work_order": "设计方案",
      "workload": "8h",
      "author_abbreviation": "ZS",
      "version": "v1.0",
      "file_extension": "pdf",
      "upload_time": "2024-01-15T10:30:00.000Z",
      "uploader": "张三",
      "file_size": "1024 bytes",
      "status": "compliant"
    }
  ]
}
```

### 获取文件统计
- **接口**: `GET /api/v1/files/stats`
- **描述**: 获取文件统计信息
- **响应示例**:
```json
{
  "success": true,
  "data": {
    "total_files": 100,
    "compliant_files": 85,
    "non_compliant_files": 10,
    "pending_files": 5,
    "compliance_rate": 85.0,
    "project_stats": [
      {
        "project_name": "建杭良渚",
        "total_count": 50,
        "compliant_count": 45,
        "compliance_rate": 90.0
      }
    ],
    "uploader_stats": [
      {
        "uploader": "张三",
        "total_count": 30,
        "compliant_count": 28,
        "compliance_rate": 93.3
      }
    ]
  }
}
```

### 验证文件名
- **接口**: `POST /api/v1/files/validate`
- **描述**: 检查单个文件名是否符合规范
- **请求体**:
```json
{
  "filename": "240115-建杭良渚-设计方案-8h-ZS-v1.0.pdf"
}
```
- **响应示例**:
```json
{
  "success": true,
  "data": {
    "is_compliant": true,
    "parsed_info": {
      "date": "240115",
      "project_name": "建杭良渚",
      "work_order": "设计方案",
      "workload": "8h",
      "author_abbreviation": "ZS",
      "version": "v1.0",
      "extension": "pdf"
    }
  }
}
```

### 批量验证文件名
- **接口**: `POST /api/v1/files/validate-batch`
- **描述**: 批量检查文件名是否符合规范
- **请求体**:
```json
{
  "filenames": [
    "240115-建杭良渚-设计方案-8h-ZS-v1.0.pdf",
    "240115-星润-项目计划-12h-LS-v2.0.xlsx"
  ]
}
```
- **响应示例**:
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "filename": "240115-建杭良渚-设计方案-8h-ZS-v1.0.pdf",
        "is_compliant": true,
        "parsed_info": {...}
      }
    ],
    "summary": {
      "total": 2,
      "compliant": 2,
      "non_compliant": 0,
      "compliance_rate": 100.0
    }
  }
}
```

### 上传文件
- **接口**: `POST /api/v1/files/upload`
- **描述**: 上传文件并检查命名规范
- **请求体**: `multipart/form-data`
  - `file`: 文件内容
  - `uploader`: 上传者姓名
- **响应示例**:
```json
{
  "success": true,
  "data": {
    "message": "文件上传成功并已入库",
    "validation": {
      "is_compliant": true,
      "parsed_info": {...}
    },
    "file_id": 1
  }
}
```

---

## 💬 聊天记录接口

### 检查服务状态
- **接口**: `GET /api/v1/chatlog/status`
- **描述**: 检查chatlog服务状态
- **响应示例**:
```json
{
  "status": "running",
  "version": "0.0.15",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### 获取群聊列表
- **接口**: `GET /api/v1/chatlog/chatrooms`
- **描述**: 获取所有微信群聊列表
- **响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": "wxid_123456",
      "name": "建杭良渚外部",
      "memberCount": 15
    }
  ],
  "count": 1,
  "message": "成功获取到 1 个群聊"
}
```

### 获取联系人列表
- **接口**: `GET /api/v1/chatlog/contacts`
- **描述**: 获取所有联系人列表
- **响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": "wxid_user1",
      "name": "张三",
      "nickname": "设计师小张"
    }
  ],
  "count": 1,
  "message": "成功获取到 1 个联系人"
}
```

### 获取会话列表
- **接口**: `GET /api/v1/chatlog/sessions`
- **描述**: 获取最近会话列表
- **响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": "session1",
      "name": "建杭良渚外部",
      "lastMessage": "好的，收到",
      "lastTime": "2024-01-15 14:30:00"
    }
  ],
  "count": 1,
  "message": "成功获取到 1 个会话"
}
```

### 获取聊天记录
- **接口**: `GET /api/v1/chatlog/messages`
- **描述**: 获取聊天记录
- **查询参数**:
  - `talker`: 聊天对象标识
  - `time_range`: 时间范围 (YYYY-MM-DD 或 YYYY-MM-DD~YYYY-MM-DD)
  - `limit`: 返回记录数量限制 (默认100)
  - `offset`: 分页偏移量 (默认0)
  - `format`: 输出格式 (json/csv/text，默认json)
- **响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "seq": "msg_1",
      "senderName": "张三",
      "type": "1",
      "time": "2024-01-15T14:30:00.000Z",
      "content": "好的，收到"
    }
  ],
  "count": 1,
  "params": {
    "talker": "建杭良渚外部",
    "time_range": "2024-01-15",
    "limit": 100,
    "offset": 0,
    "format": "json"
  },
  "message": "成功获取到 1 条聊天记录"
}
```

### 获取多媒体内容
- **接口**: `GET /api/v1/chatlog/media`
- **描述**: 获取多媒体消息内容
- **查询参数**:
  - `msgid`: 消息ID
- **响应示例**:
```json
{
  "success": true,
  "data": {
    "msgid": "msg_123",
    "type": "image",
    "url": "http://127.0.0.1:5030/media/msg_123.jpg",
    "size": 1024,
    "filename": "media_msg_123.jpg"
  },
  "message": "成功获取多媒体内容"
}
```

### 获取最近聊天记录
- **接口**: `GET /api/v1/chatlog/recent`
- **描述**: 获取最近几天的聊天记录
- **查询参数**:
  - `days`: 天数 (默认7天)
- **响应示例**:
```json
{
  "success": true,
  "data": [...],
  "count": 50,
  "params": {"days": 7},
  "message": "成功获取最近 7 天的 50 条聊天记录"
}
```

### 同步聊天记录
- **接口**: `POST /api/v1/chatlog/sync`
- **描述**: 同步所有群聊的聊天记录
- **响应示例**:
```json
{
  "success": true,
  "data": {
    "success_count": 5,
    "failed_count": 0,
    "details": [...]
  },
  "message": "同步完成，成功处理 5 个群聊，失败 0 个"
}
```

### 同步指定项目聊天记录
- **接口**: `POST /api/v1/chatlogs/sync`
- **描述**: 手动同步指定项目的聊天记录
- **请求体**:
```json
{
  "project_id": 1,
  "start": "2024-01-01",
  "end": "2024-01-15"
}
```
- **响应示例**:
```json
{
  "success": true,
  "data": {
    "count": 1000
  }
}
```

### 获取项目聊天记录
- **接口**: `GET /api/v1/projects/{project_id}/chatlogs`
- **描述**: 查询指定项目的聊天记录
- **查询参数**:
  - `start`: 开始日期
  - `end`: 结束日期
  - `group`: 群类型 (internal/external)
  - `keyword`: 关键词筛选
- **响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "time": "2024-01-15 14:30",
      "sender": "张三",
      "content": "好的，收到",
      "type": "1",
      "file_name": null
    }
  ]
}
```

---

## 📊 仪表盘接口

### 获取统计数据
- **接口**: `GET /api/v1/dashboard/stats`
- **描述**: 获取仪表盘统计数据
- **响应示例**:
```json
{
  "success": true,
  "data": {
    "total_employees": 10,
    "active_projects": 5,
    "total_files": 100,
    "compliant_files": 85,
    "recent_files": [
      {
        "date": "2024-01-15",
        "count": 5
      }
    ]
  }
}
```

---

## 🔄 向后兼容接口

为了保持向后兼容，以下旧版本接口会自动重定向到v1版本：

- `GET /api/health` → `GET /api/v1/health`
- `GET /api/employees` → `GET /api/v1/employees`
- `POST /api/employees` → `POST /api/v1/employees`
- `GET /api/projects` → `GET /api/v1/projects`

---

## 📝 错误响应格式

所有接口在发生错误时都会返回统一的错误格式：

```json
{
  "success": false,
  "error": "错误描述信息"
}
```

常见HTTP状态码：
- `200`: 请求成功
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

---

## 🔧 前端API客户端

前端使用统一的API客户端库 (`src/lib/api.ts`) 来调用这些接口，确保：

1. **版本统一**: 所有接口都使用v1版本
2. **错误处理**: 统一的错误处理机制
3. **类型安全**: TypeScript类型定义
4. **请求配置**: 统一的请求头和配置

---

## 📋 更新日志

### v1.0.0 (2024-01-15)
- ✅ 统一所有API接口为v1版本
- ✅ 添加完整的接口文档
- ✅ 实现向后兼容重定向
- ✅ 更新前端API客户端库
- ✅ 修复接口版本不一致问题 