-- Migration: Add set scores columns to live_scores table
-- Issue: #186 - Live Scoring feature - store individual set scores

ALTER TABLE live_scores
    ADD COLUMN set_1_dom TINYINT NOT NULL DEFAULT 0 AFTER sets_ext,
    ADD COLUMN set_1_ext TINYINT NOT NULL DEFAULT 0 AFTER set_1_dom,
    ADD COLUMN set_2_dom TINYINT NOT NULL DEFAULT 0 AFTER set_1_ext,
    ADD COLUMN set_2_ext TINYINT NOT NULL DEFAULT 0 AFTER set_2_dom,
    ADD COLUMN set_3_dom TINYINT NOT NULL DEFAULT 0 AFTER set_2_ext,
    ADD COLUMN set_3_ext TINYINT NOT NULL DEFAULT 0 AFTER set_3_dom,
    ADD COLUMN set_4_dom TINYINT NOT NULL DEFAULT 0 AFTER set_3_ext,
    ADD COLUMN set_4_ext TINYINT NOT NULL DEFAULT 0 AFTER set_4_dom,
    ADD COLUMN set_5_dom TINYINT NOT NULL DEFAULT 0 AFTER set_4_ext,
    ADD COLUMN set_5_ext TINYINT NOT NULL DEFAULT 0 AFTER set_5_dom;
