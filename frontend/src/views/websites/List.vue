<template>
  <div class="websites-list">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <div class="header-left">
        <h2>网站管理</h2>
        <span class="subtitle">管理您的所有网站</span>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          创建网站
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-cards">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon total">
            <el-icon><Globe /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ websiteStats.total }}</div>
            <div class="stat-label">总网站数</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon running">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ websiteStats.running }}</div>
            <div class="stat-label">运行中</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon stopped">
            <el-icon><CircleClose /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ websiteStats.stopped }}</div>
            <div class="stat-label">已停止</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon ssl">
            <el-icon><Lock /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ websiteStats.ssl }}</div>
            <div class="stat-label">SSL证书</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 网站列表 -->
    <div class="websites-container">
      <div class="list-header">
        <div class="search-bar">
          <el-input
            v-model="searchQuery"
            placeholder="搜索网站名称或域名..."
            style="width: 300px;"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <div class="filter-bar">
          <el-select v-model="statusFilter" placeholder="状态筛选" style="width: 120px;" @change="handleFilter">
            <el-option label="全部" value="" />
            <el-option label="运行中" value="running" />
            <el-option label="已停止" value="stopped" />
          </el-select>
          <el-select v-model="phpFilter" placeholder="PHP版本" style="width: 120px; margin-left: 12px;" @change="handleFilter">
            <el-option label="全部版本" value="" />
            <el-option label="PHP 8.2" value="8.2" />
            <el-option label="PHP 8.1" value="8.1" />
            <el-option label="PHP 7.4" value="7.4" />
          </el-select>
        </div>
      </div>

      <!-- 网站卡片列表 -->
      <div class="websites-grid" v-loading="loading">
        <div v-for="website in websites" :key="website.id" class="website-card">
          <div class="card-header">
            <div class="website-info">
              <h3 class="website-name">{{ website.name }}</h3>
              <p class="website-domain">{{ website.domain }}</p>
            </div>
            <div class="website-status">
              <el-tag :type="website.status === 'running' ? 'success' : 'danger'" size="small">
                {{ website.status === 'running' ? '运行中' : '已停止' }}
              </el-tag>
            </div>
          </div>

          <div class="card-content">
            <div class="website-details">
              <div class="detail-item">
                <span class="label">PHP版本:</span>
                <span class="value">{{ website.php_version }}</span>
              </div>
              <div class="detail-item">
                <span class="label">SSL证书:</span>
                <span class="value">
                  <el-tag v-if="website.ssl_type !== 'none'" type="success" size="small">已配置</el-tag>
                  <el-tag v-else type="info" size="small">未配置</el-tag>
                </span>
              </div>
              <div class="detail-item">
                <span class="label">创建时间:</span>
                <span class="value">{{ formatDate(website.created_at) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">访问量:</span>
                <span class="value">{{ website.total_requests || 0 }} 次</span>
              </div>
            </div>
          </div>

          <div class="card-actions">
            <el-button size="small" @click="manageWebsite(website)">管理</el-button>
            <el-button size="small" @click="viewLogs(website)">日志</el-button>
            <el-button size="small" @click="configSSL(website)">SSL</el-button>
            <el-dropdown @command="handleCommand" trigger="click">
              <el-button size="small">
                更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :command="{action: 'backup', website}">备份网站</el-dropdown-item>
                  <el-dropdown-item :command="{action: 'clone', website}">克隆网站</el-dropdown-item>
                  <el-dropdown-item :command="{action: 'stop', website}" v-if="website.status === 'running'">停止网站</el-dropdown-item>
                  <el-dropdown-item :command="{action: 'start', website}" v-else>启动网站</el-dropdown-item>
                  <el-dropdown-item :command="{action: 'delete', website}" divided>删除网站</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
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

    <!-- 创建网站对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="创建网站"
      width="600px"
      :close-on-click-modal="false"
    >
      <create-website-form 
        @success="handleCreateSuccess"
        @cancel="createDialogVisible = false"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getWebsiteStats, getWebsites, deleteWebsite, startWebsite, stopWebsite, backupWebsite } from '@/api/websites'
import CreateWebsiteForm from '@/components/CreateWebsiteForm.vue'

const router = useRouter()

const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const phpFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)
const createDialogVisible = ref(false)

const websiteStats = ref({
  total: 0,
  running: 0,
  stopped: 0,
  ssl: 0
})

const websites = ref([
  {
    id: 1,
    name: 'example.com',
    domain: 'example.com',
    php_version: '8.1',
    status: 'running',
    ssl_type: 'lets_encrypt',
    created_at: '2024-01-15',
    total_requests: 1250
  },
  {
    id: 2,
    name: 'test.com',
    domain: 'test.com',
    php_version: '7.4',
    status: 'stopped',
    ssl_type: 'none',
    created_at: '2024-01-10',
    total_requests: 890
  }
])

// 方法定义
const showCreateDialog = () => {
  createDialogVisible.value = true
}

const handleSearch = () => {
  // 实现搜索逻辑
  fetchWebsites()
}

const handleFilter = () => {
  // 实现筛选逻辑
  fetchWebsites()
}

const handleSizeChange = (size) => {
  pageSize.value = size
  fetchWebsites()
}

const handleCurrentChange = (page) => {
  currentPage.value = page
  fetchWebsites()
}

const manageWebsite = (website) => {
  router.push(`/websites/${website.id}`)
}

const viewLogs = (website) => {
  router.push(`/websites/${website.id}/logs`)
}

const configSSL = (website) => {
  router.push(`/websites/${website.id}/ssl`)
}

const handleCommand = async (command) => {
  const { action, website } = command
  
  switch (action) {
    case 'backup':
      await backupWebsiteAction(website)
      break
    case 'clone':
      ElMessage.info('开始克隆网站...')
      break
    case 'stop':
      await stopWebsiteAction(website)
      break
    case 'start':
      await startWebsiteAction(website)
      break
    case 'delete':
      await deleteWebsiteAction(website)
      break
  }
}

const stopWebsiteAction = async (website) => {
  try {
    await ElMessageBox.confirm(`确定要停止网站 ${website.name} 吗？`, '确认操作', {
      type: 'warning'
    })

    await stopWebsite(website.id)
    ElMessage.success('网站已停止')
    fetchWebsites()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('停止网站失败')
    }
  }
}

const startWebsiteAction = async (website) => {
  try {
    await startWebsite(website.id)
    ElMessage.success('网站已启动')
    fetchWebsites()
  } catch (error) {
    ElMessage.error('启动网站失败')
  }
}

const deleteWebsiteAction = async (website) => {
  try {
    await ElMessageBox.confirm(`确定要删除网站 ${website.name} 吗？此操作不可恢复！`, '危险操作', {
      type: 'error',
      confirmButtonText: '确定删除',
      confirmButtonClass: 'el-button--danger'
    })

    await deleteWebsite(website.id)
    ElMessage.success('网站已删除')
    fetchWebsites()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除网站失败')
    }
  }
}

const backupWebsiteAction = async (website) => {
  try {
    await backupWebsite(website.id, 'full')
    ElMessage.success('网站备份任务已启动')
  } catch (error) {
    ElMessage.error('启动备份失败')
  }
}

const handleCreateSuccess = () => {
  createDialogVisible.value = false
  ElMessage.success('网站创建成功')
  fetchWebsites()
}

const fetchWebsites = async () => {
  loading.value = true
  try {
    const [websitesResponse, statsResponse] = await Promise.all([
      getWebsites({
        search: searchQuery.value,
        status: statusFilter.value,
        php_version: phpFilter.value,
        page: currentPage.value,
        size: pageSize.value
      }),
      getWebsiteStats()
    ])

    websites.value = websitesResponse.data
    total.value = websitesResponse.total || websitesResponse.data.length
    websiteStats.value = statsResponse.data

  } catch (error) {
    ElMessage.error('获取网站列表失败')
    console.error('获取网站列表失败:', error)
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

onMounted(() => {
  fetchWebsites()
})
</script>

<style lang="scss" scoped>
.websites-list {
  padding: 0;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    
    .header-left {
      h2 {
        margin: 0 0 4px 0;
        font-size: 24px;
        color: #303133;
      }
      
      .subtitle {
        color: #909399;
        font-size: 14px;
      }
    }
  }
  
  .stats-cards {
    margin-bottom: 24px;
    
    .stat-card {
      background: white;
      border-radius: 8px;
      padding: 20px;
      display: flex;
      align-items: center;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      
      .stat-icon {
        width: 48px;
        height: 48px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 16px;
        
        &.total { background: linear-gradient(135deg, #409eff, #66b1ff); }
        &.running { background: linear-gradient(135deg, #67c23a, #85ce61); }
        &.stopped { background: linear-gradient(135deg, #f56c6c, #f78989); }
        &.ssl { background: linear-gradient(135deg, #e6a23c, #ebb563); }
        
        .el-icon {
          color: white;
          font-size: 20px;
        }
      }
      
      .stat-content {
        .stat-number {
          font-size: 24px;
          font-weight: 600;
          color: #303133;
          margin-bottom: 4px;
        }
        
        .stat-label {
          font-size: 14px;
          color: #909399;
        }
      }
    }
  }
  
  .websites-container {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    
    .list-header {
      padding: 20px;
      border-bottom: 1px solid #f0f0f0;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .websites-grid {
      padding: 20px;
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
      gap: 20px;
      
      .website-card {
        border: 1px solid #e4e7ed;
        border-radius: 8px;
        padding: 20px;
        transition: all 0.3s ease;
        
        &:hover {
          border-color: #409eff;
          box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
        }
        
        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 16px;
          
          .website-info {
            .website-name {
              margin: 0 0 4px 0;
              font-size: 16px;
              font-weight: 600;
              color: #303133;
            }
            
            .website-domain {
              margin: 0;
              font-size: 14px;
              color: #409eff;
            }
          }
        }
        
        .card-content {
          margin-bottom: 16px;
          
          .website-details {
            .detail-item {
              display: flex;
              justify-content: space-between;
              margin-bottom: 8px;
              
              &:last-child {
                margin-bottom: 0;
              }
              
              .label {
                font-size: 14px;
                color: #909399;
              }
              
              .value {
                font-size: 14px;
                color: #303133;
                font-weight: 500;
              }
            }
          }
        }
        
        .card-actions {
          display: flex;
          gap: 8px;
          
          .el-button {
            flex: 1;
          }
        }
      }
    }
    
    .pagination-container {
      padding: 20px;
      border-top: 1px solid #f0f0f0;
      display: flex;
      justify-content: center;
    }
  }
}
</style>
