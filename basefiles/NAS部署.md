# NAS 部署 chatlog 工具详细指南

> 本文档适用于广告公司服务监测软件在 NAS（群晖、QNAP、Unraid 等）环境下部署 chatlog 聊天记录采集工具。适合没有开发经验的小白用户。

---

## 一、什么是 chatlog？

chatlog 是一个可以自动采集和解析微信聊天记录的工具。你可以把它部署在 NAS 上，实现聊天数据的自动归档和后端系统对接。

---

## 二、准备工作

1. **确认你的 NAS 支持哪种架构**
   - Intel/AMD 处理器：选择 `linux_amd64` 版本
   - ARM 处理器（如部分威联通、树莓派）：选择 `linux_arm64` 或 `linux_armv7` 版本
2. **确认 NAS 是否支持 Docker**（如群晖 DSM 7、QNAP、Unraid 等）
3. **准备好 ssh 登录或 NAS 的命令行/文件管理器权限**

---

## 三、方式一：直接下载二进制文件安装（推荐大部分 NAS）

### 步骤 1：下载 chatlog

1. 打开浏览器，访问 [chatlog Releases 页面](https://github.com/sjzar/chatlog/releases)
2. 找到最新版本，下载适合你 NAS 架构的压缩包（如 `chatlog_0.0.15_linux_amd64.tar.gz`）
3. 用 NAS 的文件管理器或 scp/WinSCP 上传到 NAS 某个目录（如 `/volume1/docker/chatlog`）

### 步骤 2：解压并赋予权限

```bash
cd /volume1/docker/chatlog   # 进入存放目录
# 解压
 tar -xzvf chatlog_0.0.15_linux_amd64.tar.gz
# 赋予可执行权限
chmod +x chatlog
```

### 步骤 3：创建数据目录

```bash
mkdir -p chatlog_data
```

### 步骤 4：启动 chatlog 服务

```bash
./chatlog server --work-dir ./chatlog_data --addr 0.0.0.0:5030 > chatlog.log 2>&1 &
```
- `--addr 0.0.0.0:5030` 让 chatlog 监听所有网卡，方便局域网访问
- 日志会输出到 `chatlog.log` 文件

### 步骤 5：扫码登录微信

```bash
tail -f chatlog.log
```
- 看到二维码后，用手机微信扫码登录
- 登录成功后，chatlog 会自动采集聊天记录

---

## 四、方式二：用 Docker 部署（适合支持 Docker 的 NAS）

### 步骤 1：拉取 chatlog 镜像

```bash
docker pull sjzar/chatlog:latest
```

### 步骤 2：创建数据目录

```bash
mkdir -p /volume1/docker/chatlog_data
```

### 步骤 3：启动 chatlog 容器

```bash
docker run -d \
  --name chatlog \
  -p 5030:5030 \
  -v /volume1/docker/chatlog_data:/data \
  sjzar/chatlog:latest \
  server --work-dir /data --addr 0.0.0.0:5030
```

### 步骤 4：扫码登录微信

```bash
docker logs -f chatlog
```
- 看到二维码后，用手机微信扫码登录
- 登录成功后，chatlog 会自动采集聊天记录

---

## 五、后端对接与管理

- chatlog 启动后，API 地址为：`http://<NAS的IP>:5030`
- 后端配置 chatlog API 地址为 NAS 的 IP 即可
- 建议定期备份 `/chatlog_data` 目录

---

## 六、常见问题与注意事项

### 1. NAS 没有 ssh 或命令行？
- 可以用 NAS 的"任务计划"、"Docker 管理界面"或"文件管理器"上传和运行

### 2. 端口冲突？
- 可以把 `5030` 换成其它未被占用的端口

### 3. 扫码后无法登录？
- 确认 chatlog 支持你的微信版本，且 NAS 能联网

### 4. 性能问题？
- chatlog 只做数据采集和API服务，对 NAS 性能要求不高

### 5. chatlog 启动报错 `unsupported platform: linux v3`？
- chatlog 主要支持 Windows/macOS，部分 Linux 发行版可能不兼容
- 建议尝试 Docker 方式，或在 Windows/macOS 机器运行 chatlog

---

## 七、生活化总结

- NAS 就像你的"数据仓库"，chatlog 就是"仓库管理员"，帮你自动收集和整理微信聊天数据。
- 你只需要把"管理员"安置好（部署 chatlog），定期"扫码进门"（微信扫码登录），一切数据就会自动归档到 NAS 上，随时可查。

---

如需针对某品牌/型号 NAS 的详细图文教程，请联系技术支持！ 