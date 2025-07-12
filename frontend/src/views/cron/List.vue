<template>
  <div class="cron-list">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <div class="header-left">
        <h2>计划任务</h2>
        <span class="subtitle">管理系统定时任务和备份计划</span>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          创建任务
        </el-button>
        <el-button type="success" @click="showTemplateDialog">
          <el-icon><Document /></el-icon>
          任务模板
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-cards">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon total">
            <el-icon><Clock /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ cronStats.total }}</div>
            <div class="stat-label">总任务数</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon active">
            <el-icon><VideoPlay /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ cronStats.active }}</div>
            <div class="stat-label">运行中</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon success">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ cronStats.success }}</div>
            <div class="stat-label">成功执行</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon failed">
            <el-icon><CircleClose /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ cronStats.failed }}</div>
            <div class="stat-label">执行失败</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 任务列表 -->
    <div class="cron-container">
      <div class="list-header">
        <div class="search-bar">
          <el-input
            v-model="searchQuery"
            placeholder="搜索任务名称..."
            style="width: 300px;"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-select v-model="typeFilter" placeholder="任务类型" style="width: 150px; margin-left: 12px;">
            <el-option label="全部类型" value="" />
            <el-option label="Shell脚本" value="shell" />
            <el-option label="网站备份" value="website_backup" />
            <el-option label="数据库备份" value="database_backup" />
            <el-option label="日志清理" value="log_clean" />
            <el-option label="系统清理" value="system_clean" />
          </el-select>
          <el-select v-model="statusFilter" placeholder="任务状态" style="width: 150px; margin-left: 12px;">
            <el-option label="全部状态" value="" />
            <el-option label="运行中" value="active" />
            <el-option label="已停止" value="inactive" />
            <el-option label="错误" value="error" />
          </el-select>
        </div>
        <div class="toolbar">
          <el-button @click="refreshList">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
          <el-button @click="showSystemStatus">
            <el-icon><Monitor /></el-icon>
            系统状态
          </el-button>
        </div>
      </div>

      <!-- 任务表格 -->
      <el-table :data="cronTasks" v-loading="loading" style="width: 100%">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="任务名称" min-width="200">
          <template #default="{ row }">
            <div class="task-name">
              <el-icon><Clock /></el-icon>
              <span>{{ row.name }}</span>
              <el-tag v-if="row.type !== 'shell'" size="small" style="margin-left: 8px;">
                {{ getTypeLabel(row.type) }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="cron_expression" label="执行时间" width="120">
          <template #default="{ row }">
            <el-tooltip :content="parseCronExpression(row.cron_expression)" placement="top">
              <span class="cron-expression">{{ row.cron_expression }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_run" label="最后执行" width="150">
          <template #default="{ row }">
            <span v-if="row.last_run">{{ formatDate(row.last_run) }}</span>
            <span v-else class="text-muted">未执行</span>
          </template>
        </el-table-column>
        <el-table-column prop="next_run" label="下次执行" width="150">
          <template #default="{ row }">
            <span v-if="row.next_run">{{ formatDate(row.next_run) }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="执行统计" width="120">
          <template #default="{ row }">
            <div class="execution-stats">
              <span class="success">成功: {{ row.success_runs }}</span>
              <span class="failed">失败: {{ row.failed_runs }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="runTask(row)">执行</el-button>
            <el-button size="small" @click="viewLogs(row)">日志</el-button>
            <el-dropdown @command="handleCommand" trigger="click">
              <el-button size="small">
                更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :command="{action: 'edit', task: row}">编辑</el-dropdown-item>
                  <el-dropdown-item :command="{action: 'toggle', task: row}">
                    {{ row.status === 'active' ? '停止' : '启动' }}
                  </el-dropdown-item>
                  <el-dropdown-item :command="{action: 'copy', task: row}">复制</el-dropdown-item>
                  <el-dropdown-item :command="{action: 'delete', task: row}" divided>删除</el-dropdown-item>
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

    <!-- 创建任务对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="创建计划任务"
      width="800px"
      :close-on-click-modal="false"
    >
      <create-cron-task-form 
        @success="handleCreateSuccess"
        @cancel="createDialogVisible = false"
      />
    </el-dialog>

    <!-- 任务模板对话框 -->
    <el-dialog
      v-model="templateDialogVisible"
      title="任务模板"
      width="600px"
    >
      <cron-task-templates 
        @select="handleTemplateSelect"
        @cancel="templateDialogVisible = false"
      />
    </el-dialog>

    <!-- 任务日志对话框 -->
    <el-dialog
      v-model="logsDialogVisible"
      title="任务执行日志"
      width="800px"
    >
      <cron-task-logs 
        :task-id="selectedTaskId"
        @close="logsDialogVisible = false"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCronTasks, deleteCronTask, runCronTask, toggleCronTask } from '@/api/cron'
import CreateCronTaskForm from '@/components/CreateCronTaskForm.vue'
import CronTaskTemplates from '@/components/CronTaskTemplates.vue'
import CronTaskLogs from '@/components/CronTaskLogs.vue'

const router = useRouter()

const loading = ref(false)
const searchQuery = ref('')
const typeFilter = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const createDialogVisible = ref(false)
const templateDialogVisible = ref(false)
const logsDialogVisible = ref(false)
const selectedTaskId = ref(null)

const cronStats = ref({
  total: 0,
  active: 0,
  success: 0,
  failed: 0
})

const cronTasks = ref([
  // 模拟数据
  {
    id: 1,
    name: '网站备份任务',
    type: 'website_backup',
    cron_expression: '0 2 * * *',
    status: 'active',
    total_runs: 30,
    success_runs: 28,
    failed_runs: 2,
    last_run: '2024-01-20 02:00:00',
    next_run: '2024-01-21 02:00:00',
    created_at: '2024-01-01'
  },
  {
    id: 2,
    name: '数据库备份',
    type: 'database_backup',
    cron_expression: '0 3 * * 0',
    status: 'active',
    total_runs: 4,
    success_runs: 4,
    failed_runs: 0,
    last_run: '2024-01-14 03:00:00',
    next_run: '2024-01-21 03:00:00',
    created_at: '2024-01-01'
  },
  {
    id: 3,
    name: '日志清理',
    type: 'log_clean',
    cron_expression: '0 1 * * *',
    status: 'inactive',
    total_runs: 15,
    success_runs: 15,
    failed_runs: 0,
    last_run: '2024-01-15 01:00:00',
    next_run: null,
    created_at: '2024-01-01'
  }
])

// 方法定义
const showCreateDialog = () => {
  createDialogVisible.value = true
}

const showTemplateDialog = () => {
  templateDialogVisible.value = true
}

const showSystemStatus = () => {
  ElMessage.info('显示系统状态')
}

const handleSearch = () => {
  fetchCronTasks()
}

const refreshList = () => {
  fetchCronTasks()
}

const handleSizeChange = (size) => {
  pageSize.value = size
  fetchCronTasks()
}

const handleCurrentChange = (page) => {
  currentPage.value = page
  fetchCronTasks()
}

const runTask = async (task) => {
  try {
    await runCronTask(task.id)
    ElMessage.success('任务执行已启动')
  } catch (error) {
    ElMessage.error('启动任务失败')
  }
}

const viewLogs = (task) => {
  selectedTaskId.value = task.id
  logsDialogVisible.value = true
}

const handleCommand = async (command) => {
  const { action, task } = command
  
  switch (action) {
    case 'edit':
      router.push(`/cron/edit/${task.id}`)
      break
    case 'toggle':
      await toggleTaskStatus(task)
      break
    case 'copy':
      await copyTask(task)
      break
    case 'delete':
      await deleteTask(task)
      break
  }
}

const toggleTaskStatus = async (task) => {
  try {
    await toggleCronTask(task.id)
    ElMessage.success(`任务已${task.status === 'active' ? '停止' : '启动'}`)
    fetchCronTasks()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const copyTask = async (task) => {
  ElMessage.info('复制任务功能开发中...')
}

const deleteTask = async (task) => {
  try {
    await ElMessageBox.confirm(`确定要删除任务 ${task.name} 吗？`, '确认删除', {
      type: 'warning'
    })
    
    await deleteCronTask(task.id)
    ElMessage.success('任务删除成功')
    fetchCronTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除任务失败')
    }
  }
}

const handleCreateSuccess = () => {
  createDialogVisible.value = false
  ElMessage.success('任务创建成功')
  fetchCronTasks()
}

const handleTemplateSelect = (template) => {
  templateDialogVisible.value = false
  // 使用模板创建任务
  ElMessage.info('使用模板创建任务')
}

const fetchCronTasks = async () => {
  loading.value = true
  try {
    // 模拟API调用
    setTimeout(() => {
      cronStats.value = {
        total: cronTasks.value.length,
        active: cronTasks.value.filter(t => t.status === 'active').length,
        success: cronTasks.value.reduce((sum, t) => sum + t.success_runs, 0),
        failed: cronTasks.value.reduce((sum, t) => sum + t.failed_runs, 0)
      }
      total.value = cronTasks.value.length
      loading.value = false
    }, 500)
  } catch (error) {
    ElMessage.error('获取任务列表失败')
    loading.value = false
  }
}

const getTypeLabel = (type) => {
  const typeMap = {
    shell: 'Shell',
    website_backup: '网站备份',
    database_backup: '数据库备份',
    log_clean: '日志清理',
    system_clean: '系统清理'
  }
  return typeMap[type] || type
}

const getStatusType = (status) => {
  const statusMap = {
    active: 'success',
    inactive: 'info',
    error: 'danger'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status) => {
  const statusMap = {
    active: '运行中',
    inactive: '已停止',
    error: '错误'
  }
  return statusMap[status] || status
}

const parseCronExpression = (expression) => {
  // 简单的cron表达式解析
  const parts = expression.split(' ')
  if (parts.length === 5) {
    const [minute, hour, day, month, weekday] = parts
    if (minute === '0' && hour !== '*') {
      return `每天 ${hour}:00 执行`
    }
    if (weekday !== '*') {
      return `每周${weekday} ${hour}:${minute} 执行`
    }
  }
  return expression
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchCronTasks()
})
</script>

<style lang="scss" scoped>
.cron-list {
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
        &.active { background: linear-gradient(135deg, #67c23a, #85ce61); }
        &.success { background: linear-gradient(135deg, #e6a23c, #ebb563); }
        &.failed { background: linear-gradient(135deg, #f56c6c, #f78989); }
        
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
  
  .cron-container {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    
    .list-header {
      padding: 20px;
      border-bottom: 1px solid #f0f0f0;
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .search-bar {
        display: flex;
        align-items: center;
      }
      
      .toolbar {
        display: flex;
        gap: 12px;
      }
    }
    
    .task-name {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .el-icon {
        color: #409eff;
      }
    }
    
    .cron-expression {
      font-family: 'Courier New', monospace;
      font-size: 12px;
      background: #f5f7fa;
      padding: 2px 6px;
      border-radius: 4px;
    }
    
    .execution-stats {
      display: flex;
      flex-direction: column;
      gap: 2px;
      
      .success {
        color: #67c23a;
        font-size: 12px;
      }
      
      .failed {
        color: #f56c6c;
        font-size: 12px;
      }
    }
    
    .text-muted {
      color: #909399;
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
