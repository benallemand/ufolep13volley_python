-- Issue #345 : pénalité automatique si la feuille de match n'est pas signée
-- 48 h après le match.
--
-- `classements.penalite` n'est qu'un compteur : il ne dit pas quel match a
-- causé une pénalité, ni si elle a déjà été appliquée. Cette table trace chaque
-- pénalité automatique, par match et par équipe ; la clé unique rend le cron
-- idempotent (il peut repasser sans pénaliser deux fois).
--
-- L'admin annule une pénalité par le bouton « -1 » du classement : la ligne
-- reste, comme historique, et empêche une nouvelle application.

CREATE TABLE match_penalties
(
    id               INT         NOT NULL AUTO_INCREMENT,
    id_match         BIGINT      NOT NULL,
    id_equipe        SMALLINT    NOT NULL,
    code_competition VARCHAR(2)  NOT NULL,
    reason           VARCHAR(50) NOT NULL,
    created_at       DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_match_team_reason (id_match, id_equipe, reason),
    KEY id_equipe (id_equipe),
    CONSTRAINT match_penalties_ibfk_1 FOREIGN KEY (id_match) REFERENCES matches (id_match) ON DELETE CASCADE,
    CONSTRAINT match_penalties_ibfk_2 FOREIGN KEY (id_equipe) REFERENCES equipes (id_equipe) ON DELETE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci;

-- côté dépôt applicatif, regénérer le schéma de CI :
--    pwsh .github/ci/dump-schema.ps1
