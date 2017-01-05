SET FOREIGN_KEY_CHECKS=0;
ALTER TABLE creneau
  DROP FOREIGN KEY fk_creneau_equipes;
ALTER TABLE creneau
  DROP INDEX fk_creneau_equipes;
ALTER TABLE creneau
  ADD CONSTRAINT fk_creneau_equipes FOREIGN KEY (id_equipe) REFERENCES equipes (id_equipe)
  ON DELETE CASCADE;

ALTER TABLE joueur_equipe
  DROP FOREIGN KEY fk_joueur_equipe_equipe;
ALTER TABLE joueur_equipe
  DROP INDEX fk_joueur_equipe_equipe;
ALTER TABLE joueur_equipe
  ADD CONSTRAINT fk_joueur_equipe_equipe FOREIGN KEY (id_equipe) REFERENCES equipes (id_equipe)
  ON DELETE CASCADE;


SET FOREIGN_KEY_CHECKS=1;