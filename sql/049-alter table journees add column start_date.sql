SET FOREIGN_KEY_CHECKS = 0;
ALTER TABLE journees DROP COLUMN start_date;
ALTER TABLE journees ADD COLUMN start_date DATE DEFAULT NULL;
ALTER TABLE journees CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE journees MODIFY COLUMN libelle VARCHAR(50) DEFAULT NULL;
SET FOREIGN_KEY_CHECKS = 1;
