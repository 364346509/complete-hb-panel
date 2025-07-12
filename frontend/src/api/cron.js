import request from '@/utils/request'

// 获取计划任务列表
export function getCronTasks(params) {
  return request({
    url: '/cron/tasks',
    method: 'get',
    params
  })
}

// 创建计划任务
export function createCronTask(data) {
  return request({
    url: '/cron/tasks',
    method: 'post',
    data
  })
}

// 获取计划任务详情
export function getCronTask(id) {
  return request({
    url: `/cron/tasks/${id}`,
    method: 'get'
  })
}

// 更新计划任务
export function updateCronTask(id, data) {
  return request({
    url: `/cron/tasks/${id}`,
    method: 'put',
    data
  })
}

// 删除计划任务
export function deleteCronTask(id) {
  return request({
    url: `/cron/tasks/${id}`,
    method: 'delete'
  })
}

// 执行计划任务
export function runCronTask(id) {
  return request({
    url: `/cron/tasks/${id}/run`,
    method: 'post'
  })
}

// 启用/禁用计划任务
export function toggleCronTask(id) {
  return request({
    url: `/cron/tasks/${id}/toggle`,
    method: 'post'
  })
}

// 获取任务执行日志
export function getCronTaskLogs(id, params) {
  return request({
    url: `/cron/tasks/${id}/logs`,
    method: 'get',
    params
  })
}

// 获取任务模板
export function getCronTemplates() {
  return request({
    url: '/cron/templates',
    method: 'get'
  })
}

// 获取备份任务列表
export function getBackupTasks() {
  return request({
    url: '/cron/backups',
    method: 'get'
  })
}

// 创建备份任务
export function createBackupTask(data) {
  return request({
    url: '/cron/backups',
    method: 'post',
    data
  })
}

// 执行备份任务
export function runBackupTask(id) {
  return request({
    url: `/cron/backups/${id}/run`,
    method: 'post'
  })
}

// 获取系统状态
export function getCronSystemStatus() {
  return request({
    url: '/cron/system/status',
    method: 'get'
  })
}
