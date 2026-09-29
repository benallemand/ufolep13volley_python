-- Issue #350 : le sondage fair-play passe de 0..10 étoiles à -- - = + ++.
--
-- La nouvelle échelle est stockée en -2..+2 dans les mêmes colonnes (tinyint
-- signé). Pour ne jamais mélanger les deux échelles dans les moyennes, chaque
-- sondage porte sa version :
--   1 = 0..10 étoiles, 0 = « non noté » — tous les sondages existants ;
--   2 = -2..+2, 0 = « = » (conforme) — les nouveaux.
--
-- Le défaut à 1 pendant l'ajout marque l'existant ; il passe ensuite à 2, pour
-- qu'un INSERT qui oublierait la colonne tombe dans l'échelle courante.
--
-- Ordre imposé : `survey_view_raw` lit la colonne, elle doit exister avant que
-- la vue ne soit recréée.

-- 1. la colonne
ALTER TABLE survey
    ADD COLUMN scale_version TINYINT NOT NULL DEFAULT 1 AFTER global;

ALTER TABLE survey
    ALTER COLUMN scale_version SET DEFAULT 2;

-- 2. survey_view_raw ne retient plus que l'échelle courante, et ne filtre plus
--    sur « somme des notes > 0 » (un sondage tout à `=` vaut 0 et doit
--    compter) : rejouer sql/views/survey_view_raw.sql.

-- 3. côté dépôt applicatif, regénérer le schéma de CI :
--    pwsh .github/ci/dump-schema.ps1
