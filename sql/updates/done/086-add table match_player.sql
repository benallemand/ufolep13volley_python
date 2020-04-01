SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS match_player;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE IF NOT EXISTS match_player
(
    id        BIGINT(20) PRIMARY KEY NOT NULL AUTO_INCREMENT,
    id_match  BIGINT(20)             NOT NULL,
    id_player SMALLINT(10)           NOT NULL,
    FOREIGN KEY (id_match) REFERENCES matches (id_match)
        ON DELETE CASCADE,
    FOREIGN KEY (id_player) REFERENCES joueurs (id)
        ON DELETE CASCADE
)
    ENGINE = InnoDB
    DEFAULT CHARSET = latin1;
