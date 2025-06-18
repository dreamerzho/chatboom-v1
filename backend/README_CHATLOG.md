# Chatlog 集成快速使用指南

## 🚀 快速开始

### 1. 启动 chatlog 服务

首先确保 chatlog 工具已安装并启动：

```bash
# 启动 chatlog HTTP 服务
chatlog server
```

chatlog 服务将在 `http://127.0.0.1:5030` 启动。

### 2. 启动后端服务

```bash
cd backend

# 方式一：使用专门的启动脚本（推荐）
python start_with_chatlog.py

# 方式二：直接启动 Flask 应用
python app.py
```

### 3. 测试 API 接口

#### 检查服务状态
```bash
curl http://127.0.0.1:5000/api/v1/chatlog/status
```

#### 获取群聊列表
```bash
curl http://127.0.0.1:5000/api/v1/chatlog/chatrooms
```

#### 获取最近聊天记录
```bash
curl "http://127.0.0.1:5000/api/v1/chatlog/recent?days=3"
```

#### 获取指定时间范围的聊天记录
```bash
curl "http://127.0.0.1:5000/api/v1/chatlog/messages?time_range=2024-01-15~2024-01-15&limit=50"
```

## 📋 可用的 API 接口

| 接口 | 方法 | 功能 | 参数 |
|------|------|------|------|
| `/api/v1/chatlog/status` | GET | 检查服务状态 | 无 |
| `/api/v1/chatlog/chatrooms` | GET | 获取群聊列表 | 无 |
| `/api/v1/chatlog/contacts` | GET | 获取联系人列表 | 无 |
| `/api/v1/chatlog/sessions` | GET | 获取会话列表 | 无 |
| `/api/v1/chatlog/messages` | GET | 获取聊天记录 | `talker`, `time_range`, `limit`, `offset`, `format` |
| `/api/v1/chatlog/media` | GET | 获取多媒体内容 | `msgid` |
| `/api/v1/chatlog/recent` | GET | 获取最近聊天记录 | `days` |
| `/api/v1/chatlog/sync` | POST | 同步聊天记录 | 无 |

## 🧪 测试工具

### 运行完整测试
```bash
python test_chatlog_integration.py
```

### 在浏览器中测试
- 服务状态: http://127.0.0.1:5000/api/v1/chatlog/status
- 群聊列表: http://127.0.0.1:5000/api/v1/chatlog/chatrooms
- 最近记录: http://127.0.0.1:5000/api/v1/chatlog/recent?days=3

## 🔧 参数说明

### time_range 参数格式
- 单日: `2024-01-15`
- 日期范围: `2024-01-15~2024-01-31`

### format 参数选项
- `json`: JSON 格式（默认）
- `csv`: CSV 格式
- 纯文本: 不指定或空值

## ⚠️ 常见问题

### 1. 连接失败
**错误**: 无法连接到 chatlog 服务
**解决**: 确保 chatlog 服务已启动并运行在 5030 端口

### 2. 数据为空
**错误**: API 返回空数据
**解决**: 检查 chatlog 中是否有聊天数据，确认时间范围参数

### 3. 端口冲突
**错误**: 端口被占用
**解决**: 修改 `chatlog_integration.py` 中的 `CHATLOG_API_BASE` 地址

## 📁 相关文件

- `chatlog_integration.py`: chatlog API 集成模块
- `app.py`: Flask 应用主文件（包含 API 路由）
- `test_chatlog_integration.py`: 测试脚本
- `start_with_chatlog.py`: 启动脚本
- `CHATLOG_INTEGRATION_GUIDE.md`: 详细使用指南

## 🎯 下一步

1. 在前端页面中集成这些 API
2. 实现自动定时同步功能
3. 添加数据分析和统计功能
4. 实现文件自动归档功能 