# 广告公司服务监测软件

## 项目简介

这是一个专为广告公司设计的服务监测软件，主要功能包括：

1. **工作量化**：自动统计员工在微信群中的沟通和文件交付情况
2. **质量监控**：通过关键词分析，初步评估沟通质量
3. **数字资产管理**：将群聊中的文件根据规范自动归档

## 技术架构

- **后端框架**：Python Flask
- **数据库**：SQLite（轻量级文件数据库）
- **部署环境**：Sealos DevBox

## 快速开始

### 1. 环境要求

- Python 3.11+
- Flask 3.0.0

### 2. 安装依赖

```bash
pip install Flask==3.0.0
```

### 3. 启动应用

```bash
python3 app.py
```

或者使用启动脚本：

```bash
./entrypoint.sh
```

### 4. 访问应用

- 主页：http://localhost:3000
- 健康检查：http://localhost:3000/api/health
- 员工列表：http://localhost:3000/api/employees
- 项目列表：http://localhost:3000/api/projects

## API接口

### 健康检查
- **GET** `/api/health`
- 返回服务状态信息

### 员工管理
- **GET** `/api/employees` - 获取员工列表
- **POST** `/api/employees` - 添加员工映射

### 项目管理
- **GET** `/api/projects` - 获取项目列表

## 数据库结构

### employee_mappings（员工映射表）
- `id`: 主键
- `wechat_nickname`: 微信昵称
- `real_name`: 真实姓名
- `position`: 岗位
- `abbreviation`: 姓名缩写
- `created_at`: 创建时间

### chat_messages（聊天记录表）
- `id`: 主键
- `time`: 消息时间
- `talker_name`: 群聊名称
- `sender_name`: 发送者昵称
- `message_type`: 消息类型
- `content`: 消息内容
- `file_name`: 文件名
- `project_name`: 项目名
- `created_at`: 创建时间

### projects（项目表）
- `id`: 主键
- `name`: 项目名称
- `description`: 项目描述
- `created_at`: 创建时间

## 开发说明

### 项目结构
```
project/
├── app.py              # 主应用文件
├── requirements.txt    # 依赖包列表
├── entrypoint.sh      # 启动脚本
├── README.md          # 项目说明
└── ad_company_monitor.db  # SQLite数据库文件
```

### 代码特点
- 详细的中文注释
- 模块化设计
- 错误处理机制
- RESTful API设计

## 部署说明

本项目已适配Sealos DevBox环境，无需Docker容器化部署。直接在Python环境中运行即可。

## 注意事项

1. 首次运行会自动创建SQLite数据库文件
2. 确保端口3000未被占用
3. 在Sealos DevBox环境中，应用会自动启动

## 版本信息

- 版本：1.0.0
- 更新时间：2025-06-11
- 开发环境：Sealos DevBox 