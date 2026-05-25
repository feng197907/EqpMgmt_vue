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

# 检查 gunicorn（可选，如果不可用则使用 python 直接运行）
GUNICORN_BIN=""
USE_GUNICORN=false

# 尝试查找 gunicorn
if command -v gunicorn &> /dev/null; then
    GUNICORN_BIN=$(which gunicorn)
    # 验证 gunicorn 是否能正常运行（检查 SSL 模块）
    if $GUNICORN_BIN --version &> /dev/null; then
        USE_GUNICORN=true
        log_info "使用 gunicorn: $GUNICORN_BIN"
    else
        log_warning "gunicorn 存在但无法运行（可能缺少 SSL 模块），将使用 python 直接运行"
    fi
elif $PYTHON_BIN -m pip show gunicorn &> /dev/null; then
    GUNICORN_BIN="$PYTHON_BIN -m gunicorn"
    if $GUNICORN_BIN --version &> /dev/null; then
        USE_GUNICORN=true
        log_info "使用 gunicorn (module): $GUNICORN_BIN"
    else
        log_warning "gunicorn 模块存在但无法运行，将使用 python 直接运行"
    fi
else
    log_warning "gunicorn 未安装，将使用 python 直接运行"
fi

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

# 5. 启动服务
log_info "[5/6] 启动服务..."
export PYTHONUNBUFFERED=1

mkdir -p "$PROJECT_DIR/logs"

if [ "$USE_GUNICORN" = true ]; then
    # 使用 gunicorn 启动
    log_info "使用 gunicorn 启动..."
    WORKERS=2
    BIND="0.0.0.0:5000"
    PID_FILE="$PROJECT_DIR/gunicorn.pid"
    ACCESS_LOG="$PROJECT_DIR/logs/gunicorn_access.log"
    ERROR_LOG="$PROJECT_DIR/logs/gunicorn_error.log"

    $GUNICORN_BIN \
        --workers $WORKERS \
        --bind $BIND \
        --pid $PID_FILE \
        --access-logfile $ACCESS_LOG \
        --error-logfile $ERROR_LOG \
        --log-level info \
        --daemon \
        "app:create_app()"

    SERVER_PID=$(cat "$PID_FILE" 2>/dev/null || echo "")
    log_info "gunicorn 已启动，PID: $SERVER_PID"
else
    # 使用 python 直接运行
    log_info "使用 python 直接运行..."
    PID_FILE="$PROJECT_DIR/app.pid"
    
    # 使用 setsid 创建新会话，确保进程不因终端关闭而退出
    setsid nohup $PYTHON_BIN "$PROJECT_DIR/app.py" > "$PROJECT_DIR/app.log" 2>&1 &
    SERVER_PID=$!
    echo $SERVER_PID > "$PID_FILE"
    log_info "服务已启动，PID: $SERVER_PID"
fi

log_info "gunicorn 已启动（后台模式）"
sleep 3

# 6. 健康检查
log_info "[6/6] 健康检查..."
MAX_RETRIES=10
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    sleep 1
    RETRY_COUNT=$((RETRY_COUNT + 1))
    
    # 检查进程是否存在
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ! ps -p $PID > /dev/null 2>&1; then
            log_error "进程已退出！查看日志："
            echo "----------------------------------------------"
            if [ "$USE_GUNICORN" = true ]; then
                tail -30 "$ERROR_LOG" 2>/dev/null || echo "  日志文件不存在"
            else
                tail -30 "$PROJECT_DIR/app.log" 2>/dev/null || echo "  日志文件不存在"
            fi
            echo "----------------------------------------------"
            exit 1
        fi
    elif [ "$USE_GUNICORN" = false ]; then
        # python 直接运行时，检查进程是否存在
        if ! ps -p $SERVER_PID > /dev/null 2>&1 2>/dev/null; then
            log_error "Python 进程已退出！查看日志："
            echo "----------------------------------------------"
            tail -30 "$PROJECT_DIR/app.log"
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
            
            if [ "$USE_GUNICORN" = true ]; then
                echo "  服务类型: gunicorn"
                echo "  进程 PID: $(cat $PID_FILE 2>/dev/null || echo '未知')"
                echo "  日志文件:"
                echo "    - 访问日志: $ACCESS_LOG"
                echo "    - 错误日志: $ERROR_LOG"
            else
                echo "  服务类型: python (直接运行)"
                echo "  进程 PID: $SERVER_PID"
                echo "  日志文件:"
                echo "    - $PROJECT_DIR/app.log"
            fi
            echo "    - $PROJECT_DIR/logs/error.log"
            echo ""
            echo "  查看实时日志："
            echo "    tail -f $PROJECT_DIR/logs/error.log"
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
if [ "$USE_GUNICORN" = true ]; then
    ps aux | grep gunicorn | grep -v grep || echo "  无 gunicorn 进程"
else
    ps aux | grep "python.*app.py" | grep -v grep || echo "  无 python 进程"
fi
echo ""
echo "2. 端口监听状态："
ss -tlnp | grep ':5000' || echo "  端口 5000 未监听"
echo ""
echo "3. 应用日志（最后 30 行）："
echo "----------------------------------------------"
if [ "$USE_GUNICORN" = true ]; then
    tail -30 "$ERROR_LOG" 2>/dev/null || echo "  日志文件不存在"
else
    tail -30 "$PROJECT_DIR/app.log" 2>/dev/null || echo "  日志文件不存在"
fi
echo "----------------------------------------------"
echo ""
echo "4. 错误日志（最后 20 行）："
echo "----------------------------------------------"
tail -20 "$PROJECT_DIR/logs/error.log" 2>/dev/null || echo "  日志文件不存在"
echo "----------------------------------------------"
echo ""
exit 1
