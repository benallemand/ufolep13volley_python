-- DEV: DONE 231006
-- PROD: DONE 231006
ALTER TABLE register
    DROP COLUMN is_paid;
ALTER TABLE register
    ADD COLUMN is_paid BIT(1) DEFAULT 0;