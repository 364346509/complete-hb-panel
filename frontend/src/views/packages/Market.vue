<template>
  <div class="package-market">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>软件市场</span>
          <div class="header-actions">
            <el-input
              v-model="searchQuery"
              placeholder="搜索软件包..."
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
      </template>

      <!-- 分类筛选 -->
      <div class="category-filter">
        <el-button-group>
          <el-button
            v-for="category in categories"
            :key="category.name"
            :type="selectedCategory === category.name ? 'primary' : ''"
            @click="selectCategory(category.name)"
          >
            {{ category.display_name }}
          </el-button>
        </el-button-group>
      </div>

      <!-- 软件包列表 -->
      <div class="package-list" v-loading="loading">
        <el-row :gutter="20">
          <el-col :span="8" v-for="pkg in packages" :key="pkg.id">
            <el-card class="package-card" shadow="hover">
              <div class="package-header">
                <h3>{{ pkg.display_name || pkg.name }}</h3>
                <el-tag :type="getStatusType(pkg.status)" size="small">
                  {{ getStatusText(pkg.status) }}
                </el-tag>
              </div>
              
              <div class="package-info">
                <p class="package-description">{{ pkg.description || '暂无描述' }}</p>
                <div class="package-meta">
                  <span class="package-version">版本: {{ pkg.version || 'N/A' }}</span>
                  <span class="package-size">大小: {{ formatSize(pkg.size) }}</span>
                </div>
              </div>
              
              <div class="package-actions">
                <el-button
                  v-if="pkg.status === 'not_installed'"
                  type="primary"
                  size="small"
                  @click="installPackage(pkg)"
                  :loading="isInstalling(pkg.name)"
                >
                  安装
                </el-button>
                <el-button
                  v-else-if="pkg.status === 'installed'"
                  type="danger"
                  size="small"
                  @click="uninstallPackage(pkg)"
                  :loading="isInstalling(pkg.name)"
                >
                  卸载
                </el-button>
                <el-button
                  v-else-if="pkg.status === 'upgradable'"
                  type="warning"
                  size="small"
                  @click="upgradePackage(pkg)"
                  :loading="isInstalling(pkg.name)"
                >
                  升级
                </el-button>
                <el-button size="small" @click="showPackageDetails(pkg)">
                  详情
                </el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>

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
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPackages, getPackageCategories, installPackage as apiInstallPackage, getInstallTask } from '@/api/packages'

const loading = ref(false)
const searchQuery = ref('')
const selectedCategory = ref('')
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)

const categories = ref([
  { name: '', display_name: '全部' }
])
const packages = ref([])
const installingPackages = ref(new Set())

const installDialogVisible = ref(false)
const currentTask = reactive({
  task_id: '',
  package_name: '',
  action: '',
  status: '',
  progress: 0,
  log_output: ''
})

// 获取软件包分类
const fetchCategories = async () => {
  try {
    const response = await getPackageCategories()
    categories.value = [
      { name: '', display_name: '全部' },
      ...response.data
    ]
  } catch (error) {
    console.error('获取分类失败:', error)
  }
}

// 获取软件包列表
const fetchPackages = async () => {
  loading.value = true
  try {
    const response = await getPackages({
      category: selectedCategory.value || undefined,
      search: searchQuery.value || undefined,
      page: currentPage.value,
      size: pageSize.value
    })
    packages.value = response.data
    total.value = response.total || response.data.length
  } catch (error) {
    ElMessage.error('获取软件包列表失败')
  } finally {
    loading.value = false
  }
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
