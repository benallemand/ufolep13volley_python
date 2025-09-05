-- DEV: DONE 250905
-- PROD: DONE 250905
ALTER TABLE register
    DROP COLUMN is_cup_registered;
ALTER TABLE register
    ADD COLUMN is_cup_registered BIT(1) DEFAULT 0;