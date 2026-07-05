-- Issue #249 : workflow d'inscription en 3 étapes (demande / validation / engagement).
-- Les demandes d'inscription portent désormais un statut explicite :
--   PENDING   -> demande déposée par le responsable de club, modifiable par lui
--   VALIDATED -> validée par l'admin, verrouillée pour le club, éligible à l'engagement
-- L'engagement reste l'étape set_up_season (attribution division/rang), qui ne
-- traitera plus que les inscriptions VALIDATED.

ALTER TABLE register
    ADD COLUMN status ENUM ('PENDING', 'VALIDATED') NOT NULL DEFAULT 'PENDING',
    ADD COLUMN validation_date DATETIME NULL;

-- les inscriptions déjà présentes ont été traitées par l'ancien flux : validées
UPDATE register
SET status          = 'VALIDATED',
    validation_date = creation_date;
