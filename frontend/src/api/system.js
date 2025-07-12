import request from '@/utils/request'

// 获取系统信息
export const getSystemInfo = () => {
  return request({
    url: '/system/info',
    method: 'get'
  })
}

// 获取系统统计信息
export const getSystemStats = () => {
  return request({
    url: '/system/stats',
    method: 'get'
  })
}

// 获取系统历史统计数据
export const getSystemStatsHistory = (hours = 24) => {
  return request({
    url: '/system/stats/history',
    method: 'get',
    params: { hours }
  })
}

// 获取进程列表
export const getProcesses = (params = {}) => {
  return request({
    url: '/system/processes',
    method: 'get',
    params
  })
}

// 终止进程
export const killProcess = (pid) => {
  return request({
    url: `/system/processes/${pid}`,
    method: 'delete'
  })
}

// 获取磁盘使用情况
export const getDiskUsage = () => {
  return request({
    url: '/system/disk/usage',
    method: 'get'
  })
}

// 获取网络接口信息
export const getNetworkInterfaces = () => {
  return request({
    url: '/system/network/interfaces',
    method: 'get'
  })
}

// 获取系统日志
export const getSystemLogs = (params = {}) => {
  return request({
    url: '/system/logs/system',
    method: 'get',
    params
  })
}
