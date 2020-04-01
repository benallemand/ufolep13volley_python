ALTER TABLE clubs
    ADD COLUMN affiliation_number varchar(200) DEFAULT NULL;
ALTER TABLE clubs
    ADD COLUMN nom_responsable varchar(200) DEFAULT NULL;
ALTER TABLE clubs
    ADD COLUMN prenom_responsable varchar(200) DEFAULT NULL;
ALTER TABLE clubs
    ADD COLUMN tel1_responsable varchar(200) DEFAULT NULL;
ALTER TABLE clubs
    ADD COLUMN tel2_responsable varchar(200) DEFAULT NULL;
ALTER TABLE clubs
    ADD COLUMN email_responsable varchar(200) DEFAULT NULL;

