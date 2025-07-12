<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <!-- 系统概览卡片 -->
      <el-col :span="6" v-for="card in overviewCards" :key="card.title">
        <el-card class="overview-card">
          <div class="card-content">
            <div class="card-icon" :style="{ backgroundColor: card.color }">
              <el-icon :size="24"><component :is="card.icon" /></el-icon>
            </div>
            <div class="card-info">
              <h3>{{ card.value }}</h3>
              <p>{{ card.title }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 系统监控图表 -->
      <el-col :span="12">
        <el-card title="系统监控">
          <template #header>
            <span>系统监控</span>
          </template>
          <div class="chart-container">
            <v-chart :option="systemChartOption" style="height: 300px;" />
          </div>
        </el-card>
      </el-col>
      
      <!-- 磁盘使用情况 -->
      <el-col :span="12">
        <el-card title="磁盘使用情况">
          <template #header>
            <span>磁盘使用情况</span>
          </template>
          <div class="disk-usage">
            <div v-for="disk in diskUsage" :key="disk.device" class="disk-item">
              <div class="disk-info">
                <span class="disk-name">{{ disk.device }}</span>
                <span class="disk-percent">{{ disk.percent.toFixed(1) }}%</span>
              </div>
              <el-progress
                :percentage="disk.percent"
                :color="getProgressColor(disk.percent)"
                :show-text="false"
              />
              <div class="disk-size">
                {{ formatBytes(disk.used) }} / {{ formatBytes(disk.total) }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 系统信息 -->
      <el-col :span="12">
        <el-card title="系统信息">
          <template #header>
            <span>系统信息</span>
          </template>
          <div class="system-info">
            <div v-for="info in systemInfo" :key="info.label" class="info-item">
              <span class="info-label">{{ info.label }}:</span>
              <span class="info-value">{{ info.value }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <!-- 快速操作 -->
      <el-col :span="12">
        <el-card title="快速操作">
          <template #header>
            <span>快速操作</span>
          </template>
          <div class="quick-actions">
            <el-button
              v-for="action in quickActions"
              :key="action.name"
              :type="action.type"
              :icon="action.icon"
              @click="handleQuickAction(action.action)"
              class="action-btn"
            >
              {{ action.name }}
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { getSystemInfo, getSystemStats, getDiskUsage } from '@/api/system'
import { ElMessage } from 'element-plus'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

const overviewCards = ref([
  { title: 'CPU使用率', value: '0%', icon: 'Cpu', color: '#409eff' },
  { title: '内存使用率', value: '0%', icon: 'MemoryCard', color: '#67c23a' },
  { title: '磁盘使用率', value: '0%', icon: 'HardDisk', color: '#e6a23c' },
  { title: '系统负载', value: '0.00', icon: 'TrendCharts', color: '#f56c6c' }
])

const systemChartOption = ref({
  tooltip: {
    trigger: 'axis'
  },
  legend: {
    data: ['CPU', '内存', '磁盘']
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: []
  },
  yAxis: {
    type: 'value',
    max: 100,
    axisLabel: {
      formatter: '{value}%'
    }
  },
  series: [
    {
      name: 'CPU',
      type: 'line',
      data: [],
      smooth: true,
      itemStyle: { color: '#409eff' }
    },
    {
      name: '内存',
      type: 'line',
      data: [],
      smooth: true,
      itemStyle: { color: '#67c23a' }
    },
    {
      name: '磁盘',
      type: 'line',
      data: [],
      smooth: true,
      itemStyle: { color: '#e6a23c' }
    }
  ]
})

const diskUsage = ref([])
const systemInfo = ref([])

const quickActions = [
  { name: '软件市场', type: 'primary', icon: 'ShoppingCart', action: 'packages' },
  { name: 'LAMP环境', type: 'success', icon: 'Platform', action: 'lamp' },
  { name: '系统服务', type: 'warning', icon: 'Setting', action: 'services' },
  { name: '文件管理', type: 'info', icon: 'Folder', action: 'files' }
]

let updateTimer = null

// 获取系统统计数据
const fetchSystemStats = async () => {
  try {
    const response = await getSystemStats()
    const stats = response.data
    
    // 更新概览卡片
    overviewCards.value[0].value = `${stats.cpu_usage.toFixed(1)}%`
    overviewCards.value[1].value = `${stats.memory_usage.toFixed(1)}%`
    overviewCards.value[2].value = `${stats.disk_usage.toFixed(1)}%`
    overviewCards.value[3].value = stats.load_1min.toFixed(2)
    
    // 更新图表数据
    const now = new Date().toLocaleTimeString()
    const option = systemChartOption.value
    
    if (option.xAxis.data.length >= 20) {
      option.xAxis.data.shift()
      option.series[0].data.shift()
      option.series[1].data.shift()
      option.series[2].data.shift()
    }
    
    option.xAxis.data.push(now)
    option.series[0].data.push(stats.cpu_usage)
    option.series[1].data.push(stats.memory_usage)
    option.series[2].data.push(stats.disk_usage)
    
  } catch (error) {
    console.error('获取系统统计数据失败:', error)
  }
}

// 获取系统信息
const fetchSystemInfo = async () => {
  try {
    const response = await getSystemInfo()
    const info = response.data
    
    systemInfo.value = [
      { label: '主机名', value: info.hostname },
      { label: '操作系统', value: `${info.os_name} ${info.os_version}` },
      { label: '内核版本', value: info.kernel_version },
      { label: '架构', value: info.architecture },
      { label: 'CPU型号', value: info.cpu_model },
      { label: 'CPU核心数', value: `${info.cpu_cores} 核` },
      { label: '总内存', value: `${(info.total_memory / 1024).toFixed(1)} GB` },
      { label: '总磁盘', value: `${info.total_disk} GB` }
    ]
  } catch (error) {
    console.error('获取系统信息失败:', error)
  }
}

// 获取磁盘使用情况
const fetchDiskUsage = async () => {
  try {
    const response = await getDiskUsage()
    diskUsage.value = response.data
  } catch (error) {
    console.error('获取磁盘使用情况失败:', error)
  }
}

// 格式化字节数
const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 获取进度条颜色
const getProgressColor = (percentage) => {
  if (percentage < 60) return '#67c23a'
  if (percentage < 80) return '#e6a23c'
  return '#f56c6c'
}

// 处理快速操作
const handleQuickAction = (action) => {
  const routes = {
    packages: '/packages/market',
    lamp: '/packages/lamp',
    services: '/system/services',
    files: '/files'
  }
  
  if (routes[action]) {
    router.push(routes[action])
  }
}

onMounted(() => {
  fetchSystemInfo()
  fetchSystemStats()
  fetchDiskUsage()
  
  // 每5秒更新一次数据
  updateTimer = setInterval(() => {
    fetchSystemStats()
  }, 5000)
})

onUnmounted(() => {
  if (updateTimer) {
    clearInterval(updateTimer)
  }
})
</script>

<style lang="scss" scoped>
.dashboard {
  .overview-card {
    .card-content {
      display: flex;
      align-items: center;
      
      .card-icon {
        width: 60px;
        height: 60px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        margin-right: 16px;
      }
      
      .card-info {
        h3 {
          font-size: 24px;
          font-weight: bold;
          margin: 0 0 4px 0;
          color: #303133;
        }
        
        p {
          font-size: 14px;
          color: #909399;
          margin: 0;
        }
      }
    }
  }
  
  .chart-container {
    height: 300px;
  }
  
  .disk-usage {
    .disk-item {
      margin-bottom: 20px;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .disk-info {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        
        .disk-name {
          font-weight: 500;
        }
        
        .disk-percent {
          color: #909399;
        }
      }
      
      .disk-size {
        font-size: 12px;
        color: #c0c4cc;
        margin-top: 4px;
      }
    }
  }
  
  .system-info {
    .info-item {
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      border-bottom: 1px solid #f0f0f0;
      
      &:last-child {
        border-bottom: none;
      }
      
      .info-label {
        color: #909399;
        font-size: 14px;
      }
      
      .info-value {
        color: #303133;
        font-size: 14px;
        font-weight: 500;
      }
    }
  }
  
  .quick-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    
    .action-btn {
      width: 100%;
      height: 48px;
    }
  }
}
</style>
