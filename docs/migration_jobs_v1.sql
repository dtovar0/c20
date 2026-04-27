-- Script de migración para compatibilidad con Jobs en PSX5K
-- Ejecutar en el servidor remoto para asegurar que el esquema coincide con el código nuevo.

-- 1. Crear tabla de Jobs si no existe
CREATE TABLE IF NOT EXISTS psx5k_jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(100) NOT NULL,
    tarea VARCHAR(50),
    accion_tipo VARCHAR(50),
    datos_tipo VARCHAR(50),
    routing_label VARCHAR(100),
    archivo_origen VARCHAR(255),
    run_force BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Añadir columna job_id a psx5k_tasks si no existe
SET @column_exists = (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'psx5k_tasks' AND column_name = 'job_id' AND table_schema = DATABASE());

SET @sql_stmt = IF(@column_exists = 0, 
    'ALTER TABLE psx5k_tasks ADD COLUMN job_id INT NOT NULL AFTER id', 
    'SELECT \"Column job_id already exists\"');

PREPARE stmt FROM @sql_stmt;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3. Si se añadió la columna, crear la restricción de llave foránea
SET @fk_exists = (SELECT COUNT(*) FROM information_schema.key_column_usage WHERE table_name = 'psx5k_tasks' AND column_name = 'job_id' AND constraint_name = 'fk_tasks_job' AND table_schema = DATABASE());

SET @sql_stmt_fk = IF(@fk_exists = 0, 
    'ALTER TABLE psx5k_tasks ADD CONSTRAINT fk_tasks_job FOREIGN KEY (job_id) REFERENCES psx5k_jobs(id) ON DELETE CASCADE', 
    'SELECT \"FK already exists\"');

PREPARE stmt_fk FROM @sql_stmt_fk;
EXECUTE stmt_fk;
DEALLOCATE PREPARE stmt_fk;

-- 4. Asegurar que fecha_inicio existe en psx5k_tasks
SET @date_exists = (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'psx5k_tasks' AND column_name = 'fecha_inicio' AND table_schema = DATABASE());

SET @sql_stmt_date = IF(@date_exists = 0, 
    'ALTER TABLE psx5k_tasks ADD COLUMN fecha_inicio DATETIME AFTER estado', 
    'SELECT \"Column fecha_inicio already exists\"');

PREPARE stmt_date FROM @sql_stmt_date;
EXECUTE stmt_date;
DEALLOCATE PREPARE stmt_date;
