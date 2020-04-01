SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS blacklist_gymnase;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE IF NOT EXISTS blacklist_gymnase (
  id          SMALLINT(10) PRIMARY KEY NOT NULL AUTO_INCREMENT,
  id_gymnase  SMALLINT(10)             NOT NULL,
  closed_date DATETIME                 NOT NULL,
  FOREIGN KEY (id_gymnase) REFERENCES gymnase (id)
    ON DELETE CASCADE
)
  ENGINE = InnoDB
  DEFAULT CHARSET = latin1;
