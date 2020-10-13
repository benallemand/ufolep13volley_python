SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS blacklist_by_city;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE IF NOT EXISTS blacklist_by_city
(
    id        SMALLINT(10) PRIMARY KEY NOT NULL AUTO_INCREMENT,
    city      varchar(200)             NOT NULL,
    from_date DATETIME                 NOT NULL,
    to_date   DATETIME                 NOT NULL
)
    ENGINE = InnoDB
    DEFAULT CHARSET = latin1;
