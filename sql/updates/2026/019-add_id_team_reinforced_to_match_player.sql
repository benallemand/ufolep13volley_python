-- Issue #348 : un renfort est rattaché à l'équipe qu'il renforce.
--
-- Jusqu'ici, `match_player(id_match, id_player)` ne disait ni qu'un joueur était
-- un renfort, ni pour quelle équipe il jouait : un renfort était seulement
-- déduit (présent membre d'aucune des deux équipes), et compté pour les deux.
-- Les règles #348 (compléter jusqu'à 6 / 4, un renfort par équipe, mixité) ont
-- besoin de l'équipe.
--
-- NULL pour un joueur de l'équipe, et pour les renforts saisis avant #348 :
-- `match_players_count_view` continue de compter ceux-là pour les deux équipes.
--
-- Ordre imposé : la vue lit la colonne, elle doit exister avant d'être recréée.

-- 1. la colonne
ALTER TABLE match_player
    ADD COLUMN id_team_reinforced SMALLINT NULL DEFAULT NULL AFTER id_player,
    ADD KEY id_team_reinforced (id_team_reinforced),
    ADD CONSTRAINT match_player_ibfk_3 FOREIGN KEY (id_team_reinforced)
        REFERENCES equipes (id_equipe) ON DELETE SET NULL ON UPDATE RESTRICT;

-- 2. rejouer sql/views/match_players_count_view.sql (renforts comptés par
--    équipe, et par sexe pour la mixité du championnat mixte).
--    Inutile de rejouer sql/views/matchs_view.sql : matchs_view lit
--    match_players_count_view par son nom, et les colonnes qu'elle en utilise
--    (id_match, count_status) sont inchangées.

-- 3. côté dépôt applicatif, regénérer le schéma de CI :
--    pwsh .github/ci/dump-schema.ps1
