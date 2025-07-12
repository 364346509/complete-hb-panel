#!/bin/bash

# HB-Panel 开发环境启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_step "检查开发环境依赖..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 未安装"
        exit 1
    fi
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装"
        exit 1
    fi
    
    # 检查npm
    if ! command -v npm &> /dev/null; then
        log_error "npm 未安装"
        exit 1
    fi
    
    log_info "依赖检查完成"
}

# 设置环境变量
setup_env() {
    log_step "设置开发环境变量..."
    
    if [[ ! -f .env ]]; then
        log_info "创建开发环境配置文件..."
        cat > .env << EOF
# 开发环境配置
DEBUG=true
DATABASE_URL=sqlite:///./hb_panel_dev.db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 应用配置
APP_NAME=HB-Panel-Dev
APP_VERSION=1.0.0-dev

# 服务端口
BACKEND_PORT=8000
FRONTEND_PORT=3000
NGINX_PORT=8080
EOF
    fi
    
    log_info "环境变量设置完成"
}

# 安装后端依赖
install_backend_deps() {
    log_step "安装后端依赖..."
    
    cd backend
    
    # 创建虚拟环境
    if [[ ! -d venv ]]; then
        log_info "创建Python虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 安装依赖
    pip install --upgrade pip
    pip install -r requirements.txt
    
    cd ..
    log_info "后端依赖安装完成"
}

# 安装前端依赖
install_frontend_deps() {
    log_step "安装前端依赖..."
    
    cd frontend
    
    # 安装依赖
    npm install
    
    cd ..
    log_info "前端依赖安装完成"
}

# 初始化数据库
init_database() {
    log_step "初始化数据库..."
    
    cd backend
    source venv/bin/activate
    
    # 运行数据库迁移
    python -c "
from app.core.database import engine, Base
from app.models import user, website, database
Base.metadata.create_all(bind=engine)
print('数据库表创建完成')
"
    
    # 创建默认管理员用户
    python -c "
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()
admin_user = db.query(User).filter(User.username == 'admin').first()
if not admin_user:
    admin_user = User(
        username='admin',
        email='admin@hb-panel.com',
        password_hash=get_password_hash('admin123'),
        full_name='Administrator',
        is_active=True,
        is_superuser=True
    )
    db.add(admin_user)
    db.commit()
    print('默认管理员用户创建完成')
else:
    print('管理员用户已存在')
db.close()
"
    
    cd ..
    log_info "数据库初始化完成"
}

# 启动后端服务
start_backend() {
    log_step "启动后端服务..."
    
    cd backend
    source venv/bin/activate
    
    # 启动FastAPI服务
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    
    cd ..
    log_info "后端服务已启动 (PID: $BACKEND_PID)"
}

# 启动前端服务
start_frontend() {
    log_step "启动前端服务..."
    
    cd frontend
    
    # 启动Vite开发服务器
    npm run dev &
    FRONTEND_PID=$!
    
    cd ..
    log_info "前端服务已启动 (PID: $FRONTEND_PID)"
}

# 显示服务信息
show_services() {
    log_step "开发环境启动完成！"
    
    echo ""
    echo "=========================================="
    echo "🚀 HB-Panel 开发环境"
    echo "=========================================="
    echo ""
    echo "📱 前端开发服务器: http://localhost:3000"
    echo "🔧 后端API服务器: http://localhost:8000"
    echo "📚 API文档: http://localhost:8000/docs"
    echo "🔍 API调试: http://localhost:8000/redoc"
    echo ""
    echo "👤 默认账号信息:"
    echo "   用户名: admin"
    echo "   密码: admin123"
    echo ""
    echo "🔧 开发工具:"
    echo "   热重载: 已启用"
    echo "   调试模式: 已启用"
    echo "   数据库: SQLite (开发用)"
    echo ""
    echo "📁 项目目录:"
    echo "   后端: ./backend"
    echo "   前端: ./frontend"
    echo "   配置: ./.env"
    echo ""
    echo "🛑 停止服务: Ctrl+C"
    echo "=========================================="
}

# 清理函数
cleanup() {
    log_info "正在停止服务..."
    
    if [[ -n $BACKEND_PID ]]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [[ -n $FRONTEND_PID ]]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # 杀死所有相关进程
    pkill -f "uvicorn main:app" 2>/dev/null || true
    pkill -f "npm run dev" 2>/dev/null || true
    
    log_info "服务已停止"
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 主函数
main() {
    echo ""
    echo "=========================================="
    echo "🚀 HB-Panel 开发环境启动脚本"
    echo "=========================================="
    echo ""
    
    check_dependencies
    setup_env
    install_backend_deps
    install_frontend_deps
    init_database
    start_backend
    start_frontend
    show_services
    
    # 等待用户中断
    while true; do
        sleep 1
    done
}

# 执行主函数
main "$@"
