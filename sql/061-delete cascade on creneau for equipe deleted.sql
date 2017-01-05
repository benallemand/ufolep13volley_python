SET FOREIGN_KEY_CHECKS=0;
ALTER TABLE creneau
  DROP FOREIGN KEY fk_creneau_equipes;
ALTER TABLE creneau
  DROP INDEX fk_creneau_equipes;
ALTER TABLE creneau
  ADD CONSTRAINT fk_creneau_equipes FOREIGN KEY (id_equipe) REFERENCES equipes (id_equipe)
  ON DELETE CASCADE;
SET FOREIGN_KEY_CHECKS=1;