# API接口标准化规范

## 概述
本文档定义了广告公司服务监测软件后端API的统一规范，确保所有接口都遵循一致的格式和标准。

## 1. 基础规范

### 1.1 URL规范
- 所有API接口都以 `/api/v1/` 开头
- 使用RESTful风格，资源名使用复数形式
- 示例：`/api/v1/employees`, `/api/v1/projects`

### 1.2 HTTP方法规范
- `GET`: 获取资源（查询）
- `POST`: 创建资源
- `PUT`: 更新资源（完整更新）
- `PATCH`: 部分更新资源
- `DELETE`: 删除资源

### 1.3 响应格式规范

#### 成功响应格式
```json
{
    "success": true,
    "data": {
        // 具体数据
    },
    "message": "操作成功",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

#### 错误响应格式
```json
{
    "success": false,
    "error": "错误描述",
    "error_code": "ERROR_CODE",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

### 1.4 状态码规范
- `200`: 成功
- `201`: 创建成功
- `400`: 请求参数错误
- `401`: 未授权
- `403`: 禁止访问
- `404`: 资源不存在
- `422`: 数据验证失败
- `500`: 服务器内部错误

## 2. 分页规范

### 2.1 分页参数
- `page`: 页码（从1开始）
- `per_page`: 每页数量（默认20，最大100）
- `sort_by`: 排序字段
- `sort_order`: 排序方向（asc/desc）

### 2.2 分页响应格式
```json
{
    "success": true,
    "data": {
        "items": [],
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total": 100,
            "total_pages": 5,
            "has_next": true,
            "has_prev": false
        }
    }
}
```

## 3. 查询参数规范

### 3.1 基础查询参数
- `q`: 搜索关键词
- `status`: 状态过滤
- `date_from`: 开始日期
- `date_to`: 结束日期

### 3.2 示例
```
GET /api/v1/employees?q=张三&status=active&page=1&per_page=20
```

## 4. 数据验证规范

### 4.1 必填字段验证
- 所有必填字段缺失时返回400错误
- 错误信息应明确指出缺失的字段

### 4.2 数据类型验证
- 字符串长度限制
- 数值范围验证
- 日期格式验证（ISO 8601）

### 4.3 业务规则验证
- 唯一性约束
- 关联关系验证
- 状态转换规则

## 5. 接口分类

### 5.1 员工管理接口
- `GET /api/v1/employees` - 获取员工列表
- `POST /api/v1/employees` - 创建员工映射
- `PUT /api/v1/employees/{id}` - 更新员工信息
- `DELETE /api/v1/employees/{id}` - 删除员工映射

### 5.2 项目管理接口
- `GET /api/v1/projects` - 获取项目列表
- `POST /api/v1/projects` - 创建项目
- `PUT /api/v1/projects/{id}` - 更新项目
- `DELETE /api/v1/projects/{id}` - 删除项目

### 5.3 文件管理接口
- `GET /api/v1/files` - 获取文件列表
- `POST /api/v1/files/validate` - 验证文件名
- `POST /api/v1/files/upload` - 上传文件
- `PUT /api/v1/files/{id}` - 更新文件信息

### 5.4 聊天记录接口
- `GET /api/v1/chatlog` - 获取聊天记录
- `POST /api/v1/chatlog/sync` - 同步聊天记录
- `GET /api/v1/chatlog/statistics` - 获取统计信息

### 5.5 关键词分析接口
- `GET /api/v1/keywords` - 获取关键词列表
- `POST /api/v1/keywords` - 创建关键词
- `POST /api/v1/keywords/analyze` - 执行关键词分析
- `GET /api/v1/keywords/statistics` - 获取分析统计

### 5.6 仪表板接口
- `GET /api/v1/dashboard/overview` - 获取概览数据
- `GET /api/v1/dashboard/health` - 获取健康状态
- `GET /api/v1/dashboard/trends` - 获取趋势数据

## 6. 错误处理规范

### 6.1 错误码定义
- `VALIDATION_ERROR`: 数据验证错误
- `NOT_FOUND`: 资源不存在
- `DUPLICATE_ENTRY`: 重复记录
- `INVALID_STATUS`: 状态无效
- `SYNC_ERROR`: 同步错误
- `DATABASE_ERROR`: 数据库错误

### 6.2 错误处理示例
```python
try:
    # 业务逻辑
    pass
except ValidationError as e:
    return jsonify({
        'success': False,
        'error': str(e),
        'error_code': 'VALIDATION_ERROR'
    }), 400
except Exception as e:
    logger.error(f"未知错误: {str(e)}")
    return jsonify({
        'success': False,
        'error': '服务器内部错误',
        'error_code': 'INTERNAL_ERROR'
    }), 500
```

## 7. 日志规范

### 7.1 日志级别
- `DEBUG`: 调试信息
- `INFO`: 一般信息
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

### 7.2 日志格式
```python
logger.info(f"用户 {user_id} 执行了 {action} 操作")
logger.error(f"操作失败: {error_message}", exc_info=True)
```

## 8. 安全规范

### 8.1 CORS配置
- 允许跨域请求
- 限制允许的方法和头部

### 8.2 输入验证
- 防止SQL注入
- 防止XSS攻击
- 文件上传安全检查

### 8.3 速率限制
- API调用频率限制
- 防止恶意请求

## 9. 性能规范

### 9.1 数据库查询优化
- 使用索引
- 避免N+1查询
- 分页查询

### 9.2 缓存策略
- 缓存常用数据
- 设置合理的过期时间

### 9.3 异步处理
- 耗时操作异步处理
- 使用任务队列

## 10. 文档规范

### 10.1 接口文档
- 每个接口都要有详细的文档
- 包含请求参数、响应格式、示例

### 10.2 代码注释
- 函数级别的注释
- 复杂逻辑的注释
- 中文注释优先

## 11. 测试规范

### 11.1 单元测试
- 每个接口都要有对应的测试
- 测试覆盖率要求

### 11.2 集成测试
- 端到端测试
- 数据库集成测试

### 11.3 性能测试
- 压力测试
- 负载测试

## 12. 部署规范

### 12.1 环境配置
- 开发环境
- 测试环境
- 生产环境

### 12.2 监控告警
- 接口响应时间监控
- 错误率监控
- 系统资源监控

---

**注意**: 所有新开发的接口都必须遵循本规范，确保系统的一致性和可维护性。 