import request from '@/utils/request'

// 获取数据库统计信息
export function getDatabaseStats() {
  return request({
    url: '/databases/stats',
    method: 'get'
  })
}

// 获取数据库列表
export function getDatabases(params) {
  return request({
    url: '/databases',
    method: 'get',
    params
  })
}

// 创建数据库
export function createDatabase(data) {
  return request({
    url: '/databases',
    method: 'post',
    data
  })
}

// 获取数据库详情
export function getDatabase(id) {
  return request({
    url: `/databases/${id}`,
    method: 'get'
  })
}

// 删除数据库
export function deleteDatabase(id) {
  return request({
    url: `/databases/${id}`,
    method: 'delete'
  })
}

// 备份数据库
export function backupDatabase(id, backupType = 'full', compression = 'gzip') {
  return request({
    url: `/databases/${id}/backup`,
    method: 'post',
    data: { backup_type: backupType, compression }
  })
}

// 批量备份数据库
export function batchBackupDatabases(databaseIds, backupType = 'full', compression = 'gzip') {
  return request({
    url: '/databases/batch-backup',
    method: 'post',
    data: { database_ids: databaseIds, backup_type: backupType, compression }
  })
}

// 优化数据库
export function optimizeDatabase(id) {
  return request({
    url: `/databases/${id}/optimize`,
    method: 'post'
  })
}

// 修复数据库
export function repairDatabase(id) {
  return request({
    url: `/databases/${id}/repair`,
    method: 'post'
  })
}

// 获取数据库用户列表
export function getDatabaseUsers(databaseId) {
  return request({
    url: `/databases/${databaseId}/users`,
    method: 'get'
  })
}

// 创建数据库用户
export function createDatabaseUser(databaseId, data) {
  return request({
    url: `/databases/${databaseId}/users`,
    method: 'post',
    data
  })
}

// 删除数据库用户
export function deleteDatabaseUser(databaseId, userId) {
  return request({
    url: `/databases/${databaseId}/users/${userId}`,
    method: 'delete'
  })
}

// 获取数据库备份列表
export function getDatabaseBackups(databaseId) {
  return request({
    url: `/databases/${databaseId}/backups`,
    method: 'get'
  })
}

// 导出数据库
export function exportDatabase(id, format = 'sql') {
  return request({
    url: `/databases/${id}/export`,
    method: 'post',
    data: { format }
  })
}

// 导入数据库
export function importDatabase(id, sqlFile) {
  return request({
    url: `/databases/${id}/import`,
    method: 'post',
    data: { sql_file: sqlFile }
  })
}

// 测试数据库连接
export function testDatabaseConnection(connectionData) {
  return request({
    url: '/databases/test-connection',
    method: 'post',
    data: connectionData
  })
}

// 获取数据库监控数据
export function getDatabaseMonitor(id, timeRange = '1h') {
  return request({
    url: `/databases/${id}/monitor`,
    method: 'get',
    params: { time_range: timeRange }
  })
}
