SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS emails;
DROP TABLE IF EXISTS emails_files;
SET FOREIGN_KEY_CHECKS = 1;

-- email to be sent
CREATE TABLE IF NOT EXISTS emails
(
    id             INT PRIMARY KEY                 NOT NULL AUTO_INCREMENT,
    from_email     TEXT                            NOT NULL,
    to_email       TEXT                            NOT NULL,
    cc             TEXT                            NOT NULL,
    bcc            TEXT                            NOT NULL,
    subject        TEXT                            NOT NULL,
    body           TEXT                            NOT NULL,
    creation_date  DATETIME                        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sent_date      DATETIME                                 DEFAULT NULL,
    sending_status ENUM ('TO_DO', 'DONE', 'ERROR') NOT NULL DEFAULT 'TO_DO'
)
    ENGINE = InnoDB
    DEFAULT CHARSET = latin1;

-- link 0..n file to email
CREATE TABLE emails_files
(
    id_email INT          NOT NULL,
    id_file  SMALLINT(10) NOT NULL,
    CONSTRAINT `PRIMARY` PRIMARY KEY (id_email, id_file),
    CONSTRAINT fk_emails_files_email FOREIGN KEY (id_email) REFERENCES emails (id),
    CONSTRAINT fk_emails_files_file FOREIGN KEY (id_file) REFERENCES files (id)
)
    ENGINE = InnoDB
    DEFAULT CHARSET = latin1;
CREATE INDEX fk_emails_files_email
    ON emails_files (id_email);