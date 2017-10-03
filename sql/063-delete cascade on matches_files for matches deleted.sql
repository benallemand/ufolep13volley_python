SET FOREIGN_KEY_CHECKS = 0;
ALTER TABLE matches_files
  DROP FOREIGN KEY fk_matches_files_match;
ALTER TABLE matches_files
  ADD CONSTRAINT fk_matches_files_match FOREIGN KEY (id_match) REFERENCES matches (id_match)
  ON DELETE CASCADE;

SET FOREIGN_KEY_CHECKS = 1;