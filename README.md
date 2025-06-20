# 广告公司服务监测与效能分析平台

## 1. 项目核心目标

本平台旨在将广告公司内部的沟通、协作流程数据化、可视化，以解决三大核心痛点：

1.  **工作量化**：自动统计员工在微信群中的沟通和文件交付情况，将隐性工作显性化。
2.  **质量监控**：通过独创的【精准评估模型 (V2)】，智能分析返工归因，评估项目健康度。
3.  **数字资产管理**：将群聊中的文件根据业务规范自动归档，形成可追溯的数字资产库。

---

## 2. 技术栈 (Tech Stack)

| 模块 | 技术 | 用途 |
| :--- | :--- | :--- |
| **前端** | **Next.js 14** | `React` 框架，提供服务器端渲染 (SSR) 与现代化的开发体验。 |
| | **TypeScript** | 为 `JavaScript` 提供静态类型检查，提升代码健壮性。 |
| | **Ant Design** | 高质量的 `React` UI 组件库，用于快速构建专业的数据后台界面。 |
| | **Ant Design Charts** | 基于 `Ant Design` 的数据可视化解决方案。 |
| **后端** | **Python (Flask)** | 轻量级、灵活的 `Python` Web 框架，用于构建 `RESTful API`。 |
| **数据库**| **PostgreSQL** | 功能强大的开源对象-关系型数据库，用于存储所有业务数据。 |

---

## 3. 项目结构

本仓库采用 `Monorepo` (单体仓库) 模式，将前端和后端代码统一管理。

```
.
├── backend/                # 后端项目 (Python, Flask)
│   ├── app.py              # Flask 应用主文件
│   ├── models.py           # 数据库模型定义
│   ├── chat_parser.py      # 聊天记录解析模块
│   └── requirements.txt    # Python 依赖
├── frontend/               # 前端项目 (Next.js, TypeScript)
│   ├── src/app/            # Next.js 14 的 App Router 核心目录
│   ├── package.json        # Node.js 依赖与脚本
│   └── next.config.ts      # Next.js 配置文件
├── README.md               # 您正在阅读的文档
└── ...
```

---

## 4. 本地开发指南

请遵循以下步骤在您的本地计算机上设置并运行本项目。

### A. 后端 (Backend)

1.  **进入后端目录**:
    ```bash
    cd backend
    ```

2.  **创建并激活虚拟环境** (推荐):
    ```bash
    # 创建虚拟环境
    python -m venv venv
    # 激活 (Windows)
    .\venv\Scripts\activate
    # 激活 (macOS/Linux)
    source venv/bin/activate
    ```

3.  **安装 Python 依赖**:
    ```bash
    # 建议使用国内镜像源以加速
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    ```

4.  **启动后端服务**:
    ```bash
    flask run
    ```
    服务将默认运行在 `http://127.0.0.1:5000`。

### B. 前端 (Frontend)

1.  **进入前端目录**:
    ```bash
    cd frontend
    ```

2.  **安装 Node.js 依赖**:
    ```bash
    # 建议使用淘宝镜像源以加速
    npm install --registry=https://registry.npmmirror.com
    ```

3.  **启动前端开发服务器**:
    ```bash
    npm run dev
    ```
    应用将默认运行在 `http://localhost:3000`，在浏览器中打开此地址即可看到界面。

---

## 5. API 接口 (V1)

所有 API 均以 `/api/v1` 为前缀。

### **核心看板 (Dashboard)**
- `GET /stats/kpi`: 获取核心 KPI 指标，如：员工总数、应急响应员工数、核心贡献者数、待分配人员数。
- `GET /stats/team-performance`: 获取团队效能榜数据。
- `GET /stats/project-risks`: 获取项目风险榜数据。

### **员工管理 (Employees)**
- `GET /employees`: 获取所有员工的列表，包含其总负荷指数、参与项目等核心信息。
- `GET /employees/{id}`: 获取单个员工的详细数据，包括其多维度的负荷指数构成 (如产出WE、过程成本WE等) 和在各项目中的表现详情。
- `POST /employees`: 创建一个新员工。
- `PUT /employees/{id}`: 更新指定 ID 的员工信息。
- `DELETE /employees/{id}`: 删除指定 ID 的员工。

### **人员匹配 (Matching)**
- `GET /unmatched-senders`: 获取所有在聊天记录中出现，但尚未匹配到真实员工的发送者列表。
- `POST /unmatched-senders/assign`: 将一个或多个未匹配的发送者分配给一个已存在或新创建的员工。

### **项目管理 (Projects)**
- `GET /projects`: 获取所有项目的列表。
- `GET /projects/{id}`: 获取单个项目的详细数据。

### **数据接入 (Data Ingestion)**
- `POST /upload/chat-history`: 上传 `.txt` 格式的聊天记录文件以供系统解析。

---
*文档更新于: 2025-06-21* 