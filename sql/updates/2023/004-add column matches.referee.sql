-- DEV: DONE 231028
-- PROD: DONE 231028
ALTER TABLE matches
    DROP COLUMN referee;
ALTER TABLE matches
    ADD COLUMN referee ENUM ('HOME', 'AWAY', 'BOTH') DEFAULT 'HOME';