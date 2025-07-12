# Agent B (前端开发) 任务清单

## 🎯 当前优先任务

### 1. 网站管理界面 (高优先级)
- [ ] 网站列表页面 (`frontend/src/views/websites/List.vue`)
- [ ] 网站创建向导 (`frontend/src/views/websites/Create.vue`)
- [ ] 网站详情配置 (`frontend/src/views/websites/Detail.vue`)
- [ ] 域名管理界面
- [ ] SSL证书配置界面

### 2. 数据库管理界面 (高优先级)
- [ ] 数据库列表 (`frontend/src/views/databases/List.vue`)
- [ ] 数据库创建 (`frontend/src/views/databases/Create.vue`)
- [ ] phpMyAdmin集成界面
- [ ] 数据库备份管理
- [ ] 用户权限配置

### 3. 宝塔风格仪表盘 (高优先级)
- [ ] 主仪表盘重设计 (`frontend/src/views/Dashboard.vue`)
- [ ] 系统状态卡片组件
- [ ] 快速操作面板
- [ ] 实时监控图表
- [ ] 最近操作日志

### 4. 软件商店界面 (中优先级)
- [ ] 软件分类展示
- [ ] 一键安装界面
- [ ] 安装进度显示
- [ ] 已安装软件管理

## 📁 需要创建的文件

```
frontend/src/
├── views/
│   ├── websites/
│   │   ├── List.vue       # 网站列表
│   │   ├── Create.vue     # 创建网站
│   │   ├── Detail.vue     # 网站详情
│   │   └── SSL.vue        # SSL管理
│   ├── databases/
│   │   ├── List.vue       # 数据库列表
│   │   ├── Create.vue     # 创建数据库
│   │   ├── Backup.vue     # 备份管理
│   │   └── Users.vue      # 用户管理
│   ├── software/
│   │   ├── Store.vue      # 软件商店
│   │   ├── Installed.vue  # 已安装
│   │   └── Environment.vue# 环境配置
│   └── security/
│       ├── Firewall.vue   # 防火墙
│       ├── SSH.vue        # SSH配置
│       └── SSL.vue        # SSL证书
├── components/
│   ├── WebsiteCard.vue    # 网站卡片
│   ├── DatabaseCard.vue   # 数据库卡片
│   ├── StatusCard.vue     # 状态卡片
│   └── QuickActions.vue   # 快速操作
├── api/
│   ├── websites.js        # 网站API
│   ├── databases.js       # 数据库API
│   ├── software.js        # 软件API
│   └── ssl.js            # SSL API
└── utils/
    ├── websiteUtils.js    # 网站工具函数
    └── formatters.js      # 格式化工具
```

## 🎨 UI设计要求

### 宝塔面板风格
- 使用蓝色主题色 (#1890ff)
- 卡片式布局设计
- 清晰的导航结构
- 响应式设计
- 图标使用Element Plus Icons

### 组件规范
- 统一的卡片样式
- 一致的按钮风格
- 标准的表单布局
- 友好的错误提示
- 加载状态显示

## 🔧 开发环境设置

```bash
# 切换到前端分支
git checkout feature/frontend-ui

# 安装依赖
cd frontend
npm install

# 启动开发服务器
npm run dev
```

## 📱 页面布局设计

### 主仪表盘布局
```
┌─────────────────────────────────────┐
│ 顶部导航栏                           │
├─────────────────────────────────────┤
│ 系统状态卡片 (CPU/内存/磁盘/网络)      │
├─────────────────────────────────────┤
│ 快速操作 │ 最近操作 │ 系统信息        │
├─────────────────────────────────────┤
│ 监控图表 (CPU/内存使用趋势)           │
└─────────────────────────────────────┘
```

### 网站管理布局
```
┌─────────────────────────────────────┐
│ 网站列表 + 创建按钮                   │
├─────────────────────────────────────┤
│ 网站卡片 │ 网站卡片 │ 网站卡片        │
│ (域名)   │ (状态)   │ (PHP版本)      │
├─────────────────────────────────────┤
│ 分页导航                            │
└─────────────────────────────────────┘
```

## 🔄 API接口约定

与Agent A协调的API接口格式：

```javascript
// 网站管理API
GET    /api/v1/websites          // 获取网站列表
POST   /api/v1/websites          // 创建网站
GET    /api/v1/websites/{id}     // 获取网站详情
PUT    /api/v1/websites/{id}     // 更新网站配置
DELETE /api/v1/websites/{id}     // 删除网站

// 数据库管理API
GET    /api/v1/databases         // 获取数据库列表
POST   /api/v1/databases         // 创建数据库
DELETE /api/v1/databases/{id}    // 删除数据库
```

## 📊 进度报告

每日提交时请更新进度：
- [ ] 任务1: 主仪表盘重设计 - 进度 0%
- [ ] 任务2: 网站管理界面 - 进度 0%
- [ ] 任务3: 数据库管理界面 - 进度 0%
- [ ] 任务4: 软件商店界面 - 进度 0%

## 🔄 同步计划

- **每日同步**: 晚上推送当日代码
- **接口对接**: 与Agent A协调API接口
- **UI审查**: 定期进行界面review
- **用户测试**: 前后端联调测试
