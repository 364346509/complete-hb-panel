<template>
  <div class="software-store">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <div class="header-left">
        <h2>软件商店</h2>
        <span class="subtitle">一键安装常用软件和运行环境</span>
      </div>
      <div class="header-right">
        <el-input
          v-model="searchQuery"
          placeholder="搜索软件..."
          style="width: 300px; margin-right: 16px;"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="refreshPackages" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 快速安装环境 -->
    <div class="quick-install-section">
      <h3>一键部署环境</h3>
      <el-row :gutter="16">
        <el-col :span="8" v-for="env in environments" :key="env.name">
          <div class="environment-card" @click="installEnvironment(env)">
            <div class="env-icon">
              <img :src="env.icon" :alt="env.name" />
            </div>
            <div class="env-info">
              <h4>{{ env.name }}</h4>
              <p>{{ env.description }}</p>
              <div class="env-components">
                <el-tag v-for="component in env.components" :key="component" size="small">
                  {{ component }}
                </el-tag>
              </div>
            </div>
            <div class="env-action">
              <el-button type="primary" size="small">
                {{ env.installed ? '已安装' : '一键安装' }}
              </el-button>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 软件分类 -->
    <div class="software-categories">
      <div class="category-tabs">
        <el-tabs v-model="activeCategory" @tab-change="handleCategoryChange">
          <el-tab-pane
            v-for="category in categories"
            :key="category.name"
            :label="category.display_name"
            :name="category.name"
          >
            <!-- 软件列表 -->
            <div class="software-grid" v-loading="loading">
              <div v-for="software in filteredSoftware" :key="software.id" class="software-card">
                <div class="software-header">
                  <div class="software-icon">
                    <img :src="software.icon" :alt="software.name" />
                  </div>
                  <div class="software-info">
                    <h4>{{ software.display_name }}</h4>
                    <p class="software-desc">{{ software.description }}</p>
                    <div class="software-meta">
                      <span class="version">v{{ software.version }}</span>
                      <span class="size">{{ formatSize(software.size) }}</span>
                    </div>
                  </div>
                  <div class="software-status">
                    <el-tag :type="getStatusType(software.status)" size="small">
                      {{ getStatusText(software.status) }}
                    </el-tag>
                  </div>
                </div>

                <div class="software-actions">
                  <el-button
                    v-if="software.status === 'not_installed'"
                    type="primary"
                    size="small"
                    @click="installSoftware(software)"
                    :loading="isInstalling(software.name)"
                    style="width: 100%;"
                  >
                    {{ isInstalling(software.name) ? '安装中...' : '安装' }}
                  </el-button>
                  <el-button
                    v-else-if="software.status === 'installed'"
                    type="success"
                    size="small"
                    disabled
                    style="width: 100%;"
                  >
                    已安装
                  </el-button>
                  <div v-else-if="software.status === 'installed'" class="installed-actions">
                    <el-button size="small" @click="manageSoftware(software)">管理</el-button>
                    <el-button size="small" type="danger" @click="uninstallSoftware(software)">卸载</el-button>
                  </div>
                </div>

                <div class="software-features" v-if="software.features">
                  <div class="feature-item" v-for="feature in software.features" :key="feature">
                    <el-icon><Check /></el-icon>
                    <span>{{ feature }}</span>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

        <!-- 分页 -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="total"
            :page-sizes="[12, 24, 48]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </el-card>

    <!-- 安装进度对话框 -->
    <el-dialog
      v-model="installDialogVisible"
      title="安装进度"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="install-progress">
        <div class="progress-info">
          <span>正在{{ currentTask.action }}{{ currentTask.package_name }}...</span>
          <span>{{ currentTask.progress }}%</span>
        </div>
        <el-progress :percentage="currentTask.progress" />
        <div class="progress-log" v-if="currentTask.log_output">
          <pre>{{ currentTask.log_output }}</pre>
        </div>
      </div>
      <template #footer>
        <el-button @click="installDialogVisible = false" :disabled="currentTask.status === 'installing'">
          {{ currentTask.status === 'installing' ? '安装中...' : '关闭' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPackages, getPackageCategories, installPackage as apiInstallPackage, getInstallTask } from '@/api/packages'

const loading = ref(false)
const searchQuery = ref('')
const selectedCategory = ref('')
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)

// 一键部署环境
const environments = ref([
  {
    name: 'LAMP',
    description: 'Linux + Apache + MySQL + PHP 经典组合',
    icon: '/icons/lamp.png',
    components: ['Apache', 'MySQL', 'PHP'],
    installed: false
  },
  {
    name: 'LEMP',
    description: 'Linux + Nginx + MySQL + PHP 高性能组合',
    icon: '/icons/lemp.png',
    components: ['Nginx', 'MySQL', 'PHP'],
    installed: false
  },
  {
    name: 'LNMP',
    description: 'Linux + Nginx + MySQL + PHP + Redis',
    icon: '/icons/lnmp.png',
    components: ['Nginx', 'MySQL', 'PHP', 'Redis'],
    installed: true
  }
])

// 软件分类
const categories = ref([
  { name: 'web', display_name: 'Web服务器' },
  { name: 'database', display_name: '数据库' },
  { name: 'runtime', display_name: '运行环境' },
  { name: 'cache', display_name: '缓存服务' },
  { name: 'tools', display_name: '系统工具' },
  { name: 'security', display_name: '安全软件' }
])

const activeCategory = ref('web')

// 软件列表
const allSoftware = ref([
  // Web服务器
  {
    id: 1,
    name: 'nginx',
    display_name: 'Nginx',
    description: '高性能Web服务器和反向代理',
    category: 'web',
    version: '1.24.0',
    size: 2048000,
    status: 'installed',
    icon: '/icons/nginx.png',
    features: ['高并发', '负载均衡', '反向代理', '静态文件服务']
  },
  {
    id: 2,
    name: 'apache',
    display_name: 'Apache',
    description: '世界上最流行的Web服务器',
    category: 'web',
    version: '2.4.57',
    size: 5120000,
    status: 'not_installed',
    icon: '/icons/apache.png',
    features: ['模块化', '.htaccess支持', '虚拟主机', 'SSL/TLS']
  },
  // 数据库
  {
    id: 3,
    name: 'mysql',
    display_name: 'MySQL',
    description: '最流行的开源关系型数据库',
    category: 'database',
    version: '8.0.34',
    size: 204800000,
    status: 'installed',
    icon: '/icons/mysql.png',
    features: ['ACID事务', '复制', '分区', '存储引擎']
  },
  {
    id: 4,
    name: 'postgresql',
    display_name: 'PostgreSQL',
    description: '先进的开源关系型数据库',
    category: 'database',
    version: '15.4',
    size: 153600000,
    status: 'not_installed',
    icon: '/icons/postgresql.png',
    features: ['JSON支持', '全文搜索', '地理信息', '扩展性']
  },
  // 运行环境
  {
    id: 5,
    name: 'php',
    display_name: 'PHP',
    description: '流行的Web开发语言',
    category: 'runtime',
    version: '8.2.10',
    size: 51200000,
    status: 'installed',
    icon: '/icons/php.png',
    features: ['多版本', 'FPM', '扩展丰富', 'OPcache']
  },
  {
    id: 6,
    name: 'nodejs',
    display_name: 'Node.js',
    description: 'JavaScript运行时环境',
    category: 'runtime',
    version: '18.17.1',
    size: 30720000,
    status: 'not_installed',
    icon: '/icons/nodejs.png',
    features: ['事件驱动', '非阻塞I/O', 'NPM包管理', 'V8引擎']
  },
  // 缓存服务
  {
    id: 7,
    name: 'redis',
    display_name: 'Redis',
    description: '高性能内存数据库',
    category: 'cache',
    version: '7.2.1',
    size: 10240000,
    status: 'installed',
    icon: '/icons/redis.png',
    features: ['内存存储', '持久化', '集群', '发布订阅']
  },
  {
    id: 8,
    name: 'memcached',
    display_name: 'Memcached',
    description: '分布式内存缓存系统',
    category: 'cache',
    version: '1.6.21',
    size: 1024000,
    status: 'not_installed',
    icon: '/icons/memcached.png',
    features: ['分布式', '高速缓存', '简单协议', '多线程']
  }
])

const installingPackages = ref(new Set())

// 计算属性
const filteredSoftware = computed(() => {
  return allSoftware.value.filter(software => {
    const matchCategory = activeCategory.value === 'all' || software.category === activeCategory.value
    const matchSearch = !searchQuery.value ||
      software.display_name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      software.description.toLowerCase().includes(searchQuery.value.toLowerCase())
    return matchCategory && matchSearch
  })
})

const installDialogVisible = ref(false)
const currentTask = reactive({
  task_id: '',
  package_name: '',
  action: '',
  status: '',
  progress: 0,
  log_output: ''
})

// 安装环境
const installEnvironment = async (env) => {
  if (env.installed) {
    ElMessage.info('环境已安装')
    return
  }

  try {
    await ElMessageBox.confirm(`确定要安装 ${env.name} 环境吗？`, '确认安装', {
      type: 'warning'
    })

    ElMessage.info(`开始安装 ${env.name} 环境...`)
    // 模拟安装过程
    setTimeout(() => {
      env.installed = true
      ElMessage.success(`${env.name} 环境安装成功`)
    }, 3000)

  } catch (error) {
    // 用户取消
  }
}

// 处理分类切换
const handleCategoryChange = (category) => {
  activeCategory.value = category
}

// 安装软件
const installSoftware = async (software) => {
  try {
    await ElMessageBox.confirm(`确定要安装 ${software.display_name} 吗？`, '确认安装', {
      type: 'warning'
    })

    installingPackages.value.add(software.name)
    ElMessage.info(`开始安装 ${software.display_name}...`)

    // 模拟安装过程
    setTimeout(() => {
      software.status = 'installed'
      installingPackages.value.delete(software.name)
      ElMessage.success(`${software.display_name} 安装成功`)
    }, 3000)

  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('安装失败')
    }
    installingPackages.value.delete(software.name)
  }
}

// 卸载软件
const uninstallSoftware = async (software) => {
  try {
    await ElMessageBox.confirm(`确定要卸载 ${software.display_name} 吗？`, '确认卸载', {
      type: 'warning'
    })

    software.status = 'not_installed'
    ElMessage.success(`${software.display_name} 卸载成功`)

  } catch (error) {
    // 用户取消
  }
}

// 管理软件
const manageSoftware = (software) => {
  ElMessage.info(`打开 ${software.display_name} 管理界面`)
  // 跳转到软件管理页面
}

// 搜索处理
const handleSearch = () => {
  currentPage.value = 1
  fetchPackages()
}

// 选择分类
const selectCategory = (category) => {
  selectedCategory.value = category
  currentPage.value = 1
  fetchPackages()
}

// 刷新软件包
const refreshPackages = () => {
  fetchPackages()
}

// 分页处理
const handleSizeChange = (size) => {
  pageSize.value = size
  fetchPackages()
}

const handleCurrentChange = (page) => {
  currentPage.value = page
  fetchPackages()
}

// 安装软件包
const installPackage = async (pkg) => {
  try {
    await ElMessageBox.confirm(`确定要安装 ${pkg.display_name || pkg.name} 吗？`, '确认安装', {
      type: 'warning'
    })

    installingPackages.value.add(pkg.name)
    
    const response = await apiInstallPackage({
      package_name: pkg.name,
      action: 'install'
    })

    currentTask.task_id = response.data.task_id
    currentTask.package_name = pkg.name
    currentTask.action = '安装'
    currentTask.status = 'installing'
    currentTask.progress = 0
    currentTask.log_output = ''

    installDialogVisible.value = true
    
    // 轮询任务状态
    pollTaskStatus()

  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('安装失败')
    }
    installingPackages.value.delete(pkg.name)
  }
}

// 卸载软件包
const uninstallPackage = async (pkg) => {
  try {
    await ElMessageBox.confirm(`确定要卸载 ${pkg.display_name || pkg.name} 吗？`, '确认卸载', {
      type: 'warning'
    })

    installingPackages.value.add(pkg.name)
    
    const response = await apiInstallPackage({
      package_name: pkg.name,
      action: 'uninstall'
    })

    currentTask.task_id = response.data.task_id
    currentTask.package_name = pkg.name
    currentTask.action = '卸载'
    currentTask.status = 'installing'
    currentTask.progress = 0
    currentTask.log_output = ''

    installDialogVisible.value = true
    pollTaskStatus()

  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('卸载失败')
    }
    installingPackages.value.delete(pkg.name)
  }
}

// 升级软件包
const upgradePackage = async (pkg) => {
  try {
    await ElMessageBox.confirm(`确定要升级 ${pkg.display_name || pkg.name} 吗？`, '确认升级', {
      type: 'warning'
    })

    installingPackages.value.add(pkg.name)
    
    const response = await apiInstallPackage({
      package_name: pkg.name,
      action: 'upgrade'
    })

    currentTask.task_id = response.data.task_id
    currentTask.package_name = pkg.name
    currentTask.action = '升级'
    currentTask.status = 'installing'
    currentTask.progress = 0
    currentTask.log_output = ''

    installDialogVisible.value = true
    pollTaskStatus()

  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('升级失败')
    }
    installingPackages.value.delete(pkg.name)
  }
}

// 轮询任务状态
const pollTaskStatus = async () => {
  try {
    const response = await getInstallTask(currentTask.task_id)
    const task = response.data

    currentTask.status = task.status
    currentTask.progress = task.progress
    currentTask.log_output = task.log_output

    if (task.status === 'success') {
      ElMessage.success(`${currentTask.action}完成`)
      installingPackages.value.delete(currentTask.package_name)
      fetchPackages() // 刷新列表
    } else if (task.status === 'failed') {
      ElMessage.error(`${currentTask.action}失败: ${task.error_message}`)
      installingPackages.value.delete(currentTask.package_name)
    } else if (task.status === 'installing') {
      // 继续轮询
      setTimeout(pollTaskStatus, 2000)
    }
  } catch (error) {
    ElMessage.error('获取任务状态失败')
    installingPackages.value.delete(currentTask.package_name)
  }
}

// 检查是否正在安装
const isInstalling = (packageName) => {
  return installingPackages.value.has(packageName)
}

// 显示软件包详情
const showPackageDetails = (pkg) => {
  ElMessageBox.alert(
    `
    <p><strong>名称:</strong> ${pkg.display_name || pkg.name}</p>
    <p><strong>版本:</strong> ${pkg.version || 'N/A'}</p>
    <p><strong>大小:</strong> ${formatSize(pkg.size)}</p>
    <p><strong>分类:</strong> ${pkg.category}</p>
    <p><strong>描述:</strong> ${pkg.description || '暂无描述'}</p>
    ${pkg.homepage ? `<p><strong>主页:</strong> <a href="${pkg.homepage}" target="_blank">${pkg.homepage}</a></p>` : ''}
    `,
    '软件包详情',
    {
      dangerouslyUseHTMLString: true
    }
  )
}

// 获取状态类型
const getStatusType = (status) => {
  const types = {
    'installed': 'success',
    'not_installed': 'info',
    'upgradable': 'warning',
    'broken': 'danger'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const texts = {
    'installed': '已安装',
    'not_installed': '未安装',
    'upgradable': '可升级',
    'broken': '损坏'
  }
  return texts[status] || '未知'
}

// 格式化大小
const formatSize = (bytes) => {
  if (!bytes) return 'N/A'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

onMounted(() => {
  fetchCategories()
  fetchPackages()
})
</script>

<style lang="scss" scoped>
.package-market {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .category-filter {
    margin-bottom: 20px;
  }

  .package-list {
    .package-card {
      margin-bottom: 20px;
      height: 280px;
      
      .package-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        
        h3 {
          margin: 0;
          font-size: 16px;
          color: #303133;
        }
      }
      
      .package-info {
        margin-bottom: 16px;
        
        .package-description {
          color: #606266;
          font-size: 14px;
          line-height: 1.5;
          margin-bottom: 8px;
          height: 60px;
          overflow: hidden;
          display: -webkit-box;
          -webkit-line-clamp: 3;
          -webkit-box-orient: vertical;
        }
        
        .package-meta {
          display: flex;
          justify-content: space-between;
          font-size: 12px;
          color: #909399;
        }
      }
      
      .package-actions {
        display: flex;
        gap: 8px;
        
        .el-button {
          flex: 1;
        }
      }
    }
    
    .pagination-container {
      display: flex;
      justify-content: center;
      margin-top: 30px;
    }
  }

  .install-progress {
    .progress-info {
      display: flex;
      justify-content: space-between;
      margin-bottom: 12px;
      font-size: 14px;
    }
    
    .progress-log {
      margin-top: 16px;
      max-height: 200px;
      overflow-y: auto;
      background: #f5f5f5;
      padding: 12px;
      border-radius: 4px;
      
      pre {
        margin: 0;
        font-size: 12px;
        line-height: 1.4;
        white-space: pre-wrap;
      }
    }
  }
}
</style>
