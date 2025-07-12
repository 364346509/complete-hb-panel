-- HB-Panel 数据库初始化脚本

-- 设置字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 创建用户表
CREATE TABLE IF NOT EXISTS `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `full_name` varchar(100) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `is_superuser` tinyint(1) DEFAULT '0',
  `avatar` varchar(255) DEFAULT NULL,
  `last_login` datetime DEFAULT NULL,
  `login_count` int DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建网站表
CREATE TABLE IF NOT EXISTS `websites` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `domain` varchar(255) NOT NULL,
  `domains` json DEFAULT NULL,
  `path` varchar(500) NOT NULL,
  `php_version` varchar(10) DEFAULT '8.1',
  `status` enum('running','stopped','error') DEFAULT 'stopped',
  `ssl_type` enum('none','lets_encrypt','self_signed','custom') DEFAULT 'none',
  `ssl_cert` text,
  `ssl_key` text,
  `ssl_auto_renew` tinyint(1) DEFAULT '1',
  `index_files` varchar(255) DEFAULT 'index.html,index.htm,index.php',
  `gzip_enable` tinyint(1) DEFAULT '1',
  `proxy_cache` tinyint(1) DEFAULT '0',
  `backup_enable` tinyint(1) DEFAULT '0',
  `backup_keep_days` int DEFAULT '7',
  `rewrite_rule` text,
  `total_requests` bigint DEFAULT '0',
  `total_traffic` bigint DEFAULT '0',
  `last_access` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `domain` (`domain`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建数据库表
CREATE TABLE IF NOT EXISTS `databases` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL,
  `charset` varchar(32) DEFAULT 'utf8mb4',
  `collation` varchar(64) DEFAULT 'utf8mb4_unicode_ci',
  `status` enum('active','inactive','error') DEFAULT 'active',
  `size` bigint DEFAULT '0',
  `table_count` int DEFAULT '0',
  `description` text,
  `auto_backup` tinyint(1) DEFAULT '0',
  `backup_keep_days` int DEFAULT '7',
  `last_backup` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建数据库用户表
CREATE TABLE IF NOT EXISTS `database_users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(32) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `database_id` int NOT NULL,
  `privileges` json DEFAULT NULL,
  `host` varchar(255) DEFAULT '%',
  `is_active` tinyint(1) DEFAULT '1',
  `last_login` datetime DEFAULT NULL,
  `login_count` int DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `database_id` (`database_id`),
  CONSTRAINT `database_users_ibfk_1` FOREIGN KEY (`database_id`) REFERENCES `databases` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建备份表
CREATE TABLE IF NOT EXISTS `website_backups` (
  `id` int NOT NULL AUTO_INCREMENT,
  `website_id` int NOT NULL,
  `name` varchar(200) NOT NULL,
  `type` varchar(20) DEFAULT 'full',
  `file_path` varchar(500) NOT NULL,
  `file_size` bigint DEFAULT '0',
  `status` varchar(20) DEFAULT 'completed',
  `error_message` text,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `website_id` (`website_id`),
  CONSTRAINT `website_backups_ibfk_1` FOREIGN KEY (`website_id`) REFERENCES `websites` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建数据库备份表
CREATE TABLE IF NOT EXISTS `database_backups` (
  `id` int NOT NULL AUTO_INCREMENT,
  `database_id` int NOT NULL,
  `name` varchar(200) NOT NULL,
  `file_path` varchar(500) NOT NULL,
  `file_size` bigint DEFAULT '0',
  `backup_type` varchar(20) DEFAULT 'full',
  `compression` varchar(20) DEFAULT 'gzip',
  `status` varchar(20) DEFAULT 'completed',
  `error_message` text,
  `started_at` datetime DEFAULT NULL,
  `completed_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `database_id` (`database_id`),
  CONSTRAINT `database_backups_ibfk_1` FOREIGN KEY (`database_id`) REFERENCES `databases` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建系统设置表
CREATE TABLE IF NOT EXISTS `system_settings` (
  `id` int NOT NULL AUTO_INCREMENT,
  `key` varchar(100) NOT NULL,
  `value` text,
  `description` varchar(255) DEFAULT NULL,
  `type` varchar(20) DEFAULT 'string',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `key` (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建操作日志表
CREATE TABLE IF NOT EXISTS `operation_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `action` varchar(100) NOT NULL,
  `resource_type` varchar(50) DEFAULT NULL,
  `resource_id` int DEFAULT NULL,
  `details` json DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` varchar(500) DEFAULT NULL,
  `status` varchar(20) DEFAULT 'success',
  `error_message` text,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `action` (`action`),
  KEY `created_at` (`created_at`),
  CONSTRAINT `operation_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入默认管理员用户
-- 密码: admin123 (bcrypt加密)
INSERT IGNORE INTO `users` (`username`, `email`, `password_hash`, `full_name`, `is_active`, `is_superuser`) VALUES
('admin', 'admin@hb-panel.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3L3jzjvQSG', 'Administrator', 1, 1);

-- 插入默认系统设置
INSERT IGNORE INTO `system_settings` (`key`, `value`, `description`, `type`) VALUES
('panel_name', 'HB-Panel', '面板名称', 'string'),
('panel_version', '1.0.0', '面板版本', 'string'),
('default_php_version', '8.1', '默认PHP版本', 'string'),
('auto_backup_enabled', 'true', '自动备份启用状态', 'boolean'),
('backup_keep_days', '7', '备份保留天数', 'integer'),
('ssl_auto_renew', 'true', 'SSL证书自动续期', 'boolean'),
('security_scan_enabled', 'true', '安全扫描启用状态', 'boolean'),
('log_retention_days', '30', '日志保留天数', 'integer');

SET FOREIGN_KEY_CHECKS = 1;
