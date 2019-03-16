SET FOREIGN_KEY_CHECKS = 0;
ALTER TABLE matches_files
  DROP FOREIGN KEY fk_matches_files_file;
ALTER TABLE matches_files
  ADD CONSTRAINT fk_matches_files_file FOREIGN KEY (id_file) REFERENCES files (id)
    ON DELETE CASCADE;
SET FOREIGN_KEY_CHECKS = 1;