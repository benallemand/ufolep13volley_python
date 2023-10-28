-- DEV: DONE 231028
-- PROD: DONE 231028
CREATE TABLE survey
(
    id       smallint(10) PRIMARY KEY AUTO_INCREMENT,
    user_id  smallint(10) NOT NULL,
    id_match bigint       NOT NULL,
    on_time  tinyint DEFAULT 0,
    spirit   tinyint DEFAULT 0,
    referee  tinyint DEFAULT 0,
    catering tinyint DEFAULT 0,
    global   tinyint DEFAULT 0,
    comment  TEXT    DEFAULT NULL,
    FOREIGN KEY (user_id) REFERENCES comptes_acces (id)
        ON DELETE CASCADE,
    FOREIGN KEY (id_match) REFERENCES matches (id_match)
        ON DELETE CASCADE
);