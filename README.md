# HB-Panel - 宝塔面板开源替代方案

一个功能完整的Linux服务器管理面板，基于Vue3 + FastAPI构建，提供与宝塔面板相同的功能体验。

## 🚀 核心特性

### 🌐 网站管理
- 网站一键创建和管理
- 域名绑定和SSL证书配置
- PHP版本切换 (5.6-8.2)
- 伪静态规则配置
- 网站备份和恢复
- 流量统计和访问日志

### 🗄️ 数据库管理
- MySQL/MariaDB数据库管理
- 数据库创建、删除、备份
- phpMyAdmin在线管理
- 数据库用户权限管理
- SQL文件导入导出
- 数据库性能监控

### 📁 文件管理
- 可视化文件管理器
- 在线代码编辑器
- 文件压缩和解压
- 批量文件操作
- 文件权限管理
- 回收站功能

### 🔧 软件商店
- 一键安装常用软件
- Nginx/Apache/PHP/MySQL
- Redis/Memcached/MongoDB
- Node.js/Python环境
- Docker容器管理
- 软件版本管理

### 🖥️ 系统监控
- 实时系统状态监控
- CPU、内存、磁盘监控
- 网络流量统计
- 进程管理
- 系统负载分析
- 历史数据图表

### 🔒 安全管理
- 防火墙端口管理
- SSH安全配置
- SSL证书管理
- 系统加固
- 入侵检测
- 安全日志分析

### ⏰ 计划任务
- Cron任务管理
- 定时备份
- 日志清理
- 系统维护任务
- 任务执行日志

### 📊 日志管理
- 系统日志查看
- 网站访问日志
- 错误日志分析
- 日志文件管理
- 日志统计分析

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
