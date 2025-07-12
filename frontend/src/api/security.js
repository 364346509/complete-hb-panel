import request from '@/utils/request'

// 获取安全仪表盘数据
export function getSecurityDashboard() {
  return request({
    url: '/security/dashboard',
    method: 'get'
  })
}

// 防火墙管理
export function getFirewallRules() {
  return request({
    url: '/security/firewall/rules',
    method: 'get'
  })
}

export function createFirewallRule(data) {
  return request({
    url: '/security/firewall/rules',
    method: 'post',
    data
  })
}

export function deleteFirewallRule(id) {
  return request({
    url: `/security/firewall/rules/${id}`,
    method: 'delete'
  })
}

export function toggleFirewallRule(id) {
  return request({
    url: `/security/firewall/rules/${id}/toggle`,
    method: 'post'
  })
}

export function toggleFirewall() {
  return request({
    url: '/security/firewall/toggle',
    method: 'post'
  })
}

// SSL证书管理
export function getSSLCertificates() {
  return request({
    url: '/security/ssl/certificates',
    method: 'get'
  })
}

export function renewSSLCertificate(id) {
  return request({
    url: `/security/ssl/certificates/${id}/renew`,
    method: 'post'
  })
}

// 安全事件
export function getSecurityEvents(params) {
  return request({
    url: '/security/events',
    method: 'get',
    params
  })
}

export function handleSecurityEvent(id, data) {
  return request({
    url: `/security/events/${id}/handle`,
    method: 'post',
    data
  })
}

// IP黑名单
export function getIPBlacklist() {
  return request({
    url: '/security/blacklist',
    method: 'get'
  })
}

export function addIPBlacklist(data) {
  return request({
    url: '/security/blacklist',
    method: 'post',
    data
  })
}

export function removeIPBlacklist(id) {
  return request({
    url: `/security/blacklist/${id}`,
    method: 'delete'
  })
}

// IP白名单
export function getIPWhitelist() {
  return request({
    url: '/security/whitelist',
    method: 'get'
  })
}

export function addIPWhitelist(data) {
  return request({
    url: '/security/whitelist',
    method: 'post',
    data
  })
}

export function removeIPWhitelist(id) {
  return request({
    url: `/security/whitelist/${id}`,
    method: 'delete'
  })
}

// SSH配置
export function getSSHConfig() {
  return request({
    url: '/security/ssh/config',
    method: 'get'
  })
}

export function updateSSHConfig(data) {
  return request({
    url: '/security/ssh/config',
    method: 'put',
    data
  })
}

// 安全扫描
export function startSecurityScan(scanType, target) {
  return request({
    url: '/security/scan/start',
    method: 'post',
    data: { scan_type: scanType, target }
  })
}

export function getScanResults(scanId) {
  return request({
    url: '/security/scan/results',
    method: 'get',
    params: { scan_id: scanId }
  })
}
