# 微信登录与数据获取指南

## 📱 **微信登录流程**

### **1. 启动 chatlog 服务**

首先确保 chatlog 服务正在运行：

```bash
# 在项目根目录执行
./entrypoint.sh
```

或者手动启动：

```bash
# 创建工作目录
mkdir -p chatlog_data

# 启动 chatlog 服务
./chatlog server --work-dir ./chatlog_data --addr 127.0.0.1:5030
```

### **2. 查看登录二维码**

chatlog 启动后，会在日志文件中输出登录二维码：

```bash
# 查看实时日志
tail -f chatlog.log
```

你会看到类似这样的输出：
```
2025-06-11T06:07:23Z INF 正在生成登录二维码...
[二维码字符画]
请使用微信扫描二维码登录
```

### **3. 微信扫码登录**

1. **打开手机微信**
2. **扫描终端中显示的二维码**
3. **确认登录**（可能需要输入验证码）
4. **等待登录成功**

登录成功后，chatlog 会自动开始获取微信数据。

---

## 🔄 **数据获取流程**

### **1. 自动数据同步**

登录成功后，chatlog 会自动：
- 获取微信数据库密钥
- 解密聊天记录
- 建立本地数据库
- 启动 HTTP API 服务

### **2. 验证数据获取**

检查数据是否获取成功：

```bash
# 测试 API 连接
curl http://127.0.0.1:5030/api/v1/chatroom

# 或者使用我们的测试脚本
cd backend
python test_chatlog_api.py
```

### **3. 同步到后端数据库**

通过后端 API 同步数据：

```bash
# 同步所有群聊数据
curl -X POST http://127.0.0.1:5000/api/v1/chatlog/sync-all \
  -H "Content-Type: application/json" \
  -d '{"days_back": 7}'

# 同步特定群聊
curl -X POST http://127.0.0.1:5000/api/v1/chatlog/sync \
  -H "Content-Type: application/json" \
  -d '{"group_name": "群聊名称", "days_back": 7}'
```

---

## 🛠️ **常见问题解决**

### **问题 1: chatlog 启动失败**

**错误信息**: `unsupported platform: linux v3`

**解决方案**: 
- chatlog 主要支持 Windows 和 macOS
- 在 Linux 上可能需要使用 Docker 或虚拟机
- 或者考虑在 Windows/macOS 机器上运行 chatlog，然后通过网络 API 访问

### **问题 2: 无法获取微信数据**

**可能原因**:
- 微信版本不兼容
- 数据库加密方式变化
- 权限不足

**解决方案**:
- 确保使用支持的微信版本（3.x 或 4.0）
- 检查是否有足够的系统权限
- 尝试重新登录微信

### **问题 3: 二维码显示异常**

**解决方案**:
- 使用支持 UTF-8 的终端
- 调整终端字体大小
- 尝试复制二维码链接到浏览器中查看

---

## 📊 **数据同步监控**

### **1. 查看同步状态**

```bash
# 检查 chatlog 状态
curl http://127.0.0.1:5000/api/v1/chatlog/status

# 查看群聊列表
curl http://127.0.0.1:5000/api/v1/chatlog/groups
```

### **2. 查看同步统计**

```bash
# 查看聊天记录统计
curl http://127.0.0.1:5000/api/v1/chatlog/stats

# 查看文件记录统计
curl http://127.0.0.1:5000/api/v1/files/stats
```

---

## 🔧 **高级配置**

### **1. 自定义时间范围**

```bash
# 同步指定时间范围的数据
curl -X POST http://127.0.0.1:5000/api/v1/chatlog/sync \
  -H "Content-Type: application/json" \
  -d '{
    "group_name": "群聊名称",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  }'
```

### **2. 批量同步**

```bash
# 同步所有群聊的最近30天数据
curl -X POST http://127.0.0.1:5000/api/v1/chatlog/sync-all \
  -H "Content-Type: application/json" \
  -d '{"days_back": 30}'
```

---

## 📝 **注意事项**

1. **数据安全**: 所有数据都在本地处理，不会上传到云端
2. **隐私保护**: 请确保遵守相关法律法规和隐私政策
3. **定期备份**: 建议定期备份 chatlog 工作目录
4. **版本兼容**: 确保 chatlog 版本与微信版本兼容
5. **网络连接**: 首次登录需要网络连接，后续可离线使用

---

## 🎯 **下一步**

完成微信登录和数据获取后，您可以：

1. **查看管理界面**: 访问 `http://127.0.0.1:3000` 查看数据
2. **配置员工映射**: 将微信昵称映射到真实姓名
3. **设置关键词**: 配置正面/负面关键词进行情感分析
4. **监控文件**: 自动检测和验证文件命名规范
5. **生成报告**: 查看工作统计和趋势分析

如有问题，请查看日志文件或联系技术支持。 