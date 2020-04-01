SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS blacklist_team;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE IF NOT EXISTS blacklist_team
(
  id          SMALLINT(10) PRIMARY KEY NOT NULL AUTO_INCREMENT,
  id_team     SMALLINT(10)             NOT NULL,
  closed_date DATETIME                 NOT NULL,
  FOREIGN KEY (id_team) REFERENCES equipes (id_equipe)
    ON DELETE CASCADE
)
  ENGINE = InnoDB
  DEFAULT CHARSET = latin1;
