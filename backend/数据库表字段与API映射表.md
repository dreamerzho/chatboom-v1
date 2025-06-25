# 数据库表字段与API一一映射表

---

## 1. 项目表（projects）

| 字段名                | 典型API接口                              | 前端页面/用途                  |
|----------------------|------------------------------------------|-------------------------------|
| id                   | /api/v1/projects/, /api/v1/projects/{id} | 项目列表、项目详情             |
| project_name         | 同上                                     | 项目列表、详情、文件归档、统计 |
| description          | 同上                                     | 项目详情                       |
| status               | 同上                                     | 项目状态、筛选                 |
| project_type         | /api/v1/projects/                        | 项目类型筛选                   |
| external_group_name  | /api/v1/projects/{id}                    | 项目详情-外部群                |
| internal_group_name  | /api/v1/projects/{id}                    | 项目详情-内部群                |
| start_date, end_date | /api/v1/projects/{id}                    | 项目周期                       |
| health_score         | /api/v1/projects/{id}, /dashboard/stats  | 项目健康分、仪表盘             |
| risk_level           | /api/v1/projects/{id}, /dashboard/stats  | 项目风险、仪表盘               |
| efficiency_score     | /api/v1/projects/{id}, /dashboard/stats  | 项目效率、仪表盘               |
| quality_score        | /api/v1/projects/{id}, /dashboard/stats  | 项目质量、仪表盘               |
| total_messages       | /api/v1/projects/{id}, /dashboard/stats  | 消息统计、仪表盘               |
| total_files          | /api/v1/projects/{id}, /dashboard/stats  | 文件统计、仪表盘               |
| active_employees     | /api/v1/projects/{id}, /dashboard/stats  | 活跃员工数、仪表盘             |
| last_activity        | /api/v1/projects/{id}                    | 项目详情-最近活跃              |
| created_at, updated_at | /api/v1/projects/{id}                  | 项目详情-时间                  |

---

## 2. 员工表（employee_mappings）

| 字段名              | 典型API接口                              | 前端页面/用途                  |
|--------------------|------------------------------------------|-------------------------------|
| id                 | /api/v1/employees/, /api/v1/employees/{id} | 员工列表、详情、统计           |
| wechat_nickname    | /api/v1/employees/                        | 员工管理、未匹配人员           |
| real_name          | /api/v1/employees/                        | 员工展示、统计                 |
| position           | /api/v1/employees/                        | 岗位展示、筛选                 |
| name_abbreviation  | /api/v1/employees/                        | 文件归档、统计                 |
| role               | /api/v1/employees/                        | 权限、统计                     |
| created_at, updated_at | /api/v1/employees/                    | 员工详情-时间                  |

---

## 3. 文件归档表（file_records）

| 字段名                | 典型API接口                              | 前端页面/用途                  |
|----------------------|------------------------------------------|-------------------------------|
| id                   | /api/v1/files/, /api/v1/files/list       | 文件列表、详情                 |
| original_name        | /api/v1/files/                           | 原始文件名展示                 |
| standardized_name    | /api/v1/files/                           | 规范文件名展示、合规校验       |
| project_name         | /api/v1/files/list?project_name=xxx      | 文件归属项目                   |
| work_order           | /api/v1/files/                           | 工单名展示                     |
| workload             | /api/v1/files/                           | 工作量展示                     |
| author_abbreviation  | /api/v1/files/                           | 作者缩写、统计                 |
| version              | /api/v1/files/                           | 版本号展示                     |
| file_extension       | /api/v1/files/                           | 文件类型展示                   |
| upload_time          | /api/v1/files/                           | 上传时间展示                   |
| uploader             | /api/v1/files/                           | 上传人展示                     |
| file_size            | /api/v1/files/                           | 文件大小展示                   |
| status               | /api/v1/files/                           | 文件状态、合规性               |
| project_id           | /api/v1/files/                           | 归属项目ID，统计用             |
| employee_id          | /api/v1/files/                           | 归属员工ID，统计用             |
| is_archived          | /api/v1/files/                           | 是否归档                       |
| archive_path         | /api/v1/files/                           | 归档路径                       |
| created_at, updated_at | /api/v1/files/                         | 文件详情-时间                  |

---

## 4. 工作量表（workload_records）

| 字段名                | 典型API接口                              | 前端页面/用途                  |
|----------------------|------------------------------------------|-------------------------------|
| id                   | /api/v1/workload/, /api/v1/employees/{id}/stats | 工作量统计、员工详情           |
| employee_id          | /api/v1/workload/                        | 统计归属员工                   |
| project_id           | /api/v1/workload/                        | 统计归属项目                   |
| date                 | /api/v1/workload/                        | 统计时间段                     |
| role                 | /api/v1/workload/                        | 岗位统计                       |
| output_type          | /api/v1/workload/                        | 产出类型                       |
| output_value         | /api/v1/workload/                        | 产出内容                       |
| we_value             | /api/v1/workload/                        | WE值展示                       |
| is_final             | /api/v1/workload/                        | 是否最终稿                     |
| is_iteration         | /api/v1/workload/                        | 是否迭代                       |
| iteration_count      | /api/v1/workload/                        | 迭代次数                       |
| related_file_id      | /api/v1/workload/                        | 关联文件                       |
| related_message_id   | /api/v1/workload/                        | 关联消息                       |
| business_unit        | /api/v1/workload/                        | 业务单元                       |
| quantity             | /api/v1/workload/                        | 数量                           |
| created_at           | /api/v1/workload/                        | 统计时间                       |

---

## 5. 聊天记录表（chat_messages）

| 字段名                | 典型API接口                              | 前端页面/用途                  |
|----------------------|------------------------------------------|-------------------------------|
| id                   | /api/v1/chatlog/messages                 | 消息详情、统计                 |
| message_id           | /api/v1/chatlog/messages                 | 消息唯一标识                   |
| talker_name          | /api/v1/chatlog/messages                 | 群聊名称                       |
| sender_name          | /api/v1/chatlog/messages                 | 发送人                         |
| message_type         | /api/v1/chatlog/messages                 | 消息类型                       |
| content              | /api/v1/chatlog/messages                 | 消息内容                       |
| file_name            | /api/v1/chatlog/messages                 | 文件名                         |
| timestamp            | /api/v1/chatlog/messages                 | 消息时间                       |
| project_id           | /api/v1/chatlog/messages                 | 归属项目                       |
| type                 | /api/v1/chatlog/messages                 | 消息类型（冗余）               |

---

## 6. 关键词分析相关（keywords, keyword_analyses, message_keywords）

| 字段名                | 典型API接口                              | 前端页面/用途                  |
|----------------------|------------------------------------------|-------------------------------|
| id                   | /api/v1/dashboard/negative-feedback      | 关键词统计、负面反馈           |
| keyword              | /api/v1/dashboard/negative-feedback      | 关键词展示                     |
| category_id          | /api/v1/dashboard/negative-feedback      | 关键词类别                     |
| weight               | /api/v1/dashboard/negative-feedback      | 关键词权重                     |
| analysis_date        | /api/v1/dashboard/negative-feedback      | 分析日期                       |
| project_id, employee_id | /api/v1/dashboard/negative-feedback   | 归属项目/员工                  |
| positive_score, negative_score, neutral_score | /api/v1/dashboard/negative-feedback | 情感分数           |
| keyword_stats, top_keywords | /api/v1/dashboard/negative-feedback | 关键词统计、展示               |

---

## 7. 未匹配人员（unmatched_persons）

| 字段名                | 典型API接口                              | 前端页面/用途                  |
|----------------------|------------------------------------------|-------------------------------|
| id                   | /api/v1/unmatched/                       | 未匹配人员管理                 |
| sender_name          | /api/v1/unmatched/                       | 微信昵称展示                   |
| group_name           | /api/v1/unmatched/                       | 群聊名称                       |
| role                 | /api/v1/unmatched/                       | 角色补充                       |
| remark               | /api/v1/unmatched/                       | 备注补充                       |
| created_at, updated_at | /api/v1/unmatched/                     | 时间展示                       |

---

## 8. 资产与版本（assets, file_versions）

| 字段名                | 典型API接口                              | 前端页面/用途                  |
|----------------------|------------------------------------------|-------------------------------|
| id                   | /api/v1/files/, /api/v1/assets/          | 资产/文件详情                  |
| original_name        | /api/v1/files/                           | 原始文件名                     |
| file_path            | /api/v1/files/                           | 文件路径                       |
| file_size            | /api/v1/files/                           | 文件大小                       |
| file_md5             | /api/v1/files/                           | 文件校验                       |
| version              | /api/v1/files/                           | 版本号                         |
| author_abbreviation  | /api/v1/files/                           | 作者缩写                       |
| project_id           | /api/v1/files/                           | 归属项目                       |
| upload_time          | /api/v1/files/                           | 上传时间                       |
| is_final_version     | /api/v1/files/                           | 是否最终版                     |

---

## 9. 风险与健康（risk_events, project_health_stats）

| 字段名                | 典型API接口                              | 前端页面/用途                  |
|----------------------|------------------------------------------|-------------------------------|
| id                   | /api/v1/projects/{id}/report/            | 项目风险、健康报告             |
| project_id           | /api/v1/projects/{id}/report/            | 归属项目                       |
| event_type, event_desc, event_time, severity, resolved | /api/v1/projects/{id}/report/ | 风险事件展示         |
| health_score, avg_time_to_final, avg_revisions, risk_count, warning_count, negative_sentiment_rate | /api/v1/projects/{id}/report/ | 健康统计 |

---

## 10. 其他表（如 project_chatrooms, workload_weights, employee_load_baselines 等）

这些表主要用于后台统计、配置、分析，部分字段会通过聚合API间接影响前端展示。

---

# 总结

- **每个表的主要字段都能在API和前端页面中找到用途。**
- **如有新业务需求或页面展示需求，建议同步扩展API和表结构。**
- **如需某一表的详细字段业务解释或API返回示例，随时告知！** 