#!/bin/bash
# Webhook 自动部署脚本
# 用于接收 GitHub Webhook 并自动拉取更新

# 配置
GIT_DIR="/data/EquipmentManagement"
WEBHOOK_SECRET="your_secret_token_here"  # 替换为您的 webhook 密钥
LOG_FILE="/var/log/webhook-deploy.log"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 验证 webhook 签名
verify_signature() {
    if [ -z "$WEBHOOK_SECRET" ]; then
        return 0
    fi
    
    signature=$(echo "$HTTP_X_HUB_SIGNATURE_256" | sed 's/sha256=//')
    body=$(cat)
    computed=$(echo -n "$body" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" | sed 's/^.* //')
    
    if [ "$signature" != "$computed" ]; then
        log "ERROR: Invalid signature"
        exit 1
    fi
}

# 主流程
log "=== Webhook received ==="
log "Remote: $HTTP_X_FORWARDED_FOR -> $REMOTE_ADDR"
log "Event: $HTTP_X_GITHUB_EVENT"

# 只处理 push 事件
if [ "$HTTP_X_GITHUB_EVENT" != "push" ]; then
    log "Ignoring event: $HTTP_X_GITHUB_EVENT"
    exit 0
fi

# 进入项目目录
cd "$GIT_DIR" || {
    log "ERROR: Cannot cd to $GIT_DIR"
    exit 1
}

# 记录当前状态
log "Current branch: $(git rev-parse --abbrev-ref HEAD)"
log "Commit: $(git rev-parse --short HEAD)"

# 拉取最新代码
log "Pulling latest code..."
git pull origin main >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    log "Git pull successful"
    
    # 重启服务
    log "Restarting Flask application..."
    
    # 如果使用 systemd
    if systemctl is-active --quiet flask-app; then
        systemctl restart flask-app
        log "Service restarted via systemd"
    # 如果使用 gunicorn
    elif pgrep -f gunicorn > /dev/null; then
        pkill -HUP gunicorn
        log "Gunicorn reloaded"
    # 如果直接运行 python
    elif pgrep -f "python.*app.py" > /dev/null; then
        # 重启 Python 进程
        pkill -f "python.*app.py"
        sleep 2
        cd "$GIT_DIR"
        nohup python3 app.py >> "$LOG_FILE" 2>&1 &
        log "Flask app restarted"
    fi
    
    log "=== Deployment completed successfully ==="
    echo "HTTP/1.1 200 OK"
    echo "Content-Type: text/plain"
    echo ""
    echo "Deployment successful"
else
    log "ERROR: Git pull failed"
    echo "HTTP/1.1 500 Internal Server Error"
    echo "Content-Type: text/plain"
    echo ""
    echo "Deployment failed"
    exit 1
fi
