-- Issue ufolep13volley#482 : un sondage est rempli au nom d'une ÉQUIPE.
--
-- Il n'était rattaché qu'à son auteur (`user_id`). L'équipe était retrouvée
-- par `users_teams` : un responsable de club qui remplit le sondage d'une
-- équipe de son club, choisie dans le menu, n'y est pas rattaché. Son sondage
-- n'était ni compté (« sondage à remplir »), ni relu (formulaire vierge à
-- chaque visite), ni pris en compte dans le classement fair-play.
--
-- Ordre imposé : les vues lisent la colonne, elle doit exister avant.

-- 1. la colonne
ALTER TABLE survey
    ADD COLUMN id_equipe SMALLINT NULL DEFAULT NULL AFTER id_match,
    ADD KEY idx_survey_match_team (id_match, id_equipe),
    ADD CONSTRAINT survey_ibfk_3 FOREIGN KEY (id_equipe)
        REFERENCES equipes (id_equipe) ON DELETE SET NULL ON UPDATE RESTRICT;

-- 2. reprise : l'équipe du compte qui joue le match (comme le faisaient les
--    vues), sinon celle du club qu'il gère, quand les deux équipes sont de
--    clubs différents. Sinon NULL : le sondage n'était déjà pas compté.
UPDATE survey s
    JOIN matches m ON m.id_match = s.id_match
    JOIN equipes ed ON ed.id_equipe = m.id_equipe_dom
    JOIN equipes ee ON ee.id_equipe = m.id_equipe_ext
SET s.id_equipe = CASE
    WHEN EXISTS(SELECT 1 FROM users_teams ut WHERE ut.user_id = s.user_id AND ut.team_id = m.id_equipe_dom)
        THEN m.id_equipe_dom
    WHEN EXISTS(SELECT 1 FROM users_teams ut WHERE ut.user_id = s.user_id AND ut.team_id = m.id_equipe_ext)
        THEN m.id_equipe_ext
    WHEN ed.id_club <> ee.id_club
        AND EXISTS(SELECT 1 FROM users_clubs uc WHERE uc.user_id = s.user_id AND uc.club_id = ed.id_club)
        THEN m.id_equipe_dom
    WHEN ed.id_club <> ee.id_club
        AND EXISTS(SELECT 1 FROM users_clubs uc WHERE uc.user_id = s.user_id AND uc.club_id = ee.id_club)
        THEN m.id_equipe_ext
    END;

-- 3. rejouer sql/views/matchs_view.sql (sondage compté à son équipe) puis
--    sql/views/survey_view_raw.sql (fair-play : équipe du sondage, dernier
--    sondage de chaque équipe pour chaque match).

-- 4. côté dépôt applicatif, mettre à jour le schéma de CI
--    (`.github/ci/schema.sql`).
