-- DEV: DONE 230114
-- PROD: DONE 230114
ALTER TABLE competitions
    DROP COLUMN start_register_date;
ALTER TABLE competitions
    ADD COLUMN start_register_date DATE DEFAULT NULL;
