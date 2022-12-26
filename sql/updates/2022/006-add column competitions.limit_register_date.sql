-- DEV: DONE 221226
-- PROD: DONE 221226
ALTER TABLE competitions
    DROP COLUMN limit_register_date;
ALTER TABLE competitions
    ADD COLUMN limit_register_date DATE DEFAULT NULL;
