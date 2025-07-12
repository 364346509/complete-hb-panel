#!/bin/bash

# HB-Panel 一键安装脚本
# 支持 Ubuntu 18.04+, CentOS 7+, Debian 9+
# 作者: HB-Panel Team
# 版本: v1.0.0

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

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        log_info "请使用: sudo $0"
        exit 1
    fi
}

# 检测操作系统
detect_os() {
    if [[ -f /etc/redhat-release ]]; then
        OS="centos"
        if grep -q "CentOS Linux 7" /etc/redhat-release; then
            OS_VERSION="7"
        elif grep -q "CentOS Linux 8" /etc/redhat-release; then
            OS_VERSION="8"
        fi
    elif [[ -f /etc/lsb-release ]]; then
        OS="ubuntu"
        OS_VERSION=$(lsb_release -rs)
    elif [[ -f /etc/debian_version ]]; then
        OS="debian"
        OS_VERSION=$(cat /etc/debian_version)
    else
        log_error "不支持的操作系统"
        exit 1
    fi
    
    log_info "检测到操作系统: $OS $OS_VERSION"
}

# 检查系统要求
check_requirements() {
    log_step "检查系统要求..."
    
    # 检查内存
    MEMORY=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    if [[ $MEMORY -lt 1024 ]]; then
        log_warn "内存不足1GB，建议至少2GB内存"
    fi
    
    # 检查磁盘空间
    DISK=$(df -h / | awk 'NR==2{print $4}' | sed 's/G//')
    if [[ ${DISK%.*} -lt 10 ]]; then
        log_warn "磁盘空间不足10GB，建议至少20GB空间"
    fi
    
    log_info "系统要求检查完成"
}

# 安装基础依赖
install_dependencies() {
    log_step "安装基础依赖..."
    
    if [[ $OS == "ubuntu" || $OS == "debian" ]]; then
        apt-get update
        apt-get install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release
    elif [[ $OS == "centos" ]]; then
        yum update -y
        yum install -y curl wget git unzip epel-release
    fi
    
    log_info "基础依赖安装完成"
}

# 安装Docker
install_docker() {
    log_step "安装Docker..."
    
    if command -v docker &> /dev/null; then
        log_info "Docker已安装，跳过安装步骤"
        return
    fi
    
    if [[ $OS == "ubuntu" ]]; then
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    elif [[ $OS == "centos" ]]; then
        yum install -y yum-utils
        yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    elif [[ $OS == "debian" ]]; then
        curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    fi
    
    systemctl start docker
    systemctl enable docker
    
    log_info "Docker安装完成"
}

# 安装Docker Compose
install_docker_compose() {
    log_step "安装Docker Compose..."
    
    if command -v docker-compose &> /dev/null; then
        log_info "Docker Compose已安装，跳过安装步骤"
        return
    fi
    
    DOCKER_COMPOSE_VERSION="2.24.1"
    curl -L "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    log_info "Docker Compose安装完成"
}

# 下载HB-Panel
download_hb_panel() {
    log_step "下载HB-Panel..."
    
    HB_PANEL_DIR="/opt/hb-panel"
    
    if [[ -d $HB_PANEL_DIR ]]; then
        log_warn "HB-Panel目录已存在，正在备份..."
        mv $HB_PANEL_DIR "${HB_PANEL_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    git clone https://github.com/364346509/complete-hb-panel.git $HB_PANEL_DIR
    cd $HB_PANEL_DIR
    
    log_info "HB-Panel下载完成"
}

# 配置环境变量
setup_environment() {
    log_step "配置环境变量..."
    
    cd /opt/hb-panel
    
    # 生成随机密码
    MYSQL_ROOT_PASSWORD=$(openssl rand -base64 32)
    JWT_SECRET_KEY=$(openssl rand -base64 64)
    
    # 创建环境配置文件
    cat > .env << EOF
# 数据库配置
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
MYSQL_DATABASE=hb_panel
MYSQL_USER=hb_panel
MYSQL_PASSWORD=$(openssl rand -base64 32)

# JWT配置
JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 应用配置
APP_NAME=HB-Panel
APP_VERSION=1.0.0
DEBUG=false

# 服务端口
BACKEND_PORT=8000
FRONTEND_PORT=3000
NGINX_PORT=8080

# 域名配置（可选）
DOMAIN=localhost
EOF
    
    log_info "环境变量配置完成"
}

# 启动服务
start_services() {
    log_step "启动HB-Panel服务..."
    
    cd /opt/hb-panel
    
    # 构建并启动服务
    docker-compose up -d --build
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        log_info "HB-Panel服务启动成功"
    else
        log_error "HB-Panel服务启动失败"
        docker-compose logs
        exit 1
    fi
}

# 配置防火墙
setup_firewall() {
    log_step "配置防火墙..."
    
    if command -v ufw &> /dev/null; then
        ufw allow 8080/tcp
        ufw allow 22/tcp
        ufw --force enable
    elif command -v firewall-cmd &> /dev/null; then
        firewall-cmd --permanent --add-port=8080/tcp
        firewall-cmd --permanent --add-port=22/tcp
        firewall-cmd --reload
    fi
    
    log_info "防火墙配置完成"
}

# 创建系统服务
create_systemd_service() {
    log_step "创建系统服务..."
    
    cat > /etc/systemd/system/hb-panel.service << EOF
[Unit]
Description=HB-Panel Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/hb-panel
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable hb-panel
    
    log_info "系统服务创建完成"
}

# 显示安装结果
show_result() {
    log_step "安装完成！"
    
    echo ""
    echo "=========================================="
    echo "🎉 HB-Panel 安装成功！"
    echo "=========================================="
    echo ""
    echo "📱 访问地址: http://$(curl -s ifconfig.me):8080"
    echo "🏠 本地访问: http://localhost:8080"
    echo ""
    echo "👤 默认账号信息:"
    echo "   用户名: admin"
    echo "   密码: admin123"
    echo ""
    echo "📁 安装目录: /opt/hb-panel"
    echo "📋 配置文件: /opt/hb-panel/.env"
    echo ""
    echo "🔧 常用命令:"
    echo "   启动服务: systemctl start hb-panel"
    echo "   停止服务: systemctl stop hb-panel"
    echo "   重启服务: systemctl restart hb-panel"
    echo "   查看状态: systemctl status hb-panel"
    echo "   查看日志: cd /opt/hb-panel && docker-compose logs"
    echo ""
    echo "📚 文档地址: https://github.com/364346509/complete-hb-panel"
    echo "🐛 问题反馈: https://github.com/364346509/complete-hb-panel/issues"
    echo ""
    echo "=========================================="
    echo "感谢使用 HB-Panel！"
    echo "=========================================="
}

# 主函数
main() {
    echo ""
    echo "=========================================="
    echo "🚀 HB-Panel 一键安装脚本"
    echo "=========================================="
    echo ""
    
    check_root
    detect_os
    check_requirements
    install_dependencies
    install_docker
    install_docker_compose
    download_hb_panel
    setup_environment
    start_services
    setup_firewall
    create_systemd_service
    show_result
}

# 执行主函数
main "$@"
