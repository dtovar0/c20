-- Migration V3.0: Adding User Preference Columns
-- This script adds the preference columns to the users table.

ALTER TABLE `users` 
ADD COLUMN `pref_notifications` TINYINT(1) DEFAULT 1,
ADD COLUMN `pref_refresh_interval` INT DEFAULT 60,
ADD COLUMN `pref_tour_enabled` TINYINT(1) DEFAULT 1,
ADD COLUMN `pref_email_notifications` TINYINT(1) DEFAULT 1;

-- If you want to move them after created_at for aesthetic reasons:
ALTER TABLE `users` 
MODIFY COLUMN `pref_notifications` TINYINT(1) DEFAULT 1 AFTER `created_at`,
MODIFY COLUMN `pref_refresh_interval` INT DEFAULT 60 AFTER `pref_notifications`,
MODIFY COLUMN `pref_tour_enabled` TINYINT(1) DEFAULT 1 AFTER `pref_refresh_interval`,
MODIFY COLUMN `pref_email_notifications` TINYINT(1) DEFAULT 1 AFTER `pref_tour_enabled`;
