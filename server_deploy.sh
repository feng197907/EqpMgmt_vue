#!/bin/bash
# =============================================================================
# EquipmentManagement 一键部署脚本（gunicorn 版）
# 功能：拉取最新代码 + 重启 gunicorn 服务
# 用法：./server_deploy.sh
# =============================================================================

set -e  # 遇到错误立即退出

PROJECT_DIR="/data/EquipmentManagement"
cd "$PROJECT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo ""
echo "=============================================="
echo "   EquipmentManagement 部署脚本 (gunicorn)"
echo "=============================================="
echo ""

# 0. 检查 Python 和 gunicorn
log_info "[0/6] 检查环境..."
PYTHON_CANDIDATES=(
    "/usr/local/python3.11/bin/python3.11"
    "/usr/bin/python3.11"
    "/usr/local/bin/python3.11"
)

PYTHON_BIN=""
for candidate in "${PYTHON_CANDIDATES[@]}"; do
    if [ -x "$candidate" ]; then
        PYTHON_BIN="$candidate"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    PYTHON_BIN=$(which python3.11 2>/dev/null || which python3 2>/dev/null || which python 2>/dev/null)
fi

if [ -z "$PYTHON_BIN" ] || [ ! -x "$PYTHON_BIN" ]; then
    log_error "未找到 Python！请安装 Python 3.7+"
    exit 1
fi

log_info "使用 Python: $PYTHON_BIN"
$PYTHON_BIN --version

# 检查 gunicorn
GUNICORN_BIN=$(which gunicorn 2>/dev/null || echo "$PROJECT_DIR/venv/bin/gunicorn")
if [ ! -x "$GUNICORN_BIN" ]; then
    log_warning "gunicorn 未找到，尝试安装..."
    $PYTHON_BIN -m pip install gunicorn --quiet --disable-pip-version-check 2>&1 | grep -v "WARNING:" || true
    GUNICORN_BIN=$(which gunicorn 2>/dev/null || echo "")
fi

if [ -z "$GUNICORN_BIN" ] || [ ! -x "$GUNICORN_BIN" ]; then
    log_error "gunicorn 安装失败！"
    exit 1
fi

log_info "使用 gunicorn: $GUNICORN_BIN"
$GUNICORN_BIN --version

# 1. 拉取最新代码
log_info "[1/6] 拉取最新代码..."
git pull origin main

# 2. 安装/更新依赖
log_info "[2/6] 安装/更新依赖..."
$PYTHON_BIN -m pip install -r requirements.txt --quiet --disable-pip-version-check 2>&1 | grep -v "WARNING:" || true

# 3. 停止旧进程
log_info "[3/6] 停止旧进程..."
# 方法1：如果 gunicorn 有 PID 文件
if [ -f "$PROJECT_DIR/gunicorn.pid" ]; then
    OLD_PID=$(cat "$PROJECT_DIR/gunicorn.pid")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        log_info "向旧进程 $OLD_PID 发送 SIGTERM..."
        kill -TERM $OLD_PID 2>/dev/null || true
        sleep 2
    fi
    rm -f "$PROJECT_DIR/gunicorn.pid"
fi

# 方法2：pkill 兜底
pkill -f "gunicorn.*5000" 2>/dev/null || true
pkill -f "gunicorn.*app:app" 2>/dev/null || true
pkill -f "gunicorn.*create_app" 2>/dev/null || true

# 方法3：fuser 杀掉 5000 端口
fuser -k 5000/tcp 2>/dev/null || true

sleep 3

# 4. 确保旧进程已停止
log_info "[4/6] 确保旧进程已停止..."
if pgrep -f "gunicorn.*5000" > /dev/null 2>&1; then
    log_warning "旧进程仍在运行，强制杀死..."
    pkill -9 -f "gunicorn.*5000" 2>/dev/null || true
    sleep 2
fi

# 5. 启动 gunicorn
log_info "[5/6] 启动 gunicorn..."
export PYTHONUNBUFFERED=1

# gunicorn 启动参数
WORKERS=2
BIND="0.0.0.0:5000"
PID_FILE="$PROJECT_DIR/gunicorn.pid"
ACCESS_LOG="$PROJECT_DIR/logs/gunicorn_access.log"
ERROR_LOG="$PROJECT_DIR/logs/gunicorn_error.log"

# 确保日志目录存在
mkdir -p "$PROJECT_DIR/logs"

# 使用 gunicorn 以 daemon 模式启动
$GUNICORN_BIN \
    --workers $WORKERS \
    --bind $BIND \
    --pid $PID_FILE \
    --access-logfile $ACCESS_LOG \
    --error-logfile $ERROR_LOG \
    --log-level info \
    --daemon \
    "app:create_app()"

log_info "gunicorn 已启动（后台模式）"
sleep 3

# 6. 健康检查
log_info "[6/6] 健康检查..."
MAX_RETRIES=10
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    sleep 1
    RETRY_COUNT=$((RETRY_COUNT + 1))
    
    # 检查 PID 文件对应的进程是否存在
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ! ps -p $PID > /dev/null 2>&1; then
            log_error "gunicorn 进程已退出！查看日志："
            echo "----------------------------------------------"
            tail -30 "$ERROR_LOG" 2>/dev/null || echo "  日志文件不存在"
            echo "----------------------------------------------"
            exit 1
        fi
    fi
    
    # 检查端口是否监听
    if ss -tln | grep -q ':5000 '; then
        # 尝试 HTTP 请求
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/login 2>/dev/null || echo "000")
        if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
            echo ""
            echo "=============================================="
            log_success "✅ 部署成功！服务正常运行"
            echo "=============================================="
            echo ""
            echo "  访问地址: http://82.157.4.72:5000"
            echo "  进程 PID: $(cat $PID_FILE 2>/dev/null || echo '未知')"
            echo "  日志文件:"
            echo "    - 访问日志: $ACCESS_LOG"
            echo "    - 错误日志: $ERROR_LOG"
            echo "    - 应用日志: $PROJECT_DIR/logs/error.log"
            echo ""
            echo "  查看实时日志："
            echo "    tail -f $PROJECT_DIR/logs/error.log"
            echo "    tail -f $ERROR_LOG"
            echo ""
            exit 0
        fi
    fi
    
    log_warning "等待服务启动... ($RETRY_COUNT/$MAX_RETRIES)"
done

# 超时：服务启动但未响应
echo ""
log_error "❌ 部署失败：服务启动超时"
echo ""
echo "=============================================="
echo "  调试信息"
echo "=============================================="
echo ""
echo "1. 进程状态："
ps aux | grep gunicorn | grep -v grep || echo "  无 gunicorn 进程"
echo ""
echo "2. 端口监听状态："
ss -tlnp | grep ':5000' || echo "  端口 5000 未监听"
echo ""
echo "3. gunicorn 错误日志（最后 30 行）："
echo "----------------------------------------------"
tail -30 "$ERROR_LOG" 2>/dev/null || echo "  日志文件不存在"
echo "----------------------------------------------"
echo ""
echo "4. 应用错误日志（最后 20 行）："
echo "----------------------------------------------"
tail -20 "$PROJECT_DIR/logs/error.log" 2>/dev/null || echo "  日志文件不存在"
echo "----------------------------------------------"
echo ""
exit 1
