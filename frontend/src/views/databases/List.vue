<template>
  <div class="databases-list">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <div class="header-left">
        <h2>数据库管理</h2>
        <span class="subtitle">管理MySQL数据库和用户</span>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          创建数据库
        </el-button>
        <el-button type="success" @click="openPhpMyAdmin">
          <el-icon><Monitor /></el-icon>
          phpMyAdmin
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-cards">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon total">
            <el-icon><Coin /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ databaseStats.total }}</div>
            <div class="stat-label">数据库总数</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon size">
            <el-icon><PieChart /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ formatSize(databaseStats.totalSize) }}</div>
            <div class="stat-label">总占用空间</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon users">
            <el-icon><User /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ databaseStats.users }}</div>
            <div class="stat-label">数据库用户</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon backups">
            <el-icon><Download /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ databaseStats.backups }}</div>
            <div class="stat-label">备份文件</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 数据库列表 -->
    <div class="databases-container">
      <div class="list-header">
        <div class="search-bar">
          <el-input
            v-model="searchQuery"
            placeholder="搜索数据库名称..."
            style="width: 300px;"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <div class="toolbar">
          <el-button @click="refreshList">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
          <el-button @click="showBackupDialog">
            <el-icon><Download /></el-icon>
            批量备份
          </el-button>
        </div>
      </div>

      <!-- 数据库表格 -->
      <el-table :data="databases" v-loading="loading" style="width: 100%">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="数据库名称" min-width="150">
          <template #default="{ row }">
            <div class="database-name">
              <el-icon><Coin /></el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="charset" label="字符集" width="100" />
        <el-table-column prop="collation" label="排序规则" width="150" />
        <el-table-column prop="size" label="大小" width="100">
          <template #default="{ row }">
            {{ formatSize(row.size) }}
          </template>
        </el-table-column>
        <el-table-column prop="tables" label="表数量" width="80" />
        <el-table-column prop="created_at" label="创建时间" width="150">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="last_backup" label="最后备份" width="150">
          <template #default="{ row }">
            <span v-if="row.last_backup">{{ formatDate(row.last_backup) }}</span>
            <el-tag v-else type="warning" size="small">未备份</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="manageDatabase(row)">管理</el-button>
            <el-button size="small" @click="backupDatabase(row)">备份</el-button>
            <el-dropdown @command="handleCommand" trigger="click">
              <el-button size="small">
                更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :command="{action: 'export', database: row}">导出SQL</el-dropdown-item>
                  <el-dropdown-item :command="{action: 'import', database: row}">导入SQL</el-dropdown-item>
                  <el-dropdown-item :command="{action: 'optimize', database: row}">优化表</el-dropdown-item>
                  <el-dropdown-item :command="{action: 'repair', database: row}">修复表</el-dropdown-item>
                  <el-dropdown-item :command="{action: 'users', database: row}" divided>用户权限</el-dropdown-item>
                  <el-dropdown-item :command="{action: 'delete', database: row}">删除数据库</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 创建数据库对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="创建数据库"
      width="500px"
      :close-on-click-modal="false"
    >
      <create-database-form 
        @success="handleCreateSuccess"
        @cancel="createDialogVisible = false"
      />
    </el-dialog>

    <!-- 备份对话框 -->
    <el-dialog
      v-model="backupDialogVisible"
      title="数据库备份"
      width="600px"
    >
      <backup-database-form 
        :databases="selectedDatabases"
        @success="handleBackupSuccess"
        @cancel="backupDialogVisible = false"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getDatabaseStats,
  getDatabases,
  deleteDatabase,
  backupDatabase,
  batchBackupDatabases,
  optimizeDatabase,
  repairDatabase,
  exportDatabase,
  importDatabase
} from '@/api/databases'
import CreateDatabaseForm from '@/components/CreateDatabaseForm.vue'
import BackupDatabaseForm from '@/components/BackupDatabaseForm.vue'

const router = useRouter()

const loading = ref(false)
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const createDialogVisible = ref(false)
const backupDialogVisible = ref(false)
const selectedDatabases = ref([])

const databaseStats = ref({
  total: 0,
  totalSize: 0,
  users: 0,
  backups: 0
})

const databases = ref([
  {
    id: 1,
    name: 'wordpress_db',
    charset: 'utf8mb4',
    collation: 'utf8mb4_unicode_ci',
    size: 25600000, // 25.6MB
    tables: 12,
    created_at: '2024-01-15',
    last_backup: '2024-01-20'
  },
  {
    id: 2,
    name: 'laravel_app',
    charset: 'utf8mb4',
    collation: 'utf8mb4_unicode_ci',
    size: 12800000, // 12.8MB
    tables: 8,
    created_at: '2024-01-10',
    last_backup: null
  },
  {
    id: 3,
    name: 'test_db',
    charset: 'utf8',
    collation: 'utf8_general_ci',
    size: 5120000, // 5.12MB
    tables: 3,
    created_at: '2024-01-05',
    last_backup: '2024-01-18'
  }
])

// 方法定义
const showCreateDialog = () => {
  createDialogVisible.value = true
}

const showBackupDialog = () => {
  backupDialogVisible.value = true
}

const openPhpMyAdmin = () => {
  window.open('/phpmyadmin', '_blank')
}

const handleSearch = () => {
  fetchDatabases()
}

const refreshList = () => {
  fetchDatabases()
}

const handleSizeChange = (size) => {
  pageSize.value = size
  fetchDatabases()
}

const handleCurrentChange = (page) => {
  currentPage.value = page
  fetchDatabases()
}

const manageDatabase = (database) => {
  router.push(`/databases/${database.id}`)
}

const backupDatabaseAction = async (database) => {
  try {
    ElMessage.info('开始备份数据库...')
    await backupDatabase(database.id, 'full', 'gzip')
    ElMessage.success('数据库备份任务已启动')
    fetchDatabases()
  } catch (error) {
    ElMessage.error('数据库备份失败')
  }
}

const handleCommand = async (command) => {
  const { action, database } = command
  
  switch (action) {
    case 'export':
      exportDatabaseAction(database)
      break
    case 'import':
      importDatabaseAction(database)
      break
    case 'optimize':
      optimizeDatabaseAction(database)
      break
    case 'repair':
      repairDatabaseAction(database)
      break
    case 'users':
      manageDatabaseUsers(database)
      break
    case 'delete':
      await deleteDatabaseAction(database)
      break
  }
}

const exportDatabaseAction = async (database) => {
  try {
    ElMessage.info('开始导出数据库...')
    await exportDatabase(database.id, 'sql')
    ElMessage.success('数据库导出任务已启动')
  } catch (error) {
    ElMessage.error('导出数据库失败')
  }
}

const importDatabaseAction = (database) => {
  ElMessage.info('请选择SQL文件导入')
  // 实现文件选择和导入逻辑
}

const optimizeDatabaseAction = async (database) => {
  try {
    ElMessage.info('正在优化数据库表...')
    const result = await optimizeDatabase(database.id)
    ElMessage.success('数据库优化完成')
    console.log('优化结果:', result)
  } catch (error) {
    ElMessage.error('数据库优化失败')
  }
}

const repairDatabaseAction = async (database) => {
  try {
    ElMessage.info('正在修复数据库表...')
    const result = await repairDatabase(database.id)
    ElMessage.success('数据库修复完成')
    console.log('修复结果:', result)
  } catch (error) {
    ElMessage.error('数据库修复失败')
  }
}

const manageDatabaseUsers = (database) => {
  router.push(`/databases/${database.id}/users`)
}

const deleteDatabaseAction = async (database) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除数据库 ${database.name} 吗？此操作不可恢复！`,
      '危险操作',
      {
        type: 'error',
        confirmButtonText: '确定删除',
        confirmButtonClass: 'el-button--danger'
      }
    )

    await deleteDatabase(database.id)
    ElMessage.success('数据库删除成功')
    fetchDatabases()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除数据库失败')
    }
  }
}

const handleCreateSuccess = () => {
  createDialogVisible.value = false
  ElMessage.success('数据库创建成功')
  fetchDatabases()
}

const handleBackupSuccess = () => {
  backupDialogVisible.value = false
  ElMessage.success('数据库备份成功')
  fetchDatabases()
}

const fetchDatabases = async () => {
  loading.value = true
  try {
    const [databasesResponse, statsResponse] = await Promise.all([
      getDatabases({
        search: searchQuery.value,
        page: currentPage.value,
        size: pageSize.value
      }),
      getDatabaseStats()
    ])

    databases.value = databasesResponse.data
    total.value = databasesResponse.total || databasesResponse.data.length
    databaseStats.value = statsResponse.data

  } catch (error) {
    ElMessage.error('获取数据库列表失败')
    console.error('获取数据库列表失败:', error)
  } finally {
    loading.value = false
  }
}

const formatSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

onMounted(() => {
  fetchDatabases()
})
</script>

<style lang="scss" scoped>
.databases-list {
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
    
    .header-right {
      display: flex;
      gap: 12px;
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
        &.size { background: linear-gradient(135deg, #67c23a, #85ce61); }
        &.users { background: linear-gradient(135deg, #e6a23c, #ebb563); }
        &.backups { background: linear-gradient(135deg, #f56c6c, #f78989); }
        
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
  
  .databases-container {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    
    .list-header {
      padding: 20px;
      border-bottom: 1px solid #f0f0f0;
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .toolbar {
        display: flex;
        gap: 12px;
      }
    }
    
    .database-name {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .el-icon {
        color: #409eff;
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
