-- DEV: DONE 221020
-- PROD: DONE 221020
ALTER TABLE register DROP COLUMN division;
ALTER TABLE register DROP COLUMN rank_start;
ALTER TABLE register ADD COLUMN division VARCHAR(2) DEFAULT NULL;
ALTER TABLE register ADD COLUMN rank_start SMALLINT(10) DEFAULT NULL;