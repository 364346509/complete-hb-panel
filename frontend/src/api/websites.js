import request from '@/utils/request'

// 获取网站统计信息
export function getWebsiteStats() {
  return request({
    url: '/websites/stats',
    method: 'get'
  })
}

// 获取网站列表
export function getWebsites(params) {
  return request({
    url: '/websites',
    method: 'get',
    params
  })
}

// 创建网站
export function createWebsite(data) {
  return request({
    url: '/websites',
    method: 'post',
    data
  })
}

// 获取网站详情
export function getWebsite(id) {
  return request({
    url: `/websites/${id}`,
    method: 'get'
  })
}

// 更新网站
export function updateWebsite(id, data) {
  return request({
    url: `/websites/${id}`,
    method: 'put',
    data
  })
}

// 删除网站
export function deleteWebsite(id) {
  return request({
    url: `/websites/${id}`,
    method: 'delete'
  })
}

// 启动网站
export function startWebsite(id) {
  return request({
    url: `/websites/${id}/start`,
    method: 'post'
  })
}

// 停止网站
export function stopWebsite(id) {
  return request({
    url: `/websites/${id}/stop`,
    method: 'post'
  })
}

// 备份网站
export function backupWebsite(id, backupType = 'full') {
  return request({
    url: `/websites/${id}/backup`,
    method: 'post',
    data: { backup_type: backupType }
  })
}

// 获取网站日志
export function getWebsiteLogs(id, logType = 'access', lines = 100) {
  return request({
    url: `/websites/${id}/logs`,
    method: 'get',
    params: { log_type: logType, lines }
  })
}

// 获取SSL信息
export function getSSLInfo(id) {
  return request({
    url: `/websites/${id}/ssl`,
    method: 'get'
  })
}

// 配置SSL
export function configureSSL(id, sslType, autoRenew = true) {
  return request({
    url: `/websites/${id}/ssl`,
    method: 'post',
    data: { ssl_type: sslType, auto_renew: autoRenew }
  })
}

// 获取PHP版本列表
export function getPHPVersions() {
  return request({
    url: '/websites/php-versions',
    method: 'get'
  })
}

// 获取伪静态规则模板
export function getRewriteRules() {
  return request({
    url: '/websites/rewrite-rules',
    method: 'get'
  })
}
