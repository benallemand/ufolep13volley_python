-- Issue #404 : numéros de licence saisis à la main tels qu'imprimés sur la
-- licence, avec le préfixe de département (`013_96769993`), ou avec des
-- espaces / tabulations. Un import ne les retrouve jamais par leur licence.
--
-- Depuis #404, `Players::save()` normalise la saisie. Cette reprise corrige
-- l'existant. Au 03/10/2026 sur le dump de prod : 2 joueurs.

-- 1. À regarder avant : ce qui va changer.
SELECT id, nom, prenom, departement_affiliation, num_licence,
       REGEXP_REPLACE(REGEXP_REPLACE(num_licence, '[[:space:]]', ''), '^0?[0-9]{2,3}_', '') AS corrige
FROM joueurs
WHERE num_licence REGEXP '[[:space:]]|^0?[0-9]{2,3}_';

-- 2. La correction.
UPDATE joueurs
SET num_licence = REGEXP_REPLACE(REGEXP_REPLACE(num_licence, '[[:space:]]', ''), '^0?[0-9]{2,3}_', '')
WHERE num_licence REGEXP '[[:space:]]|^0?[0-9]{2,3}_';
