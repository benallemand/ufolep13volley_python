-- DEV: DONE 230118
-- PROD: DONE 230118
ALTER TABLE equipes
    DROP COLUMN is_cup_registered;
ALTER TABLE equipes
    ADD COLUMN is_cup_registered BIT(1) DEFAULT 0;
UPDATE equipes
SET is_cup_registered = 1
WHERE code_competition = 'm';
