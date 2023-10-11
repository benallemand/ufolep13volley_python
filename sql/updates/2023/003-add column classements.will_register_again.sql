-- DEV: DONE 231011
-- PROD: DONE 231011
ALTER TABLE classements
    DROP COLUMN will_register_again;
ALTER TABLE classements
    ADD COLUMN will_register_again BIT(1) DEFAULT 1;