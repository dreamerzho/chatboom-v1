# 广告公司服务监测软件 - API接口文档

## 概述
本文档描述了广告公司服务监测软件的后端API接口，主要用于员工管理、项目管理和数据分析。

## 基础信息
- **基础URL**: `http://localhost:5000`
- **API版本**: v1
- **数据格式**: JSON
- **字符编码**: UTF-8

## 通用响应格式
所有API接口都遵循统一的响应格式：

### 成功响应
```json
{
  "success": true,
  "data": {...},
  "message": "操作成功" // 可选
}
```

### 错误响应
```json
{
  "success": false,
  "error": "错误描述"
}
```

## 员工管理API (Employee Management)

### 1. 获取员工列表
**接口**: `GET /api/v1/employees/`

**描述**: 获取所有员工映射列表

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "wechat_nickname": "张三",
      "real_name": "张三",
      "position": "设计师",
      "name_abbreviation": "ZS",
      "role": "员工",
      "created_at": "2025-06-17T15:25:12.531551",
      "updated_at": "2025-06-17T15:25:12.533051"
    }
  ]
}
```

### 2. 创建员工映射
**接口**: `POST /api/v1/employees/`

**描述**: 创建新的员工映射

**请求体**:
```json
{
  "wechat_nickname": "张三",
  "real_name": "张三",
  "position": "设计师",
  "name_abbreviation": "ZS",
  "role": "员工"
}
```

**必填字段**:
- `wechat_nickname`: 微信昵称
- `real_name`: 真实姓名
- `position`: 岗位
- `name_abbreviation`: 姓名缩写

**可选字段**:
- `role`: 角色（默认为"员工"）

### 3. 更新员工映射
**接口**: `PUT /api/v1/employees/{employee_id}`

**描述**: 更新指定员工的映射信息

**请求体**: 同创建员工映射，但所有字段都是可选的

### 4. 删除员工映射
**接口**: `DELETE /api/v1/employees/{employee_id}`

**描述**: 删除指定的员工映射

### 5. 获取员工统计
**接口**: `GET /api/v1/employees/{employee_id}/stats`

**描述**: 获取指定员工的工作统计数据

**查询参数**:
- `start_date`: 开始日期（ISO格式，可选）
- `end_date`: 结束日期（ISO格式，可选）

**响应示例**:
```json
{
  "success": true,
  "data": {
    "employee_info": {
      "id": 1,
      "wechat_nickname": "张三",
      "real_name": "张三",
      "position": "设计师",
      "role": "员工"
    },
    "message_stats": {
      "total_messages": 150,
      "text_messages": 120,
      "image_messages": 20,
      "file_messages": 10,
      "avg_messages_per_day": 15.0
    },
    "activity_stats": {
      "active_days": 10,
      "latest_activity": "2025-06-17T10:30:00"
    },
    "project_stats": [
      {
        "project_id": 1,
        "project_name": "项目A",
        "message_count": 80
      }
    ],
    "time_range": {
      "start_date": null,
      "end_date": null
    }
  }
}
```

### 6. 获取员工统计概览
**接口**: `GET /api/v1/employees/stats/overview`

**描述**: 获取所有员工的统计概览

**查询参数**:
- `start_date`: 开始日期（ISO格式，可选）
- `end_date`: 结束日期（ISO格式，可选）

**响应示例**:
```json
{
  "success": true,
  "data": {
    "employees": [
      {
        "employee_id": 1,
        "wechat_nickname": "张三",
        "real_name": "张三",
        "position": "设计师",
        "role": "员工",
        "total_messages": 150,
        "file_messages": 10,
        "active_days": 10,
        "latest_activity": "2025-06-17T10:30:00"
      }
    ],
    "summary": {
      "total_employees": 2,
      "total_messages": 250,
      "total_files": 15,
      "total_active_days": 20,
      "avg_messages_per_employee": 125.0
    },
    "time_range": {
      "start_date": null,
      "end_date": null
    }
  }
}
```

### 7. 获取未映射用户列表
**接口**: `GET /api/v1/employees/unmapped`

**描述**: 获取所有在聊天记录中出现但未被映射的微信昵称

**响应示例**:
```json
{
  "success": true,
  "data": {
    "unmapped_senders": [
      {
        "sender_name": "未知用户1",
        "message_count": 25
      }
    ],
    "total_count": 1,
    "mapped_count": 2,
    "total_senders": 3
  }
}
```

### 8. 批量添加未映射用户
**接口**: `POST /api/v1/employees/unmapped/batch-add`

**描述**: 批量添加未映射用户为员工

**请求体**:
```json
{
  "senders": [
    {
      "sender_name": "未知用户1",
      "real_name": "王五",
      "position": "开发工程师",
      "name_abbreviation": "WW",
      "role": "员工"
    }
  ]
}
```

### 9. 批量导入员工
**接口**: `POST /api/v1/employees/batch-import`

**描述**: 批量导入员工映射（支持JSON格式）

**请求体**:
```json
{
  "employees": [
    {
      "wechat_nickname": "张三",
      "real_name": "张三",
      "position": "设计师",
      "name_abbreviation": "ZS",
      "role": "员工"
    }
  ]
}
```

### 10. 导出员工数据
**接口**: `GET /api/v1/employees/export`

**描述**: 导出员工映射数据

**响应示例**:
```json
{
  "success": true,
  "data": [...],
  "export_time": "2025-06-17T15:25:21.199856",
  "total_count": 2
}
```

## 项目管理API (Project Management)

### 1. 获取项目列表
**接口**: `GET /api/v1/projects/`

**描述**: 获取所有项目列表

### 2. 创建项目
**接口**: `POST /api/v1/projects/`

**描述**: 创建新项目

**请求体**:
```json
{
  "project_name": "项目A",
  "description": "项目描述",
  "status": "进行中"
}
```

### 3. 获取项目详情
**接口**: `GET /api/v1/projects/{project_id}`

**描述**: 获取指定项目的详细信息

### 4. 更新项目
**接口**: `PUT /api/v1/projects/{project_id}`

**描述**: 更新项目信息

### 5. 删除项目
**接口**: `DELETE /api/v1/projects/{project_id}`

**描述**: 删除项目

## 文件管理API (File Management)

### 1. 获取文件列表
**接口**: `GET /api/v1/files/list`

**描述**: 获取文件记录列表

### 2. 获取文件统计
**接口**: `GET /api/v1/files/stats`

**描述**: 获取文件统计信息

## 仪表盘API (Dashboard)

### 1. 获取仪表盘统计
**接口**: `GET /api/v1/dashboard/stats`

**描述**: 获取仪表盘统计数据

## 健康检查API (Health Check)

### 1. 健康检查
**接口**: `GET /api/health`

**描述**: 检查服务健康状态

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2025-06-17T15:25:21.199856",
  "version": "1.0.0"
}
```

## 错误代码说明

### HTTP状态码
- `200`: 请求成功
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

### 常见错误信息
- `缺少请求数据`: 请求体为空或格式错误
- `缺少必填字段`: 缺少必需的字段
- `该微信昵称已存在`: 微信昵称重复
- `员工不存在`: 指定的员工ID不存在
- `开始日期格式错误`: 日期格式不正确

## 使用示例

### 创建员工映射
```bash
curl -X POST http://localhost:5000/api/v1/employees/ \
  -H "Content-Type: application/json" \
  -d '{
    "wechat_nickname": "张三",
    "real_name": "张三",
    "position": "设计师",
    "name_abbreviation": "ZS",
    "role": "员工"
  }'
```

### 获取员工统计
```bash
curl "http://localhost:5000/api/v1/employees/1/stats?start_date=2025-06-01&end_date=2025-06-17"
```

### 批量导入员工
```bash
curl -X POST http://localhost:5000/api/v1/employees/batch-import \
  -H "Content-Type: application/json" \
  -d '{
    "employees": [
      {
        "wechat_nickname": "张三",
        "real_name": "张三",
        "position": "设计师",
        "name_abbreviation": "ZS"
      }
    ]
  }'
```

## 注意事项

1. **数据格式**: 所有日期时间字段使用ISO 8601格式
2. **字符编码**: 支持中文字符，使用UTF-8编码
3. **分页**: 目前所有列表接口返回全部数据，后续可添加分页功能
4. **权限**: 当前版本未实现权限控制，后续可添加用户认证和授权
5. **数据验证**: 所有输入数据都会进行格式验证
6. **错误处理**: 所有接口都有完整的错误处理机制

## 更新日志

### v1.0.0 (2025-06-17)
- 实现员工管理基础功能
- 实现项目管理基础功能
- 实现文件管理基础功能
- 实现仪表盘统计功能
- 实现未映射用户管理功能
- 实现批量导入导出功能 