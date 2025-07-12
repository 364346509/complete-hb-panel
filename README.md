# HB-Panel - HasBir Linux管理面板

一个现代化的Linux服务器管理面板，基于Vue3 + FastAPI构建。

## 功能特性

### 🖥️ 系统监控
- 实时CPU、内存、磁盘使用率监控
- 网络流量统计
- 系统负载监控
- 进程管理

### 📦 软件市场
- 常用软件一键安装/卸载
- 软件包搜索和管理
- 依赖关系处理
- 安装历史记录

### 🌐 Web环境管理
- LAMP环境一键安装 (Apache + MySQL + PHP)
- LEMP环境一键安装 (Nginx + MySQL + PHP-FPM)
- 混合环境支持 (Nginx + Apache + MySQL + PHP + Redis)
- 自动安全配置和测试页面

### 📁 文件管理
- 在线文件浏览器
- 文件上传/下载
- 文件编辑器
- 权限管理

### ⚙️ 系统服务
- 服务启停控制
- 服务状态监控
- 开机自启管理
- 日志查看

### 👥 用户管理
- 系统用户管理
- SSH密钥管理
- 用户权限配置

### 🔒 安全管理
- 防火墙规则配置
- SSH安全设置
- 登录日志监控
- 安全扫描

## 技术栈

### 后端
- **框架**: FastAPI
- **语言**: Python 3.8+
- **数据库**: SQLite/MySQL
- **认证**: JWT
- **API文档**: Swagger/OpenAPI

### 前端
- **框架**: Vue 3
- **UI库**: Element Plus
- **构建工具**: Vite
- **状态管理**: Pinia
- **路由**: Vue Router 4

## 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- Linux系统 (Ubuntu/CentOS/Debian)

### 安装步骤

1. 克隆项目
```bash
git clone https://github.com/your-repo/hb-panel.git
cd hb-panel
```

2. 安装后端依赖
```bash
cd backend
pip install -r requirements.txt
```

3. 安装前端依赖
```bash
cd frontend
npm install
```

4. 启动开发服务器
```bash
# 后端 (端口8000)
cd backend
python main.py

# 前端 (端口3000)
cd frontend
npm run dev
```

5. 访问面板
打开浏览器访问: http://localhost:3000

## 项目结构

```
hb-panel/
├── backend/                 # FastAPI后端
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务逻辑
│   │   └── utils/          # 工具函数
│   ├── requirements.txt
│   └── main.py
├── frontend/               # Vue3前端
│   ├── src/
│   │   ├── components/     # 组件
│   │   ├── views/          # 页面
│   │   ├── router/         # 路由
│   │   ├── store/          # 状态管理
│   │   └── utils/          # 工具函数
│   ├── package.json
│   └── vite.config.js
├── scripts/                # 部署脚本
├── docs/                   # 文档
└── README.md
```

## 开发指南

### API文档
启动后端服务后，访问 http://localhost:8000/docs 查看API文档

### 贡献指南
1. Fork项目
2. 创建功能分支
3. 提交更改
4. 发起Pull Request

## 许可证
MIT License

## 联系方式
- 项目主页: https://github.com/your-repo/hb-panel
- 问题反馈: https://github.com/your-repo/hb-panel/issues
