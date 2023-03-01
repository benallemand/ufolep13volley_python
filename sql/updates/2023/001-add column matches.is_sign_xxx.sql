-- DEV: reDONE 230301
-- PROD: DONE 230301
ALTER TABLE matches
    DROP COLUMN is_sign_team_dom;
ALTER TABLE matches
    ADD COLUMN is_sign_team_dom BIT(1) DEFAULT 0;
ALTER TABLE matches
    DROP COLUMN is_sign_team_ext;
ALTER TABLE matches
    ADD COLUMN is_sign_team_ext BIT(1) DEFAULT 0;
ALTER TABLE matches
    DROP COLUMN is_sign_match_dom;
ALTER TABLE matches
    ADD COLUMN is_sign_match_dom BIT(1) DEFAULT 0;
ALTER TABLE matches
    DROP COLUMN is_sign_match_ext;
ALTER TABLE matches
    ADD COLUMN is_sign_match_ext BIT(1) DEFAULT 0;