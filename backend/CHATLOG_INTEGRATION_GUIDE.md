# Chatlog 集成使用指南

## 概述

本指南说明如何将我们的后端系统与 chatlog 工具进行集成，实现自动获取微信群聊数据的功能。

## 前置条件

1. **安装并启动 chatlog 工具**
   - 下载 chatlog 预编译版本
   - 按照 chatlog 官方文档进行安装和配置
   - 启动 chatlog 的 HTTP 服务（默认端口 5030）

2. **确保网络连接**
   - chatlog 服务运行在 `http://127.0.0.1:5030`
   - 后端服务运行在 `http://127.0.0.1:5000`

## API 接口说明

### 1. 检查服务状态
```http
GET /api/v1/chatlog/status
```
**功能**: 检查 chatlog 服务是否正常运行
**返回**: 服务状态信息

### 2. 获取群聊列表
```http
GET /api/v1/chatlog/chatrooms
```
**功能**: 获取所有微信群聊列表
**返回**: 群聊信息列表

### 3. 获取联系人列表
```http
GET /api/v1/chatlog/contacts
```
**功能**: 获取所有联系人列表
**返回**: 联系人信息列表

### 4. 获取会话列表
```http
GET /api/v1/chatlog/sessions
```
**功能**: 获取最近会话列表
**返回**: 会话信息列表

### 5. 获取聊天记录
```http
GET /api/v1/chatlog/messages?talker=xxx&time_range=2024-01-01~2024-01-31&limit=100&offset=0&format=json
```
**参数**:
- `talker`: 聊天对象标识（可选）
- `time_range`: 时间范围，格式为 `YYYY-MM-DD` 或 `YYYY-MM-DD~YYYY-MM-DD`
- `limit`: 返回记录数量限制（默认 100）
- `offset`: 分页偏移量（默认 0）
- `format`: 输出格式，支持 `json`、`csv` 或纯文本（默认 json）

### 6. 获取多媒体内容
```http
GET /api/v1/chatlog/media?msgid=xxx
```
**参数**:
- `msgid`: 消息ID（必需）

### 7. 获取最近聊天记录
```http
GET /api/v1/chatlog/recent?days=7
```
**参数**:
- `days`: 天数，默认获取最近7天的记录

### 8. 同步聊天记录
```http
POST /api/v1/chatlog/sync
```
**功能**: 同步所有群聊的聊天记录
**返回**: 同步结果信息

## 使用示例

### 1. 检查服务状态
```bash
curl http://127.0.0.1:5000/api/v1/chatlog/status
```

### 2. 获取群聊列表
```bash
curl http://127.0.0.1:5000/api/v1/chatlog/chatrooms
```

### 3. 获取今天的聊天记录
```bash
curl "http://127.0.0.1:5000/api/v1/chatlog/messages?time_range=2024-01-15~2024-01-15&limit=50"
```

### 4. 获取最近3天的聊天记录
```bash
curl "http://127.0.0.1:5000/api/v1/chatlog/recent?days=3"
```

### 5. 同步所有聊天记录
```bash
curl -X POST http://127.0.0.1:5000/api/v1/chatlog/sync
```

## 测试验证

运行测试脚本验证集成功能：

```bash
cd backend
python test_chatlog_integration.py
```

测试脚本会依次检查：
1. chatlog 服务状态
2. 获取群聊列表
3. 获取联系人列表
4. 获取会话列表
5. 获取聊天记录
6. 获取最近聊天记录
7. 同步聊天记录

## 常见问题

### 1. 连接失败
**问题**: 无法连接到 chatlog 服务
**解决**: 
- 检查 chatlog 是否已启动
- 确认端口号是否正确（默认 5030）
- 检查防火墙设置

### 2. 数据为空
**问题**: API 返回空数据
**解决**:
- 确认 chatlog 中是否有聊天数据
- 检查时间范围参数是否正确
- 确认群聊名称或ID是否正确

### 3. 权限问题
**问题**: 无法访问某些数据
**解决**:
- 检查 chatlog 的权限设置
- 确认微信数据是否已正确解密

## 集成到前端

前端可以通过以下方式调用这些 API：

```javascript
// 检查服务状态
const status = await fetch('/api/v1/chatlog/status').then(r => r.json());

// 获取群聊列表
const chatrooms = await fetch('/api/v1/chatlog/chatrooms').then(r => r.json());

// 获取聊天记录
const messages = await fetch('/api/v1/chatlog/messages?time_range=2024-01-15~2024-01-15').then(r => r.json());
```

## 注意事项

1. **数据安全**: 确保 chatlog 服务只在可信的网络环境中运行
2. **性能考虑**: 大量数据查询时注意使用分页和限制参数
3. **错误处理**: 前端应妥善处理 API 返回的错误信息
4. **定期同步**: 建议定期调用同步接口以获取最新数据

## 扩展功能

后续可以扩展的功能：
1. 自动定时同步
2. 数据分析和统计
3. 关键词监控
4. 文件自动归档
5. 员工工作量统计 