SET FOREIGN_KEY_CHECKS = 0;
ALTER TABLE joueur_equipe
  DROP FOREIGN KEY fk_joueur_equipe_joueur;
ALTER TABLE joueur_equipe
  DROP INDEX fk_joueur_equipe_joueur;
ALTER TABLE joueur_equipe
  ADD CONSTRAINT fk_joueur_equipe_joueur FOREIGN KEY (id_joueur) REFERENCES joueurs (id)
  ON DELETE CASCADE;
CREATE INDEX fk_joueur_equipe_joueur
  ON joueur_equipe (id_joueur);
SET FOREIGN_KEY_CHECKS = 1;