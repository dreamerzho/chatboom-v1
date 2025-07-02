### **ChatBoom MVP 稳定版重构开发指令**

**总体目标**：为了快速交付一个稳定、高性能的MVP版本，我们将对后端进行一次精准的重构。核心思想是**变实时计算为预计算**，将Dashboard和项目列表所需的核心指标预先计算并存入一张新的聚合表中，从而大幅提升API响应速度和数据一致性。

#### **第一步：创建核心数据聚合表 ProjectSummary**

**目标**：创建一个新的数据库模型 ProjectSummary 用于存储预计算的项目核心指标，并生成相应的数据库迁移脚本。

**操作指令**：

1. 在 backend/models/ 目录下，创建一个新文件 project\_summary.py。  
2. 在该文件中，定义一个新的SQLAlchemy模型类 ProjectSummary。这个模型应包含以下字段，请参考 ProjectHealth 模型和 精准评估模型 (V2).md 文档来确定数据类型（大部分应为 Float 或 Integer）：  
   * id (主键, Integer)  
   * project\_id (外键，关联 projects.id, 并且设置 unique=True 以确保每个项目只有一条摘要记录)  
   * project\_name (String)  
   * total\_files (Integer)  
   * total\_workload\_we (Float)  
   * health\_score (Float)  
   * rework\_rate (Float)  
   * avg\_internal\_revisions (Float)  
   * avg\_customer\_revisions (Float)  
   * risk\_events\_count (Integer)  
   * positive\_feedback\_count (Integer)  
   * negative\_feedback\_count (Integer)  
   * last\_updated (DateTime, 记录每次更新的时间)  
3. 在 backend/models/\_\_init\_\_.py 中，导入并暴露这个新的 ProjectSummary 模型。  
4. 使用 alembic 工具，基于新的 ProjectSummary 模型自动生成一个新的数据库迁移（migration）脚本。请将生成的脚本文件放在 backend/migration/alembic/versions/ 目录下，并确保其内容正确无误。

#### **第二步：重构 analysis\_service 为ETL服务**

**目标**：将 analysis\_service.py 的职能从提供实时计算函数，转变为一个核心的ETL（抽取-转换-加载）服务，负责填充 ProjectSummary 表。

**操作指令**：

1. 打开 backend/analysis\_service.py 文件。  
2. 创建一个新的核心函数 def update\_all\_project\_summaries():。  
3. 将 backend/routes/dashboard.py 中用于计算全局指标的大部分复杂查询逻辑，以及 analysis\_service.py 中现有的 calculate\_project\_health\_score, calculate\_rework\_stats 等函数的核心计算逻辑，**全部迁移并整合**到 update\_all\_project\_summaries 函数内部。  
4. 该函数的逻辑流程应如下：  
   a. 查询所有的 Project。  
   b. 遍历每一个 project。  
   c. 对于每个 project，计算出 ProjectSummary 模型所需的所有指标（total\_files, health\_score, rework\_rate 等）。  
   d. 使用 db.session.merge() 或 "先查询后更新/创建" 的逻辑，将计算结果“更新或插入（Upsert）”到 ProjectSummary 表中。确保每个 project\_id 对应一条记录。  
   e. 在函数的最后，提交数据库会话 db.session.commit()。  
5. 删除 analysis\_service.py 中那些已经被新函数取代的、零散的旧计算函数。

#### **第三步：精简核心API路由**

**目标**：修改Dashboard和项目列表的API端点，使其直接从新的 ProjectSummary 表中读取数据，实现API的“瘦身”和性能提升。

**操作指令**：

1. 打开 backend/routes/dashboard.py 文件。  
2. 找到获取仪表盘概览数据的API端点（例如 /overview 或 /）。  
3. **完全删除**其中所有复杂的、多表JOIN的SQLAlchemy查询和实时计算逻辑。  
4. 将其替换为一条极其简单的查询：summaries \= ProjectSummary.query.all()。  
5. 将查询到的 summaries 结果序列化后直接返回。  
6. 打开 backend/routes/projects.py 文件。  
7. 找到获取项目列表的API端点（例如 GET /）。  
8. 同样地，**完全删除**其原有的计算逻辑，将其替换为对 ProjectSummary 表的直接查询。  
9. 确保返回的数据结构与前端 ProjectCard 组件期望的格式一致。

#### **第四步：配置定时调度任务**

**目标**：确保新的ETL服务能够被周期性地自动执行，保持聚合数据的“准实时”。

**操作指令**：

1. 打开 backend/scheduler.py 文件。  
2. **移除或注释掉**所有旧的、用于更新 project\_health\_stats 的零散定时任务。  
3. 从 backend.analysis\_service 导入我们新创建的 update\_all\_project\_summaries 函数。  
4. 在调度器中，添加一个新的定时任务，配置为**每15分钟**执行一次 update\_all\_project\_summaries() 函数。  
5. 确保调度器在Flask应用启动时能正确初始化并运行。

#### **最终验证**

**目标**：确认所有修改已正确完成，并且系统作为一个整体能够正常工作。

**操作指令**：

1. 请完整审查以上所有步骤的修改。  
2. 启动后端应用，并手动执行一次数据库迁移命令 flask db upgrade，以应用新的 ProjectSummary 表结构。  
3. 手动触发一次 update\_all\_project\_summaries() 函数（可以通过创建一个临时脚本或API来调用），检查 project\_summary 表是否已成功填充数据。  
4. 通过Postman或直接访问浏览器，请求 /api/dashboard 和 /api/projects 接口，确认它们现在能够极快地返回数据，并且数据内容与 project\_summary 表中的一致。  
5. 确认前端页面（特别是仪表盘和项目列表页）能够正常展示数据。

完成以上所有步骤后，我们的MVP将在性能和稳定性上达到一个全新的水平，为后续的快速迭代和功能开发奠定坚实的基础。