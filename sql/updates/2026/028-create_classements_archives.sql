-- Issue #435 : classement final de chaque demi-saison, figé avant que la
-- demi-saison suivante ne l'efface.
--
-- Les pénalités et les reports (`classements.penalite`, `report_count`) ne
-- sont attachés à aucun match : ils sont remis à zéro à chaque demi-saison,
-- et `classements` est reconstruit à l'initialisation de la suivante. Une
-- fois les matchs archivés, le classement n'est même plus calculable : les
-- deux calculs (`get_rank_ffvb_by_competition_division.sql`,
-- `get_rank_by_competition_division.sql`) ignorent les matchs ARCHIVED.
--
-- Une ligne par équipe et par division, recopiée telle que le site
-- l'affichait (`Rank::getRank`) : des valeurs, pas des calculs refaits à la
-- lecture. Le nom et le club de l'équipe sont ceux de l'époque.
--
-- `demi_saison` : 1 ou 2 pour un championnat, 0 pour une compétition qui
-- dure toute la saison (coupes).
-- `source` : FROZEN (figé depuis le site), REBUILT (reconstitué après coup
-- depuis les matchs archivés : sans pénalités ni reports).

CREATE TABLE classements_archives (
    id INT NOT NULL AUTO_INCREMENT,
    saison VARCHAR(9) NOT NULL,
    demi_saison TINYINT NOT NULL DEFAULT 0,
    code_competition VARCHAR(2) NOT NULL,
    libelle_competition VARCHAR(100) NOT NULL,
    division VARCHAR(2) NOT NULL,
    rang SMALLINT NOT NULL,
    id_equipe SMALLINT NOT NULL,
    nom_equipe VARCHAR(50) NOT NULL,
    club VARCHAR(200) DEFAULT NULL,
    points SMALLINT NOT NULL,
    joues SMALLINT NOT NULL,
    gagnes SMALLINT NOT NULL,
    perdus SMALLINT NOT NULL,
    sets_pour SMALLINT NOT NULL,
    sets_contre SMALLINT NOT NULL,
    quotient_sets DECIMAL(10, 3) DEFAULT NULL,
    quotient_points DECIMAL(10, 3) DEFAULT NULL,
    penalites SMALLINT NOT NULL DEFAULT 0,
    reports SMALLINT NOT NULL DEFAULT 0,
    forfaits SMALLINT NOT NULL DEFAULT 0,
    premier_match DATE DEFAULT NULL,
    dernier_match DATE DEFAULT NULL,
    source VARCHAR(10) NOT NULL DEFAULT 'FROZEN',
    frozen_at DATETIME NOT NULL,
    frozen_by SMALLINT DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_classement_archive (saison, demi_saison, code_competition, division, id_equipe),
    KEY idx_classement_archive_periode (saison, demi_saison, code_competition)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
