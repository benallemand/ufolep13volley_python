-- DEV: DONE 220925
-- PROD: DONE 220925
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS register;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE IF NOT EXISTS register
(
    id                BIGINT(20) PRIMARY KEY NOT NULL AUTO_INCREMENT,
    new_team_name     VARCHAR(100) UNIQUE    NOT NULL,
    id_club           SMALLINT(10)           NOT NULL,
    id_competition    SMALLINT(10)           NOT NULL,
    old_team_id       SMALLINT(10) UNIQUE DEFAULT NULL,
    leader_name       VARCHAR(100)           NOT NULL,
    leader_first_name VARCHAR(100)           NOT NULL,
    leader_email      VARCHAR(100)           NOT NULL,
    leader_phone      VARCHAR(100)           NOT NULL,
    id_court_1        SMALLINT(10)        DEFAULT NULL,
    day_court_1       VARCHAR(100)        DEFAULT NULL,
    hour_court_1      VARCHAR(100)        DEFAULT NULL,
    id_court_2        SMALLINT(10)        DEFAULT NULL,
    day_court_2       VARCHAR(100)        DEFAULT NULL,
    hour_court_2      VARCHAR(100)        DEFAULT NULL,
    remarks           VARCHAR(5000)       DEFAULT NULL,
    creation_date     TIMESTAMP           DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (id_club) REFERENCES clubs (id)
        ON DELETE CASCADE,
    FOREIGN KEY (id_competition) REFERENCES competitions (id)
        ON DELETE CASCADE,
    FOREIGN KEY (old_team_id) REFERENCES equipes (id_equipe)
        ON DELETE CASCADE,
    FOREIGN KEY (id_court_1) REFERENCES gymnase (id)
        ON DELETE CASCADE,
    FOREIGN KEY (id_court_2) REFERENCES gymnase (id)
        ON DELETE CASCADE
)
    ENGINE = InnoDB
    DEFAULT CHARSET = latin1;
