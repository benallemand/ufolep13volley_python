ALTER TABLE matches
  DROP COLUMN date_original;

ALTER TABLE matches
  ADD COLUMN date_original DATE DEFAULT NULL;

DROP TRIGGER IF EXISTS trg_bkp_orig_date;

DELIMITER $$
$$
CREATE TRIGGER trg_bkp_orig_date
BEFORE UPDATE ON matches
FOR EACH ROW
  BEGIN
    IF NEW.date_reception <> OLD.date_reception
    THEN
      SET NEW.date_original = OLD.date_reception;
    END IF;
  END
$$
DELIMITER ;