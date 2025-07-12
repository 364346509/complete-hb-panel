#!/bin/bash

# HB-Panel 安装脚本
# HasBir Linux管理面板一键安装脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
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

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        log_info "请使用: sudo $0"
        exit 1
    fi
}

# 检查系统版本
check_system() {
    log_info "检查系统环境..."
    
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        log_error "无法检测系统版本"
        exit 1
    fi
    
    log_info "检测到系统: $OS $VER"
    
    # 支持的系统
    case $OS in
        "Ubuntu")
            if [[ $(echo "$VER >= 18.04" | bc -l) -eq 1 ]]; then
                log_success "系统版本支持"
            else
                log_error "Ubuntu版本需要18.04或更高"
                exit 1
            fi
            ;;
        "CentOS Linux"|"Rocky Linux"|"AlmaLinux")
            if [[ $(echo "$VER >= 7" | bc -l) -eq 1 ]]; then
                log_success "系统版本支持"
            else
                log_error "CentOS/Rocky/AlmaLinux版本需要7或更高"
                exit 1
            fi
            ;;
        "Debian GNU/Linux")
            if [[ $(echo "$VER >= 9" | bc -l) -eq 1 ]]; then
                log_success "系统版本支持"
            else
                log_error "Debian版本需要9或更高"
                exit 1
            fi
            ;;
        *)
            log_warning "未测试的系统，可能存在兼容性问题"
            ;;
    esac
}

# 安装依赖
install_dependencies() {
    log_info "安装系统依赖..."
    
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        apt-get update
        apt-get install -y curl wget git python3 python3-pip python3-venv nodejs npm supervisor nginx
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        yum update -y
        yum install -y curl wget git python3 python3-pip nodejs npm supervisor nginx
    elif command -v dnf &> /dev/null; then
        # Fedora/Rocky/AlmaLinux
        dnf update -y
        dnf install -y curl wget git python3 python3-pip nodejs npm supervisor nginx
    else
        log_error "不支持的包管理器"
        exit 1
    fi
    
    log_success "系统依赖安装完成"
}

# 创建用户和目录
setup_user() {
    log_info "创建HB-Panel用户和目录..."
    
    # 创建用户
    if ! id "hbpanel" &>/dev/null; then
        useradd -r -s /bin/bash -d /opt/hb-panel hbpanel
        log_success "用户hbpanel创建成功"
    else
        log_info "用户hbpanel已存在"
    fi
    
    # 创建目录
    mkdir -p /opt/hb-panel
    mkdir -p /var/log/hb-panel
    mkdir -p /etc/hb-panel
    
    # 设置权限
    chown -R hbpanel:hbpanel /opt/hb-panel
    chown -R hbpanel:hbpanel /var/log/hb-panel
    
    log_success "目录结构创建完成"
}

# 安装HB-Panel
install_hbpanel() {
    log_info "安装HB-Panel..."
    
    cd /opt/hb-panel
    
    # 如果是从git克隆
    if [[ -d ".git" ]]; then
        log_info "更新代码..."
        sudo -u hbpanel git pull
    else
        log_info "下载代码..."
        # 这里应该是实际的git仓库地址
        sudo -u hbpanel git clone https://github.com/your-repo/hb-panel.git .
    fi
    
    # 安装后端依赖
    log_info "安装Python依赖..."
    cd /opt/hb-panel/backend
    sudo -u hbpanel python3 -m venv venv
    sudo -u hbpanel ./venv/bin/pip install -r requirements.txt
    
    # 安装前端依赖
    log_info "安装Node.js依赖..."
    cd /opt/hb-panel/frontend
    sudo -u hbpanel npm install
    
    # 构建前端
    log_info "构建前端..."
    sudo -u hbpanel npm run build
    
    log_success "HB-Panel安装完成"
}

# 配置数据库
setup_database() {
    log_info "初始化数据库..."
    
    cd /opt/hb-panel/backend
    
    # 创建数据库
    sudo -u hbpanel ./venv/bin/python -c "
from app.core.database import init_db
import asyncio
asyncio.run(init_db())
print('数据库初始化完成')
"
    
    # 创建默认管理员用户
    sudo -u hbpanel ./venv/bin/python -c "
from app.core.database import SessionLocal
from app.services.user_service import UserService

db = SessionLocal()
user_service = UserService(db)

# 检查是否已有管理员用户
admin = user_service.get_user_by_username('admin')
if not admin:
    admin = user_service.create_user(
        username='admin',
        email='admin@hbpanel.local',
        password='admin123',
        full_name='系统管理员',
        is_superuser=True
    )
    print('默认管理员用户创建成功')
    print('用户名: admin')
    print('密码: admin123')
    print('请登录后立即修改密码！')
else:
    print('管理员用户已存在')

db.close()
"
    
    log_success "数据库配置完成"
}

# 配置Nginx
setup_nginx() {
    log_info "配置Nginx..."
    
    cat > /etc/nginx/sites-available/hb-panel << 'EOF'
server {
    listen 80;
    server_name _;
    
    # 前端静态文件
    location / {
        root /opt/hb-panel/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        root /opt/hb-panel/frontend/dist;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF
    
    # 启用站点
    ln -sf /etc/nginx/sites-available/hb-panel /etc/nginx/sites-enabled/
    
    # 删除默认站点
    rm -f /etc/nginx/sites-enabled/default
    
    # 测试配置
    nginx -t
    
    log_success "Nginx配置完成"
}

# 配置Supervisor
setup_supervisor() {
    log_info "配置Supervisor..."
    
    cat > /etc/supervisor/conf.d/hb-panel.conf << 'EOF'
[program:hb-panel-backend]
command=/opt/hb-panel/backend/venv/bin/python main.py
directory=/opt/hb-panel/backend
user=hbpanel
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/hb-panel/backend.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5
environment=PYTHONPATH="/opt/hb-panel/backend"
EOF
    
    log_success "Supervisor配置完成"
}

# 配置防火墙
setup_firewall() {
    log_info "配置防火墙..."
    
    if command -v ufw &> /dev/null; then
        # Ubuntu防火墙
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw --force enable
    elif command -v firewall-cmd &> /dev/null; then
        # CentOS/RHEL防火墙
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --reload
    fi
    
    log_success "防火墙配置完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 重新加载Supervisor配置
    supervisorctl reread
    supervisorctl update
    
    # 启动服务
    systemctl enable nginx
    systemctl restart nginx
    systemctl enable supervisor
    systemctl restart supervisor
    
    # 启动HB-Panel后端
    supervisorctl start hb-panel-backend
    
    log_success "服务启动完成"
}

# 显示安装结果
show_result() {
    log_success "HB-Panel安装完成！"
    echo
    echo "========================================"
    echo "访问信息:"
    echo "  URL: http://$(hostname -I | awk '{print $1}')"
    echo "  用户名: admin"
    echo "  密码: admin123"
    echo "========================================"
    echo
    log_warning "请立即登录并修改默认密码！"
    echo
    echo "服务管理命令:"
    echo "  查看状态: supervisorctl status hb-panel-backend"
    echo "  重启后端: supervisorctl restart hb-panel-backend"
    echo "  查看日志: tail -f /var/log/hb-panel/backend.log"
    echo "  重启Nginx: systemctl restart nginx"
    echo
}

# 主函数
main() {
    echo "========================================"
    echo "HB-Panel 安装脚本"
    echo "HasBir Linux管理面板"
    echo "========================================"
    echo
    
    check_root
    check_system
    install_dependencies
    setup_user
    install_hbpanel
    setup_database
    setup_nginx
    setup_supervisor
    setup_firewall
    start_services
    show_result
}

# 运行主函数
main "$@"
