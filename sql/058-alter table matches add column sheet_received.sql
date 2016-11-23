ALTER TABLE matches
  ADD COLUMN sheet_received TINYINT(1) NOT NULL DEFAULT '0';

UPDATE matches
SET sheet_received = 1
WHERE certif = 1;
