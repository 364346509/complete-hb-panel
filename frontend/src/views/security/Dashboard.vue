<template>
  <div class="security-dashboard">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <div class="header-left">
        <h2>安全中心</h2>
        <span class="subtitle">系统安全状态监控和管理</span>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="startSecurityScan">
          <el-icon><Shield /></el-icon>
          安全扫描
        </el-button>
        <el-button type="warning" @click="showFirewallSettings">
          <el-icon><Lock /></el-icon>
          防火墙设置
        </el-button>
      </div>
    </div>

    <!-- 安全状态卡片 -->
    <el-row :gutter="16" class="security-cards">
      <el-col :span="6">
        <div class="security-card">
          <div class="card-header">
            <div class="card-icon firewall">
              <el-icon><Lock /></el-icon>
            </div>
            <div class="card-title">防火墙状态</div>
          </div>
          <div class="card-content">
            <div class="status-indicator" :class="firewallStatus.enabled ? 'active' : 'inactive'">
              {{ firewallStatus.enabled ? '已启用' : '已禁用' }}
            </div>
            <div class="card-stats">
              <span>规则数: {{ firewallStatus.rules }}</span>
              <span>阻止: {{ firewallStatus.blocked }}</span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="security-card">
          <div class="card-header">
            <div class="card-icon ssl">
              <el-icon><Key /></el-icon>
            </div>
            <div class="card-title">SSL证书</div>
          </div>
          <div class="card-content">
            <div class="status-indicator active">
              {{ sslStatus.total }} 个证书
            </div>
            <div class="card-stats">
              <span>有效: {{ sslStatus.valid }}</span>
              <span>即将过期: {{ sslStatus.expiring }}</span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="security-card">
          <div class="card-header">
            <div class="card-icon scan">
              <el-icon><Search /></el-icon>
            </div>
            <div class="card-title">安全扫描</div>
          </div>
          <div class="card-content">
            <div class="status-indicator" :class="scanStatus.status === 'clean' ? 'active' : 'warning'">
              {{ scanStatus.status === 'clean' ? '安全' : '发现威胁' }}
            </div>
            <div class="card-stats">
              <span>最后扫描: {{ scanStatus.lastScan }}</span>
              <span>威胁: {{ scanStatus.threats }}</span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="security-card">
          <div class="card-header">
            <div class="card-icon events">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="card-title">安全事件</div>
          </div>
          <div class="card-content">
            <div class="status-indicator" :class="securityEvents.critical > 0 ? 'danger' : 'active'">
              {{ securityEvents.total }} 个事件
            </div>
            <div class="card-stats">
              <span>严重: {{ securityEvents.critical }}</span>
              <span>警告: {{ securityEvents.warning }}</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 主要功能区域 -->
    <el-row :gutter="16">
      <!-- 防火墙管理 -->
      <el-col :span="12">
        <div class="function-card">
          <div class="card-header">
            <h3>防火墙管理</h3>
            <el-button size="small" @click="showFirewallRules">查看全部</el-button>
          </div>
          <div class="card-content">
            <div class="firewall-status">
              <div class="status-item">
                <span class="label">状态:</span>
                <el-tag :type="firewallStatus.enabled ? 'success' : 'danger'" size="small">
                  {{ firewallStatus.enabled ? '已启用' : '已禁用' }}
                </el-tag>
                <el-button 
                  size="small" 
                  :type="firewallStatus.enabled ? 'danger' : 'success'"
                  @click="toggleFirewall"
                  style="margin-left: 12px;"
                >
                  {{ firewallStatus.enabled ? '禁用' : '启用' }}
                </el-button>
              </div>
            </div>
            <div class="recent-rules">
              <h4>最近规则</h4>
              <div class="rule-list">
                <div v-for="rule in recentFirewallRules" :key="rule.id" class="rule-item">
                  <div class="rule-info">
                    <span class="rule-name">{{ rule.name }}</span>
                    <span class="rule-detail">{{ rule.port }} / {{ rule.protocol }}</span>
                  </div>
                  <el-tag :type="rule.action === 'allow' ? 'success' : 'danger'" size="small">
                    {{ rule.action === 'allow' ? '允许' : '拒绝' }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-col>

      <!-- SSH安全 -->
      <el-col :span="12">
        <div class="function-card">
          <div class="card-header">
            <h3>SSH安全</h3>
            <el-button size="small" @click="showSSHSettings">配置</el-button>
          </div>
          <div class="card-content">
            <div class="ssh-info">
              <div class="info-item">
                <span class="label">SSH端口:</span>
                <span class="value">{{ sshConfig.port }}</span>
              </div>
              <div class="info-item">
                <span class="label">Root登录:</span>
                <el-tag :type="sshConfig.permitRootLogin ? 'danger' : 'success'" size="small">
                  {{ sshConfig.permitRootLogin ? '允许' : '禁止' }}
                </el-tag>
              </div>
              <div class="info-item">
                <span class="label">密码认证:</span>
                <el-tag :type="sshConfig.passwordAuth ? 'warning' : 'success'" size="small">
                  {{ sshConfig.passwordAuth ? '启用' : '禁用' }}
                </el-tag>
              </div>
              <div class="info-item">
                <span class="label">密钥认证:</span>
                <el-tag :type="sshConfig.keyAuth ? 'success' : 'warning'" size="small">
                  {{ sshConfig.keyAuth ? '启用' : '禁用' }}
                </el-tag>
              </div>
            </div>
            <div class="ssh-keys">
              <h4>SSH密钥 ({{ sshKeys.length }})</h4>
              <el-button size="small" type="primary" @click="showAddKeyDialog">添加密钥</el-button>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- IP黑白名单 -->
    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :span="12">
        <div class="function-card">
          <div class="card-header">
            <h3>IP黑名单</h3>
            <el-button size="small" @click="showBlacklistDialog">添加</el-button>
          </div>
          <div class="card-content">
            <div class="ip-list">
              <div v-for="ip in ipBlacklist.slice(0, 5)" :key="ip.id" class="ip-item">
                <div class="ip-info">
                  <span class="ip-address">{{ ip.address }}</span>
                  <span class="ip-reason">{{ ip.reason }}</span>
                </div>
                <div class="ip-actions">
                  <el-button size="small" type="danger" @click="removeFromBlacklist(ip)">移除</el-button>
                </div>
              </div>
              <div v-if="ipBlacklist.length === 0" class="empty-state">
                暂无黑名单IP
              </div>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :span="12">
        <div class="function-card">
          <div class="card-header">
            <h3>安全事件</h3>
            <el-button size="small" @click="showAllEvents">查看全部</el-button>
          </div>
          <div class="card-content">
            <div class="event-list">
              <div v-for="event in recentSecurityEvents" :key="event.id" class="event-item">
                <div class="event-info">
                  <div class="event-title">{{ event.title }}</div>
                  <div class="event-detail">
                    <span class="event-time">{{ formatDate(event.time) }}</span>
                    <span class="event-ip">{{ event.sourceIp }}</span>
                  </div>
                </div>
                <el-tag :type="getEventLevelType(event.level)" size="small">
                  {{ getEventLevelText(event.level) }}
                </el-tag>
              </div>
              <div v-if="recentSecurityEvents.length === 0" class="empty-state">
                暂无安全事件
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 对话框 -->
    <el-dialog v-model="firewallDialogVisible" title="防火墙设置" width="600px">
      <firewall-settings @close="firewallDialogVisible = false" />
    </el-dialog>

    <el-dialog v-model="sshDialogVisible" title="SSH设置" width="600px">
      <ssh-settings @close="sshDialogVisible = false" />
    </el-dialog>

    <el-dialog v-model="addKeyDialogVisible" title="添加SSH密钥" width="500px">
      <add-ssh-key @close="addKeyDialogVisible = false" />
    </el-dialog>

    <el-dialog v-model="blacklistDialogVisible" title="添加IP黑名单" width="400px">
      <add-ip-blacklist @close="blacklistDialogVisible = false" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSecurityDashboard, toggleFirewall } from '@/api/security'

const router = useRouter()

const firewallDialogVisible = ref(false)
const sshDialogVisible = ref(false)
const addKeyDialogVisible = ref(false)
const blacklistDialogVisible = ref(false)

// 安全状态数据
const firewallStatus = ref({
  enabled: true,
  rules: 12,
  blocked: 156
})

const sslStatus = ref({
  total: 5,
  valid: 4,
  expiring: 1
})

const scanStatus = ref({
  status: 'clean',
  lastScan: '2小时前',
  threats: 0
})

const securityEvents = ref({
  total: 8,
  critical: 0,
  warning: 3
})

const sshConfig = ref({
  port: 22,
  permitRootLogin: false,
  passwordAuth: true,
  keyAuth: true
})

const sshKeys = ref([
  { id: 1, name: 'admin-key', fingerprint: 'SHA256:abc123...' },
  { id: 2, name: 'backup-key', fingerprint: 'SHA256:def456...' }
])

const recentFirewallRules = ref([
  { id: 1, name: 'SSH访问', port: '22', protocol: 'tcp', action: 'allow' },
  { id: 2, name: 'HTTP访问', port: '80', protocol: 'tcp', action: 'allow' },
  { id: 3, name: 'HTTPS访问', port: '443', protocol: 'tcp', action: 'allow' },
  { id: 4, name: '恶意IP', port: '*', protocol: '*', action: 'deny' }
])

const ipBlacklist = ref([
  { id: 1, address: '192.168.1.100', reason: '暴力破解' },
  { id: 2, address: '10.0.0.50', reason: '恶意扫描' },
  { id: 3, address: '172.16.0.25', reason: '异常访问' }
])

const recentSecurityEvents = ref([
  {
    id: 1,
    title: '检测到SSH暴力破解尝试',
    level: 'high',
    sourceIp: '192.168.1.100',
    time: '2024-01-20 14:30:00'
  },
  {
    id: 2,
    title: '异常登录尝试',
    level: 'medium',
    sourceIp: '10.0.0.50',
    time: '2024-01-20 13:15:00'
  },
  {
    id: 3,
    title: '端口扫描检测',
    level: 'low',
    sourceIp: '172.16.0.25',
    time: '2024-01-20 12:45:00'
  }
])

// 方法定义
const startSecurityScan = () => {
  ElMessage.info('启动安全扫描...')
}

const showFirewallSettings = () => {
  firewallDialogVisible.value = true
}

const showFirewallRules = () => {
  router.push('/security/firewall')
}

const showSSHSettings = () => {
  sshDialogVisible.value = true
}

const showAddKeyDialog = () => {
  addKeyDialogVisible.value = true
}

const showBlacklistDialog = () => {
  blacklistDialogVisible.value = true
}

const showAllEvents = () => {
  router.push('/security/events')
}

const toggleFirewallStatus = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要${firewallStatus.value.enabled ? '禁用' : '启用'}防火墙吗？`,
      '确认操作',
      { type: 'warning' }
    )
    
    await toggleFirewall()
    firewallStatus.value.enabled = !firewallStatus.value.enabled
    ElMessage.success(`防火墙已${firewallStatus.value.enabled ? '启用' : '禁用'}`)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const removeFromBlacklist = async (ip) => {
  try {
    await ElMessageBox.confirm(`确定要移除IP ${ip.address} 吗？`, '确认操作', {
      type: 'warning'
    })
    
    // 调用API移除IP
    ElMessage.success('IP已从黑名单移除')
    // 刷新列表
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('移除失败')
    }
  }
}

const getEventLevelType = (level) => {
  const levelMap = {
    low: 'info',
    medium: 'warning',
    high: 'danger',
    critical: 'danger'
  }
  return levelMap[level] || 'info'
}

const getEventLevelText = (level) => {
  const levelMap = {
    low: '低',
    medium: '中',
    high: '高',
    critical: '严重'
  }
  return levelMap[level] || level
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const fetchSecurityDashboard = async () => {
  try {
    // const response = await getSecurityDashboard()
    // 更新数据
  } catch (error) {
    ElMessage.error('获取安全状态失败')
  }
}

onMounted(() => {
  fetchSecurityDashboard()
})
</script>

<style lang="scss" scoped>
.security-dashboard {
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
  
  .security-cards {
    margin-bottom: 24px;
    
    .security-card {
      background: white;
      border-radius: 8px;
      padding: 20px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      
      .card-header {
        display: flex;
        align-items: center;
        margin-bottom: 16px;
        
        .card-icon {
          width: 40px;
          height: 40px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 12px;
          
          &.firewall { background: linear-gradient(135deg, #f56c6c, #f78989); }
          &.ssl { background: linear-gradient(135deg, #67c23a, #85ce61); }
          &.scan { background: linear-gradient(135deg, #409eff, #66b1ff); }
          &.events { background: linear-gradient(135deg, #e6a23c, #ebb563); }
          
          .el-icon {
            color: white;
            font-size: 18px;
          }
        }
        
        .card-title {
          font-size: 16px;
          font-weight: 600;
          color: #303133;
        }
      }
      
      .card-content {
        .status-indicator {
          font-size: 18px;
          font-weight: 600;
          margin-bottom: 8px;
          
          &.active { color: #67c23a; }
          &.inactive { color: #909399; }
          &.warning { color: #e6a23c; }
          &.danger { color: #f56c6c; }
        }
        
        .card-stats {
          display: flex;
          gap: 16px;
          font-size: 14px;
          color: #909399;
        }
      }
    }
  }
  
  .function-card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    margin-bottom: 16px;
    
    .card-header {
      padding: 20px 20px 0 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      h3 {
        margin: 0;
        font-size: 18px;
        color: #303133;
      }
    }
    
    .card-content {
      padding: 20px;
      
      .firewall-status {
        margin-bottom: 20px;
        
        .status-item {
          display: flex;
          align-items: center;
          
          .label {
            font-weight: 600;
            margin-right: 8px;
          }
        }
      }
      
      .recent-rules {
        h4 {
          margin: 0 0 12px 0;
          font-size: 14px;
          color: #606266;
        }
        
        .rule-list {
          .rule-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #f0f0f0;
            
            &:last-child {
              border-bottom: none;
            }
            
            .rule-info {
              .rule-name {
                display: block;
                font-weight: 600;
                color: #303133;
              }
              
              .rule-detail {
                font-size: 12px;
                color: #909399;
              }
            }
          }
        }
      }
      
      .ssh-info {
        margin-bottom: 20px;
        
        .info-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 0;
          
          .label {
            font-weight: 600;
            color: #606266;
          }
          
          .value {
            color: #303133;
          }
        }
      }
      
      .ssh-keys {
        h4 {
          margin: 0 0 12px 0;
          font-size: 14px;
          color: #606266;
        }
      }
      
      .ip-list, .event-list {
        .ip-item, .event-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 0;
          border-bottom: 1px solid #f0f0f0;
          
          &:last-child {
            border-bottom: none;
          }
        }
        
        .ip-info {
          .ip-address {
            display: block;
            font-weight: 600;
            color: #303133;
          }
          
          .ip-reason {
            font-size: 12px;
            color: #909399;
          }
        }
        
        .event-info {
          flex: 1;
          
          .event-title {
            font-weight: 600;
            color: #303133;
            margin-bottom: 4px;
          }
          
          .event-detail {
            font-size: 12px;
            color: #909399;
            
            .event-time {
              margin-right: 12px;
            }
          }
        }
        
        .empty-state {
          text-align: center;
          color: #909399;
          padding: 20px 0;
        }
      }
    }
  }
}
</style>
