-- DEV: DONE 221212
-- PROD: DONE 221212
ALTER TABLE comptes_acces
    DROP COLUMN password_hash;

ALTER TABLE comptes_acces
    ADD COLUMN password_hash varchar(200) DEFAULT NULL;

UPDATE comptes_acces
SET password_hash = MD5(CONCAT(login, password));

ALTER TABLE comptes_acces DROP COLUMN password;
ALTER TABLE comptes_acces DROP COLUMN is_email_sent;

