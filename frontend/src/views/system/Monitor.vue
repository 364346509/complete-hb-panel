<template>
  <div class="system-monitor">
    <el-row :gutter="20">
      <!-- 实时监控卡片 -->
      <el-col :span="6" v-for="card in monitorCards" :key="card.title">
        <el-card class="monitor-card">
          <div class="card-content">
            <div class="card-icon" :style="{ backgroundColor: card.color }">
              <el-icon :size="24"><component :is="card.icon" /></el-icon>
            </div>
            <div class="card-info">
              <h3>{{ card.value }}</h3>
              <p>{{ card.title }}</p>
              <div class="card-trend" :class="card.trend">
                <el-icon><component :is="card.trendIcon" /></el-icon>
                <span>{{ card.change }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 系统监控图表 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>系统性能监控</span>
              <el-button-group>
                <el-button 
                  v-for="period in timePeriods" 
                  :key="period.value"
                  :type="selectedPeriod === period.value ? 'primary' : ''"
                  size="small"
                  @click="changePeriod(period.value)"
                >
                  {{ period.label }}
                </el-button>
              </el-button-group>
            </div>
          </template>
          <div class="chart-container">
            <v-chart :option="chartOption" style="height: 400px;" />
          </div>
        </el-card>
      </el-col>

      <!-- 系统信息 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>系统信息</span>
          </template>
          <div class="system-info">
            <div v-for="info in systemInfo" :key="info.label" class="info-item">
              <span class="info-label">{{ info.label }}</span>
              <span class="info-value">{{ info.value }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 磁盘使用情况 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>磁盘使用情况</span>
          </template>
          <div class="disk-usage">
            <div v-for="disk in diskUsage" :key="disk.device" class="disk-item">
              <div class="disk-header">
                <span class="disk-name">{{ disk.device }}</span>
                <span class="disk-percent">{{ disk.percent.toFixed(1) }}%</span>
              </div>
              <el-progress
                :percentage="disk.percent"
                :color="getProgressColor(disk.percent)"
                :show-text="false"
              />
              <div class="disk-details">
                <span>{{ formatBytes(disk.used) }} / {{ formatBytes(disk.total) }}</span>
                <span>可用: {{ formatBytes(disk.free) }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 网络接口 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>网络接口</span>
          </template>
          <div class="network-interfaces">
            <div v-for="interface in networkInterfaces" :key="interface.name" class="interface-item">
              <div class="interface-header">
                <span class="interface-name">{{ interface.name }}</span>
                <el-tag :type="interface.is_up ? 'success' : 'danger'" size="small">
                  {{ interface.is_up ? '活动' : '非活动' }}
                </el-tag>
              </div>
              <div class="interface-details">
                <div v-for="addr in interface.addresses" :key="addr.address" class="address-item">
                  <span class="address-type">{{ getAddressType(addr.family) }}</span>
                  <span class="address-value">{{ addr.address }}</span>
                </div>
              </div>
            </div>
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
import { getSystemInfo, getSystemStats, getDiskUsage, getNetworkInterfaces } from '@/api/system'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

const monitorCards = ref([
  { 
    title: 'CPU使用率', 
    value: '0%', 
    icon: 'Cpu', 
    color: '#409eff',
    trend: 'up',
    trendIcon: 'ArrowUp',
    change: '0%'
  },
  { 
    title: '内存使用率', 
    value: '0%', 
    icon: 'MemoryCard', 
    color: '#67c23a',
    trend: 'down',
    trendIcon: 'ArrowDown',
    change: '0%'
  },
  { 
    title: '磁盘使用率', 
    value: '0%', 
    icon: 'HardDisk', 
    color: '#e6a23c',
    trend: 'stable',
    trendIcon: 'Minus',
    change: '0%'
  },
  { 
    title: '网络流量', 
    value: '0 KB/s', 
    icon: 'Connection', 
    color: '#f56c6c',
    trend: 'up',
    trendIcon: 'ArrowUp',
    change: '0%'
  }
])

const timePeriods = [
  { label: '1小时', value: 1 },
  { label: '6小时', value: 6 },
  { label: '24小时', value: 24 },
  { label: '7天', value: 168 }
]

const selectedPeriod = ref(1)
const systemInfo = ref([])
const diskUsage = ref([])
const networkInterfaces = ref([])

const chartOption = ref({
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'cross'
    }
  },
  legend: {
    data: ['CPU使用率', '内存使用率', '磁盘使用率']
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
      name: 'CPU使用率',
      type: 'line',
      data: [],
      smooth: true,
      itemStyle: { color: '#409eff' },
      areaStyle: { opacity: 0.3 }
    },
    {
      name: '内存使用率',
      type: 'line',
      data: [],
      smooth: true,
      itemStyle: { color: '#67c23a' },
      areaStyle: { opacity: 0.3 }
    },
    {
      name: '磁盘使用率',
      type: 'line',
      data: [],
      smooth: true,
      itemStyle: { color: '#e6a23c' },
      areaStyle: { opacity: 0.3 }
    }
  ]
})

let updateTimer = null

// 获取系统统计数据
const fetchSystemStats = async () => {
  try {
    const response = await getSystemStats()
    const stats = response.data
    
    // 更新监控卡片
    monitorCards.value[0].value = `${stats.cpu_usage.toFixed(1)}%`
    monitorCards.value[1].value = `${stats.memory_usage.toFixed(1)}%`
    monitorCards.value[2].value = `${stats.disk_usage.toFixed(1)}%`
    
    const networkSpeed = (stats.network_in + stats.network_out) / 1024
    monitorCards.value[3].value = `${networkSpeed.toFixed(1)} KB/s`
    
    // 更新图表数据
    const now = new Date().toLocaleTimeString()
    const option = chartOption.value
    
    if (option.xAxis.data.length >= 60) {
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
      { label: 'CPU核心', value: `${info.cpu_cores} 核` },
      { label: '总内存', value: `${(info.total_memory / 1024).toFixed(1)} GB` },
      { label: '系统负载', value: info.load_average }
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

// 获取网络接口信息
const fetchNetworkInterfaces = async () => {
  try {
    const response = await getNetworkInterfaces()
    networkInterfaces.value = response.data
  } catch (error) {
    console.error('获取网络接口信息失败:', error)
  }
}

// 切换时间周期
const changePeriod = (period) => {
  selectedPeriod.value = period
  // TODO: 根据时间周期获取历史数据
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

// 获取地址类型
const getAddressType = (family) => {
  const types = {
    'AddressFamily.AF_INET': 'IPv4',
    'AddressFamily.AF_INET6': 'IPv6',
    'AddressFamily.AF_PACKET': 'MAC'
  }
  return types[family] || family
}

onMounted(() => {
  fetchSystemInfo()
  fetchSystemStats()
  fetchDiskUsage()
  fetchNetworkInterfaces()
  
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
.system-monitor {
  .monitor-card {
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
        flex: 1;
        
        h3 {
          font-size: 24px;
          font-weight: bold;
          margin: 0 0 4px 0;
          color: #303133;
        }
        
        p {
          font-size: 14px;
          color: #909399;
          margin: 0 0 8px 0;
        }
        
        .card-trend {
          display: flex;
          align-items: center;
          font-size: 12px;
          
          &.up {
            color: #f56c6c;
          }
          
          &.down {
            color: #67c23a;
          }
          
          &.stable {
            color: #909399;
          }
          
          span {
            margin-left: 4px;
          }
        }
      }
    }
  }
  
  .chart-container {
    height: 400px;
  }
  
  .system-info {
    .info-item {
      display: flex;
      justify-content: space-between;
      padding: 12px 0;
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
  
  .disk-usage {
    .disk-item {
      margin-bottom: 24px;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .disk-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        
        .disk-name {
          font-weight: 500;
          color: #303133;
        }
        
        .disk-percent {
          color: #909399;
          font-size: 14px;
        }
      }
      
      .disk-details {
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        color: #c0c4cc;
        margin-top: 8px;
      }
    }
  }
  
  .network-interfaces {
    .interface-item {
      margin-bottom: 20px;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .interface-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        
        .interface-name {
          font-weight: 500;
          color: #303133;
        }
      }
      
      .interface-details {
        .address-item {
          display: flex;
          justify-content: space-between;
          padding: 4px 0;
          font-size: 12px;
          
          .address-type {
            color: #909399;
            width: 60px;
          }
          
          .address-value {
            color: #606266;
            font-family: monospace;
          }
        }
      }
    }
  }
}
</style>
