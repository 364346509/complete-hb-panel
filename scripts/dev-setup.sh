#!/bin/bash

# HB-Panel 开发环境设置脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查开发环境依赖..."
    
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
    
    log_success "依赖检查完成"
}

# 设置后端环境
setup_backend() {
    log_info "设置后端开发环境..."
    
    cd backend
    
    # 创建虚拟环境
    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
        log_success "Python虚拟环境创建完成"
    fi
    
    # 激活虚拟环境并安装依赖
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # 创建环境配置文件
    if [[ ! -f ".env" ]]; then
        cat > .env << 'EOF'
# 开发环境配置
DEBUG=True
HOST=0.0.0.0
PORT=8000
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=sqlite:///./hb_panel_dev.db
ALLOWED_HOSTS=["*"]
LOG_LEVEL=DEBUG
EOF
        log_success "后端环境配置文件创建完成"
    fi
    
    # 初始化数据库
    python -c "
import asyncio
from app.core.database import init_db
asyncio.run(init_db())
print('开发数据库初始化完成')
"
    
    # 创建开发用户
    python -c "
from app.core.database import SessionLocal
from app.services.user_service import UserService

db = SessionLocal()
user_service = UserService(db)

# 创建开发管理员用户
admin = user_service.get_user_by_username('admin')
if not admin:
    admin = user_service.create_user(
        username='admin',
        email='admin@dev.local',
        password='admin123',
        full_name='开发管理员',
        is_superuser=True
    )
    print('开发管理员用户创建成功')
    print('用户名: admin, 密码: admin123')

# 创建普通测试用户
test_user = user_service.get_user_by_username('test')
if not test_user:
    test_user = user_service.create_user(
        username='test',
        email='test@dev.local',
        password='test123',
        full_name='测试用户',
        is_superuser=False
    )
    print('测试用户创建成功')
    print('用户名: test, 密码: test123')

db.close()
"
    
    cd ..
    log_success "后端环境设置完成"
}

# 设置前端环境
setup_frontend() {
    log_info "设置前端开发环境..."
    
    cd frontend
    
    # 安装依赖
    npm install
    
    # 创建环境配置文件
    if [[ ! -f ".env.development" ]]; then
        cat > .env.development << 'EOF'
# 前端开发环境配置
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=HB-Panel 开发版
EOF
        log_success "前端环境配置文件创建完成"
    fi
    
    cd ..
    log_success "前端环境设置完成"
}

# 创建开发脚本
create_dev_scripts() {
    log_info "创建开发脚本..."
    
    # 后端启动脚本
    cat > start-backend.sh << 'EOF'
#!/bin/bash
cd backend
source venv/bin/activate
python main.py
EOF
    chmod +x start-backend.sh
    
    # 前端启动脚本
    cat > start-frontend.sh << 'EOF'
#!/bin/bash
cd frontend
npm run dev
EOF
    chmod +x start-frontend.sh
    
    # 同时启动脚本
    cat > start-dev.sh << 'EOF'
#!/bin/bash

# 启动后端
echo "启动后端服务..."
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端
echo "启动前端服务..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# 等待用户输入退出
echo "开发服务已启动"
echo "后端: http://localhost:8000"
echo "前端: http://localhost:3000"
echo "API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 退出"

# 捕获退出信号
trap 'kill $BACKEND_PID $FRONTEND_PID; exit' INT

# 等待进程结束
wait
EOF
    chmod +x start-dev.sh
    
    # 测试脚本
    cat > run-tests.sh << 'EOF'
#!/bin/bash

echo "运行后端测试..."
cd backend
source venv/bin/activate
python -m pytest tests/ -v

echo "运行前端测试..."
cd ../frontend
npm run test

echo "代码质量检查..."
npm run lint
EOF
    chmod +x run-tests.sh
    
    log_success "开发脚本创建完成"
}

# 创建VS Code配置
create_vscode_config() {
    log_info "创建VS Code配置..."
    
    mkdir -p .vscode
    
    # 设置文件
    cat > .vscode/settings.json << 'EOF'
{
    "python.defaultInterpreterPath": "./backend/venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "eslint.workingDirectories": ["frontend"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.fixAll.eslint": true
    },
    "files.associations": {
        "*.vue": "vue"
    },
    "emmet.includeLanguages": {
        "vue": "html"
    }
}
EOF
    
    # 启动配置
    cat > .vscode/launch.json << 'EOF'
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/backend/main.py",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}/backend",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/backend"
            }
        }
    ]
}
EOF
    
    # 任务配置
    cat > .vscode/tasks.json << 'EOF'
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "启动后端",
            "type": "shell",
            "command": "./start-backend.sh",
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "new"
            }
        },
        {
            "label": "启动前端",
            "type": "shell",
            "command": "./start-frontend.sh",
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "new"
            }
        },
        {
            "label": "运行测试",
            "type": "shell",
            "command": "./run-tests.sh",
            "group": "test"
        }
    ]
}
EOF
    
    log_success "VS Code配置创建完成"
}

# 显示开发指南
show_dev_guide() {
    log_success "开发环境设置完成！"
    echo
    echo "========================================"
    echo "开发指南:"
    echo "========================================"
    echo
    echo "启动开发服务:"
    echo "  ./start-dev.sh          # 同时启动前后端"
    echo "  ./start-backend.sh      # 仅启动后端"
    echo "  ./start-frontend.sh     # 仅启动前端"
    echo
    echo "访问地址:"
    echo "  前端: http://localhost:3000"
    echo "  后端: http://localhost:8000"
    echo "  API文档: http://localhost:8000/docs"
    echo
    echo "测试账号:"
    echo "  管理员 - 用户名: admin, 密码: admin123"
    echo "  普通用户 - 用户名: test, 密码: test123"
    echo
    echo "开发工具:"
    echo "  ./run-tests.sh          # 运行测试"
    echo "  code .                  # 打开VS Code"
    echo
    echo "项目结构:"
    echo "  backend/                # FastAPI后端"
    echo "  frontend/               # Vue3前端"
    echo "  scripts/                # 部署脚本"
    echo "  docs/                   # 文档"
    echo
    log_warning "开发环境仅用于开发测试，请勿用于生产环境！"
}

# 主函数
main() {
    echo "========================================"
    echo "HB-Panel 开发环境设置"
    echo "========================================"
    echo
    
    check_dependencies
    setup_backend
    setup_frontend
    create_dev_scripts
    create_vscode_config
    show_dev_guide
}

# 运行主函数
main "$@"
