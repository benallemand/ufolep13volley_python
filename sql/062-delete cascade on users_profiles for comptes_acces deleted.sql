SET FOREIGN_KEY_CHECKS = 0;
ALTER TABLE users_profiles
  DROP FOREIGN KEY fk_users_profiles_user;
ALTER TABLE users_profiles
  DROP INDEX fk_users_profiles_user;
ALTER TABLE users_profiles
  ADD CONSTRAINT fk_users_profiles_user FOREIGN KEY (user_id) REFERENCES comptes_acces (id)
  ON DELETE CASCADE;

SET FOREIGN_KEY_CHECKS = 1;