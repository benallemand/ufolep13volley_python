-- DEV: DONE 221228
-- PROD: DONE 221228
ALTER TABLE news
    DROP COLUMN is_disabled;
ALTER TABLE news
    ADD COLUMN is_disabled BIT(1) DEFAULT 0;
