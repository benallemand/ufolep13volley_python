-- Issues #425 et #426 : le journal d'activité enregistre l'équipe concernée
-- par une action, et l'administrateur qui agit « en tant que » un autre
-- compte.
--
-- #425 : l'historique d'une équipe était déduit des équipes de l'AUTEUR
-- (users_teams). Celui de Grans 2 contenait toutes les actions
-- d'administration d'un admin qui en est responsable (348 lignes au
-- 12/10/2026), visibles par l'autre responsable de l'équipe.
--
-- #426 : pendant « Agir en tant que », les actions étaient journalisées au
-- nom du compte cible, sans trace de l'admin.
--
-- Les types suivent `equipes.id_equipe` et `comptes_acces.id` (SMALLINT).

-- 1. Les colonnes.
ALTER TABLE activity
    ADD COLUMN id_team SMALLINT NULL AFTER user_id,
    ADD COLUMN original_user_id SMALLINT NULL AFTER id_team,
    ADD KEY idx_activity_team (id_team);

-- 2. Les lignes passées : rattachées à l'équipe que leur texte nomme sous la
--    forme « NOM(code) » (« Ajout de X a l'equipe KOKINOUS(mo) »,
--    « L'equipe Grans 2(m) a un nouveau responsable… »). Le nom le plus long
--    l'emporte, pour qu'« AH1 » ne prenne pas une ligne de « Les AH1 ». Les
--    autres (inscriptions, comptes, matchs…) restent sans équipe : elles
--    sortent des historiques d'équipe, et restent dans l'écran Activité.
UPDATE activity a
    JOIN (SELECT a2.id,
                 (SELECT e.id_equipe
                  FROM equipes e
                  WHERE a2.comment LIKE CONCAT('%', e.nom_equipe, '(', e.code_competition, ')%')
                  ORDER BY CHAR_LENGTH(e.nom_equipe) DESC, e.id_equipe
                  LIMIT 1) AS id_team
          FROM activity a2
          WHERE a2.id_team IS NULL) m ON m.id = a.id
SET a.id_team = m.id_team
WHERE m.id_team IS NOT NULL;

-- 3. À regarder après : lignes rattachées ou non.
SELECT id_team IS NOT NULL AS rattachee, COUNT(*) FROM activity GROUP BY 1;
