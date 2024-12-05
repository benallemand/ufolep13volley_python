-- DEV: DONE 241205
-- PROD: DONE 241205
ALTER TABLE joueurs DROP COLUMN est_actif;
ALTER TABLE matches DROP COLUMN forfait_dom;
ALTER TABLE matches DROP COLUMN forfait_ext;
ALTER TABLE matches DROP COLUMN sheet_received;
ALTER TABLE matches DROP COLUMN score_equipe_dom;
ALTER TABLE matches DROP COLUMN score_equipe_ext;
commit;