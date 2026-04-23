
-- === NEXUS ADMIN SYSTEM === --
-- Database Structural Export --
-- Target: MySQL 8.0+ --

SET FOREIGN_KEY_CHECKS = 0;

-- 1. AUTHENTICATION MODULE
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(80) UNIQUE NOT NULL,
    `password_hash` VARCHAR(255),
    `email` VARCHAR(120),
    `role` VARCHAR(20) DEFAULT 'operador',
    `is_active` BOOLEAN DEFAULT TRUE,
    INDEX (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `auth_config` (
    `id` INT PRIMARY KEY DEFAULT 1,
    `ldap_host` VARCHAR(255),
    `ldap_port` INT DEFAULT 389,
    `ldap_ssl` BOOLEAN DEFAULT FALSE,
    `ldap_base_dn` VARCHAR(255),
    `ldap_user` VARCHAR(255),
    `ldap_pass` VARCHAR(255),
    `ldap_user_attr` VARCHAR(50) DEFAULT 'sAMAccountName',
    `ldap_group_admin` VARCHAR(255),
    `ldap_group_user` VARCHAR(255),
    `ldap_role_mappings` TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. AUDIT MODULE
CREATE TABLE IF NOT EXISTS `audit_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `level` VARCHAR(20) DEFAULT 'info',
    `user` VARCHAR(80),
    `action` VARCHAR(100),
    `detail` TEXT,
    INDEX (`user`),
    INDEX (`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. PSX5K MODULE (MASTER-DETAIL ARCHITECTURE)
CREATE TABLE IF NOT EXISTS `psx5k_jobs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `usuario` VARCHAR(80),
    `tarea` VARCHAR(50),
    `accion_tipo` VARCHAR(50),
    `datos_tipo` VARCHAR(50),
    `routing_label` VARCHAR(100),
    `archivo_origen` VARCHAR(255),
    `force` BOOLEAN DEFAULT FALSE,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX (`usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `psx5k_tasks` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `job_id` INT,
    `chunk_index` INT,
    `chunk_total` INT,
    `datos` LONGTEXT,
    `estado` VARCHAR(50) DEFAULT 'Pendiente',
    `fecha_inicio` DATETIME,
    `fecha_fin` DATETIME,
    `parent_id` INT NULL,
    `tipo` VARCHAR(20) DEFAULT 'normal',
    FOREIGN KEY (`job_id`) REFERENCES `psx5k_jobs`(`id`) ON DELETE CASCADE,
    INDEX (`job_id`),
    INDEX (`estado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `psx5k_details` (
    `id` INT PRIMARY KEY,
    `total` INT DEFAULT 0,
    `ok` INT DEFAULT 0,
    `fail` INT DEFAULT 0,
    `force_ok` INT DEFAULT 0,
    FOREIGN KEY (`id`) REFERENCES `psx5k_tasks`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `psx5k_history` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `task_id` INT,
    `numero` VARCHAR(20),
    `routing_label` VARCHAR(100),
    `estado` VARCHAR(20),
    `fecha` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`task_id`) REFERENCES `psx5k_tasks`(`id`) ON DELETE CASCADE,
    INDEX (`task_id`),
    INDEX (`numero`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;
