# ClawDesk remote client / Home backend over Tailscale

Janner 的目标形态：Office Mac 只跑 ClawDesk 客户端，不在 Office 安装/运行本地后端和 Hermes；后端运行在 Hermes 所在机器（Home Mac / Mac mini），Office 客户端把 Backend URL 指到 Tailscale IP。

## 1. 在 Hermes 所在机器启动后端

从 ClawDesk repo 根目录：

```bash
CLAWDESK_HOST=0.0.0.0 CLAWDESK_PORT=8765 ./scripts/run_backend.sh
```

含义：

- `0.0.0.0` 让同一 Tailscale 网络内的 Office Mac 可以访问；
- 数据库默认在 `server/.data/clawdesk-dev.db`；
- Hermes mode 默认 `auto`，会优先调用本机 Hermes CLI；
- 真实 Hermes 回复依赖这台后端机器上已经配置好的 `hermes` CLI。

查看本机 Tailscale IP：

```bash
tailscale ip -4
```

假设输出为：

```text
100.95.79.69
```

那么 Office 客户端填：

```text
http://100.95.79.69:8765
```

## 2. Office Mac 只安装客户端包

构建 client-only 包：

```bash
./scripts/package_macos_client.py
```

输出：

```text
dist/ClawDesk-Client.app
dist/ClawDesk-0.1.0-macOS-client.zip
```

这个包只包含 SwiftUI 客户端，不嵌入后端，不要求 Office Mac 安装 `uv` 或 Hermes。

Office 首次打开后：

1. 进入右上角 Backend Settings；
2. Base URL 填 Home/Hermes 机器的 Tailscale 地址，例如 `http://100.95.79.69:8765`；
3. 点击 `Save & Check`；
4. 显示 Connected 后即可使用。

## 3. 安全边界

当前是 Tailscale 私网使用模型，不建议直接暴露公网。

建议：

- 只绑定 Tailscale 可达网络，优先在可信设备间使用；
- 不要把 `0.0.0.0:8765` 暴露到公网路由器端口映射；
- 后续可增加 ClawDesk backend token / mTLS / Tailscale Serve/Funnel 规则；
- 当前 API 没有鉴权，依赖 Tailscale 网络边界。

## 4. 验证

在 Home/Hermes 机器启动后端后，Office 或任意同 Tailnet 机器运行：

```bash
curl http://100.95.79.69:8765/health
```

预期：

```json
{"ok":true,"hermes_mode":"auto"}
```

真实 Hermes 路径仍可在后端机器验证：

```bash
./scripts/smoke_real_hermes.py
```
