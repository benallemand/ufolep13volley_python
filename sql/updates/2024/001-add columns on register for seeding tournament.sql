-- DEV: DONE 240824
-- PROD: DONE 240824
ALTER TABLE register
    DROP COLUMN is_seeding_tournament_requested;
ALTER TABLE register
    ADD COLUMN is_seeding_tournament_requested BIT(1) DEFAULT 0;
ALTER TABLE register
    DROP COLUMN can_seeding_tournament_setup;
ALTER TABLE register
    ADD COLUMN can_seeding_tournament_setup BIT(1) DEFAULT 0;