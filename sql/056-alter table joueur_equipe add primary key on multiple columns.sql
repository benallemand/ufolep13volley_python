ALTER TABLE joueur_equipe DROP PRIMARY KEY;
ALTER TABLE joueur_equipe DROP COLUMN id;
ALTER TABLE joueur_equipe ADD PRIMARY KEY (id_joueur, id_equipe);
