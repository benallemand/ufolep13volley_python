-- Issue #247 : fusion des comptes — un email = un compte.
-- L'ancien modèle à profil exclusif forçait les admins aussi responsables
-- d'équipe à avoir deux comptes. Pour chaque email en doublon, on conserve
-- le compte dont login = email et on lui transfère les liaisons et le rôle
-- admin de l'autre compte, puis on supprime le doublon.
-- Enfin, on garantit l'unicité des emails.
--
-- NB : le flag is_admin du doublon est capturé dans tmp_merge dès le départ,
-- car MySQL interdit de mettre à jour comptes_acces avec une sous-requête
-- sur cette même table (erreur 1093).

CREATE TEMPORARY TABLE tmp_merge AS
SELECT keep.id AS keep_id, dup.id AS dup_id, dup.is_admin AS dup_is_admin
FROM comptes_acces keep
         JOIN comptes_acces dup ON dup.email = keep.email AND dup.id <> keep.id
WHERE keep.login = keep.email
  AND dup.login <> dup.email;

-- rôle admin : conservé si l'un des deux comptes l'avait
UPDATE comptes_acces ca
    JOIN tmp_merge m ON ca.id = m.keep_id
SET ca.is_admin = 1
WHERE m.dup_is_admin = 1;

-- liaisons équipes (INSERT IGNORE : PK composite user_id/team_id)
INSERT IGNORE INTO users_teams (user_id, team_id)
SELECT m.keep_id, ut.team_id
FROM users_teams ut
         JOIN tmp_merge m ON ut.user_id = m.dup_id;
DELETE ut FROM users_teams ut JOIN tmp_merge m ON ut.user_id = m.dup_id;

-- liaisons clubs
INSERT IGNORE INTO users_clubs (user_id, club_id)
SELECT m.keep_id, uc.club_id
FROM users_clubs uc
         JOIN tmp_merge m ON uc.user_id = m.dup_id;
DELETE uc FROM users_clubs uc JOIN tmp_merge m ON uc.user_id = m.dup_id;

-- historique d'activité et sondages : réattribués au compte conservé
UPDATE activity a JOIN tmp_merge m ON a.user_id = m.dup_id SET a.user_id = m.keep_id;
UPDATE survey s JOIN tmp_merge m ON s.user_id = m.dup_id SET s.user_id = m.keep_id;

-- anciens profils du doublon (table encore présente jusqu'à la migration de drop)
DELETE up FROM users_profiles up JOIN tmp_merge m ON up.user_id = m.dup_id;

-- suppression des comptes doublons
DELETE ca FROM comptes_acces ca JOIN tmp_merge m ON ca.id = m.dup_id;

DROP TEMPORARY TABLE tmp_merge;

-- un email = un compte
ALTER TABLE comptes_acces
    ADD UNIQUE KEY uq_email (email);
