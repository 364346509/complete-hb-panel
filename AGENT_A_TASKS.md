# Agent A (后端开发) 任务清单

## 🎯 当前优先任务

### 1. 网站管理模块 (高优先级)
- [ ] 创建网站数据模型 (`backend/app/models/website.py`)
- [ ] 实现网站管理API (`backend/app/api/endpoints/websites.py`)
- [ ] 网站创建、删除、配置功能
- [ ] 域名绑定和SSL证书配置
- [ ] PHP版本切换功能

### 2. 数据库管理模块 (高优先级)
- [ ] 数据库模型设计 (`backend/app/models/database.py`)
- [ ] 数据库管理API (`backend/app/api/endpoints/databases.py`)
- [ ] MySQL/MariaDB连接管理
- [ ] 数据库备份和恢复
- [ ] 用户权限管理

### 3. SSL证书管理 (中优先级)
- [ ] SSL证书模型 (`backend/app/models/ssl.py`)
- [ ] Let's Encrypt自动申请
- [ ] 证书安装和续期
- [ ] 证书状态监控

### 4. 系统监控增强 (中优先级)
- [ ] 网站访问统计
- [ ] 数据库性能监控
- [ ] 服务状态检查
- [ ] 资源使用告警

## 📁 需要创建的文件

```
backend/app/
├── models/
│   ├── website.py          # 网站管理模型
│   ├── database.py         # 数据库管理模型
│   ├── ssl.py             # SSL证书模型
│   └── monitor.py         # 监控数据模型
├── api/endpoints/
│   ├── websites.py        # 网站管理API
│   ├── databases.py       # 数据库管理API
│   ├── ssl.py            # SSL证书API
│   └── monitor.py        # 监控API
├── services/
│   ├── website_service.py # 网站管理服务
│   ├── database_service.py# 数据库管理服务
│   ├── ssl_service.py     # SSL证书服务
│   └── monitor_service.py # 监控服务
└── utils/
    ├── nginx_config.py    # Nginx配置生成
    ├── apache_config.py   # Apache配置生成
    └── mysql_manager.py   # MySQL管理工具
```

## 🔧 开发环境设置

```bash
# 切换到后端分支
git checkout feature/backend-core

# 安装依赖
cd backend
pip install -r requirements.txt

# 启动开发服务器
python main.py
```

## 📝 代码规范

- 所有API使用RESTful设计
- 数据模型使用SQLAlchemy ORM
- 异步函数使用async/await
- 错误处理使用HTTPException
- 日志记录使用Python logging
- 注释使用中文

## 🧪 测试要求

- 每个API端点编写单元测试
- 数据库操作编写集成测试
- 使用pytest测试框架
- 测试覆盖率 > 80%

## 📊 进度报告

每日提交时请更新进度：
- [ ] 任务1: 网站管理模型 - 进度 0%
- [ ] 任务2: 网站管理API - 进度 0%
- [ ] 任务3: 数据库管理 - 进度 0%
- [ ] 任务4: SSL证书管理 - 进度 0%

## 🔄 同步计划

- **每日同步**: 晚上推送当日代码
- **接口对接**: 与Agent B协调API接口
- **代码审查**: 定期进行代码review
- **集成测试**: 前后端联调测试
