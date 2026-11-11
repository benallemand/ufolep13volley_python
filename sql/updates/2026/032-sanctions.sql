-- Issue #475 : les pénalités deviennent des sanctions.
--
-- Une sanction est un manquement constaté (motif, match éventuel), avec la
-- sanction envisagée. La commission l'APPLIQUE ou la LÈVE (clémence) en
-- réunion de fin de demi-saison : seule une sanction appliquée touche le
-- classement. Avant, chaque pénalité retirait ses points tout de suite.
--
-- Reprise de l'existant :
--  - pénalités automatiques actives -> sanctions « constatées », point rendu
--    au classement en attendant la réunion (décision de la commission) ;
--  - pénalités automatiques annulées -> sanctions « levées » ;
--  - points de pénalité manuels restants -> sanction « appliquée », motif
--    « autre » (le motif n'était pas enregistré), pour que `penalite` reste
--    la somme des sanctions appliquées.
--
-- Après la migration : régénérer le schéma de la CI
-- (`pwsh .github/ci/dump-schema.ps1` dans le dépôt ufolep13volley).

CREATE TABLE sanctions
(
    id               INT                                     NOT NULL AUTO_INCREMENT,
    code_competition VARCHAR(2)                              NOT NULL,
    id_equipe        SMALLINT                                NOT NULL,
    id_match         BIGINT                                  NULL DEFAULT NULL,
    motif            VARCHAR(40)                             NOT NULL,
    sanction_type    VARCHAR(20)                             NOT NULL,
    points           TINYINT                                 NOT NULL DEFAULT 0,
    comment          VARCHAR(1000)                           NULL DEFAULT NULL,
    source           ENUM ('AUTO', 'MANUELLE')               NOT NULL DEFAULT 'MANUELLE',
    status           ENUM ('CONSTATEE', 'APPLIQUEE', 'LEVEE') NOT NULL DEFAULT 'CONSTATEE',
    created_at       DATETIME                                NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by       SMALLINT                                NULL DEFAULT NULL,
    decided_at       DATETIME                                NULL DEFAULT NULL,
    decided_by       SMALLINT                                NULL DEFAULT NULL,
    decision_comment VARCHAR(1000)                           NULL DEFAULT NULL,
    effect_backup    JSON                                    NULL DEFAULT NULL,
    PRIMARY KEY (id),
    KEY idx_sanctions_team (id_equipe, code_competition),
    KEY idx_sanctions_match (id_match),
    KEY idx_sanctions_status (status),
    CONSTRAINT fk_sanctions_equipe FOREIGN KEY (id_equipe) REFERENCES equipes (id_equipe) ON DELETE CASCADE,
    CONSTRAINT fk_sanctions_match FOREIGN KEY (id_match) REFERENCES matches (id_match) ON DELETE SET NULL
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci;

-- Forfait général : l'équipe sort du classement de sa compétition.
ALTER TABLE classements
    ADD COLUMN withdrawn_at DATETIME NULL DEFAULT NULL;

-- Pénalités automatiques -> sanctions
INSERT INTO sanctions (code_competition, id_equipe, id_match, motif, sanction_type, points, source, status,
                       created_at, decided_at, decision_comment)
SELECT p.code_competition,
       p.id_equipe,
       p.id_match,
       'feuille_non_signee',
       'points',
       1,
       'AUTO',
       IF(p.cancelled_at IS NULL, 'CONSTATEE', 'LEVEE'),
       p.created_at,
       p.cancelled_at,
       IF(p.cancelled_at IS NULL, NULL, 'Pénalité automatique annulée avant la refonte des sanctions')
FROM match_penalties p;

-- Le point des pénalités automatiques actives est rendu : elles attendent la réunion.
UPDATE classements c
    JOIN (SELECT id_equipe, code_competition, COUNT(*) AS n
          FROM match_penalties
          WHERE cancelled_at IS NULL
          GROUP BY id_equipe, code_competition) a
    ON a.id_equipe = c.id_equipe AND a.code_competition = c.code_competition
SET c.penalite = GREATEST(c.penalite - a.n, 0);

-- Points manuels restants : sanction appliquée, motif inconnu.
INSERT INTO sanctions (code_competition, id_equipe, motif, sanction_type, points, comment, source, status,
                       decided_at, decision_comment)
SELECT c.code_competition,
       c.id_equipe,
       'autre',
       'points',
       c.penalite,
       'Points de pénalité saisis avant la refonte des sanctions (motif non enregistré)',
       'MANUELLE',
       'APPLIQUEE',
       NOW(),
       'Reprise de l''existant'
FROM classements c
WHERE c.penalite > 0;

DROP TABLE match_penalties;
