SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS files;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE IF NOT EXISTS files (
  id        SMALLINT(10) NOT NULL AUTO_INCREMENT,
  path_file VARCHAR(500) NOT NULL,
  PRIMARY KEY (id),
  KEY id (id)
)
  ENGINE = InnoDB
  DEFAULT CHARSET = latin1;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS matches_files;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE matches_files
(
  id_match SMALLINT(10) DEFAULT '0' NOT NULL,
  id_file  SMALLINT(10) DEFAULT '0' NOT NULL,
  CONSTRAINT `PRIMARY` PRIMARY KEY (id_match, id_file),
  CONSTRAINT fk_matches_files_match FOREIGN KEY (id_match) REFERENCES matches (id_match),
  CONSTRAINT fk_matches_files_file FOREIGN KEY (id_file) REFERENCES files (id)
)
  ENGINE = InnoDB
  DEFAULT CHARSET = latin1;
CREATE INDEX fk_matches_files_match
  ON matches_files (id_match);
