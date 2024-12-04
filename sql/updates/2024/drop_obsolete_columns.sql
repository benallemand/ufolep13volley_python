-- DEV: DONE 241204
-- PROD: DONE 241204
ALTER TABLE joueurs DROP COLUMN est_actif;
ALTER TABLE matches DROP COLUMN forfait_dom;
ALTER TABLE matches DROP COLUMN forfait_ext;
ALTER TABLE matches DROP COLUMN sheet_received;