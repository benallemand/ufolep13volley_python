-- DEV: DONE 241116
-- PROD: DONE 241116
CREATE TABLE commission_division
(
    id            smallint(10) PRIMARY KEY AUTO_INCREMENT,
    id_commission smallint(10) NOT NULL,
    division      varchar(5) DEFAULT NULL,
    FOREIGN KEY (id_commission) REFERENCES commission (id_commission)
        ON DELETE CASCADE
);