UPDATE joueurs j SET j.prenom = CONCAT(UPPER(LEFT(j.prenom, 1)), LOWER(SUBSTRING(REPLACE(REPLACE(j.prenom, ' ', ''), '-', ''),2)));
UPDATE joueurs j SET j.nom = UPPER(REPLACE(REPLACE(j.nom, ' ', ''), '-', ''));