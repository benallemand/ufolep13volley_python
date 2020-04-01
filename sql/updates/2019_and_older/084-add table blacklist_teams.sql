SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS blacklist_teams;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE IF NOT EXISTS blacklist_teams
(
    id        SMALLINT(10) PRIMARY KEY NOT NULL AUTO_INCREMENT,
    id_team_1 SMALLINT(10)             NOT NULL,
    id_team_2 SMALLINT(10)             NOT NULL,
    FOREIGN KEY (id_team_1) REFERENCES equipes (id_equipe)
        ON DELETE CASCADE,
    FOREIGN KEY (id_team_2) REFERENCES equipes (id_equipe)
        ON DELETE CASCADE
)
    ENGINE = InnoDB
    DEFAULT CHARSET = latin1;
