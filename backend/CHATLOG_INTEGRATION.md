# Chatlog工具集成功能说明

## 概述

本模块实现了与chatlog工具的API集成，可以自动拉取和解析微信群聊记录，实现工作量化、质量监控和数字资产管理的核心目标。

## 功能特性

### 1. 状态检查
- 检查chatlog工具是否正常运行
- 验证API连接状态
- 获取服务健康信息

### 2. 群聊管理
- 获取所有可用的群聊列表
- 查看群聊基本信息
- 支持群聊筛选和搜索

### 3. 数据同步
- 自动同步指定群聊的聊天记录
- 支持时间范围筛选（最近N天）
- 批量同步所有群聊数据
- 避免重复数据导入

### 4. 数据导出
- 导出指定群聊的聊天记录
- 支持JSON格式输出
- 可指定时间范围

### 5. 数据查询
- 分页查询聊天记录
- 支持多维度筛选（群聊、发送者、消息类型、时间）
- 实时统计信息

## API接口说明

### 1. 检查chatlog状态
```http
GET /api/v1/chatlog/status?chatlog_url=http://localhost:8080
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "status": "running",
    "message": "chatlog工具运行正常",
    "response": {
      "version": "1.0.0",
      "uptime": "2h30m"
    }
  }
}
```

### 2. 获取群聊列表
```http
GET /api/v1/chatlog/groups?chatlog_url=http://localhost:8080
```

**响应示例：**
```json
{
  "success": true,
  "data": [
    {
      "name": "建杭良渚外部",
      "member_count": 15,
      "last_message_time": "2024-01-15T10:30:00Z"
    }
  ],
  "message": "成功获取到 1 个群聊"
}
```

### 3. 同步指定群聊数据
```http
POST /api/v1/chatlog/sync
Content-Type: application/json

{
  "group_name": "建杭良渚外部",
  "days_back": 7,
  "chatlog_url": "http://localhost:8080"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "成功同步群聊 建杭良渚外部 的聊天记录",
  "stats": {
    "total_messages": 150,
    "text_messages": 120,
    "file_messages": 25,
    "image_messages": 3,
    "video_messages": 2,
    "parsed_files": 20,
    "errors": 0
  },
  "export_count": 150
}
```

### 4. 同步所有群聊数据
```http
POST /api/v1/chatlog/sync-all
Content-Type: application/json

{
  "days_back": 7,
  "chatlog_url": "http://localhost:8080"
}
```

### 5. 导出聊天记录
```http
POST /api/v1/chatlog/export
Content-Type: application/json

{
  "group_name": "建杭良渚外部",
  "start_time": "2024-01-08 00:00:00",
  "end_time": "2024-01-15 23:59:59",
  "chatlog_url": "http://localhost:8080"
}
```

### 6. 获取聊天记录列表
```http
GET /api/v1/chatlog/messages?group_name=建杭良渚外部&page=1&per_page=50
```

**查询参数：**
- `group_name`: 群聊名称（可选）
- `sender_name`: 发送者昵称（可选）
- `message_type`: 消息类型（text/file/image/video，可选）
- `start_date`: 开始日期（可选）
- `end_date`: 结束日期（可选）
- `page`: 页码（默认1）
- `per_page`: 每页数量（默认50）

### 7. 获取聊天统计信息
```http
GET /api/v1/chatlog/stats
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "total_messages": 1500,
    "message_types": {
      "text": 1200,
      "file": 250,
      "image": 30,
      "video": 20
    },
    "group_stats": [
      {
        "group_name": "建杭良渚外部",
        "total_messages": 800,
        "text_messages": 650,
        "file_messages": 120,
        "image_messages": 20,
        "video_messages": 10
      }
    ],
    "sender_stats": [
      {
        "sender_name": "张三",
        "total_messages": 200,
        "text_messages": 180,
        "file_messages": 20
      }
    ],
    "recent_trend": [
      {
        "date": "2024-01-15",
        "count": 150
      }
    ]
  }
}
```

## 使用步骤

### 1. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动chatlog工具
确保chatlog工具在指定端口（默认8080）运行，并能够响应API请求。

### 3. 启动后端服务
```bash
cd backend
python app.py
```

### 4. 测试集成功能
```bash
cd backend
python test_chatlog_integration.py
```

## 配置说明

### chatlog工具配置
- **默认地址**: `http://localhost:8080`
- **健康检查路径**: `/health`
- **群聊列表路径**: `/api/groups`
- **导出数据路径**: `/api/export`

### 数据库配置
- 聊天记录存储在 `chat_messages` 表中
- 支持消息去重（基于message_id）
- 自动解析文件信息并存储

### 时间配置
- 默认同步最近7天的数据
- 支持自定义时间范围
- 时间格式：`YYYY-MM-DD HH:MM:SS`

## 错误处理

### 常见错误及解决方案

1. **连接超时**
   - 检查chatlog工具是否启动
   - 验证网络连接
   - 确认端口配置

2. **API响应异常**
   - 检查chatlog工具版本兼容性
   - 验证API路径是否正确
   - 查看chatlog工具日志

3. **数据解析失败**
   - 检查聊天记录格式
   - 验证JSON数据结构
   - 查看错误日志

## 性能优化

### 1. 批量处理
- 支持批量同步多个群聊
- 避免重复数据导入
- 优化数据库操作

### 2. 分页查询
- 支持大数据量分页
- 减少内存占用
- 提高查询效率

### 3. 缓存机制
- 缓存群聊列表
- 缓存统计信息
- 减少重复请求

## 监控和日志

### 日志记录
- 记录所有API调用
- 记录数据同步过程
- 记录错误和异常

### 性能监控
- 记录响应时间
- 监控数据量变化
- 跟踪错误率

## 扩展功能

### 1. 定时同步
- 支持定时自动同步
- 可配置同步频率
- 支持增量同步

### 2. 数据备份
- 自动备份聊天记录
- 支持数据恢复
- 定期清理旧数据

### 3. 实时通知
- 同步完成通知
- 错误告警通知
- 状态变化通知

## 注意事项

1. **数据安全**
   - 确保chatlog工具访问权限
   - 保护敏感聊天信息
   - 定期备份数据

2. **性能考虑**
   - 避免频繁同步大量数据
   - 合理设置时间范围
   - 监控系统资源使用

3. **兼容性**
   - 确保chatlog工具版本兼容
   - 测试不同数据格式
   - 验证API接口稳定性 