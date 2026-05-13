# Webhook 自动部署配置指南

## 概述
本项目包含两个自动部署脚本：
1. `webhook_server.py` - Python Flask Webhook 服务器
2. `webhook-deploy.sh` - Shell 脚本版本

## 快速配置

### 1. 上传脚本到服务器
```bash
scp -r scripts/webhook_server.py root@82.157.4.72:/root/EquipmentManagement/
```

### 2. 在服务器上安装依赖
```bash
ssh root@82.157.4.72
cd /root/EquipmentManagement
pip3 install flask
```

### 3. 配置 Webhook 密钥
编辑 `webhook_server.py`，将 `WEBHOOK_SECRET` 改为您自定义的密钥：
```python
WEBHOOK_SECRET = "your_custom_secret_here"
```

### 4. 启动 Webhook 服务
```bash
# 后台运行
nohup python3 webhook_server.py > webhook.log 2>&1 &

# 或使用 systemd (推荐)
# 创建 /etc/systemd/system/webhook.service
```

### 5. 配置 GitHub Webhook

1. 打开 GitHub 仓库 → Settings → Webhooks → Add webhook
2. 配置：
   - **Payload URL**: `http://82.157.4.72:5001/webhook`
   - **Content type**: `application/json`
   - **Secret**: 您设置的 `WEBHOOK_SECRET`
   - **Events**: Just the push event

### 6. 测试 Webhook
```bash
# 本地测试
curl -X POST http://82.157.4.72:5001/webhook

# GitHub 界面测试
# Webhooks 页面 → 点击您的 webhook → Test → Push events
```

## Systemd 服务配置 (推荐)

创建 `/etc/systemd/system/webhook.service`:
```ini
[Unit]
Description=GitHub Webhook Auto Deploy
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/EquipmentManagement
ExecStart=/usr/bin/python3 /root/EquipmentManagement/webhook_server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
systemctl daemon-reload
systemctl enable webhook
systemctl start webhook
systemctl status webhook
```

## 日志查看
```bash
# 应用日志
tail -f /var/log/webhook-deploy.log

# systemd 日志
journalctl -u webhook -f
```

## 故障排除

### Webhook 未触发
- 检查服务器防火墙是否开放 5001 端口
- 确认 GitHub Webhook 配置正确
- 查看 webhook 发送记录

### 签名验证失败
- 确保本地和 GitHub 的 secret 一致
- 检查是否有代理或负载均衡修改请求

### 部署失败
- 检查 git pull 是否正常
- 确认工作目录权限
- 查看详细日志
