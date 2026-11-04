-- Issue #452 : champs texte saisis avec des blancs de début et de fin
-- (espaces, tabulations, retours à la ligne, espace insécable, BOM), souvent
-- copiés depuis un tableur. Une tabulation devant le nom de 7 joueurs
-- d'Eguilles a fait créer un doublon de chacun à l'import de sa licence.
--
-- Depuis #452, `rest/action.php` nettoie toute saisie. Cette reprise corrige
-- l'existant, sur les colonnes saisies par les utilisateurs. Les colonnes
-- générées (`emails.body`, `activity.comment`) ne sont pas touchées.
-- Au 04/11/2026 sur le dump de prod : 150 valeurs.

-- Le client mysql de l'hébergement (MariaDB) ouvre la session en
-- utf8mb4_general_ci : @blancs et les colonnes (0900_ai_ci) ne se
-- comparaient pas (« Illegal mix of collations »).
SET NAMES utf8mb4 COLLATE utf8mb4_0900_ai_ci;

SET @blancs = '^[\\s\\p{Z}\\x{FEFF}\\x{200B}]+|[\\s\\p{Z}\\x{FEFF}\\x{200B}]+$';

-- 1. À regarder avant : les joueurs dont le nom ou le prénom va changer.
SELECT id, CONCAT('[', nom, ']') AS nom, CONCAT('[', prenom, ']') AS prenom
FROM joueurs
WHERE nom REGEXP @blancs OR prenom REGEXP @blancs;

-- 2. La correction.
UPDATE joueurs
SET nom         = REGEXP_REPLACE(nom, @blancs, ''),
    prenom      = REGEXP_REPLACE(prenom, @blancs, ''),
    num_licence = REGEXP_REPLACE(num_licence, @blancs, ''),
    telephone   = REGEXP_REPLACE(telephone, @blancs, ''),
    telephone2  = REGEXP_REPLACE(telephone2, @blancs, ''),
    email       = REGEXP_REPLACE(email, @blancs, ''),
    email2      = REGEXP_REPLACE(email2, @blancs, '')
WHERE nom REGEXP @blancs OR prenom REGEXP @blancs OR num_licence REGEXP @blancs
   OR telephone REGEXP @blancs OR telephone2 REGEXP @blancs
   OR email REGEXP @blancs OR email2 REGEXP @blancs;

UPDATE matches SET note = REGEXP_REPLACE(note, @blancs, '') WHERE note REGEXP @blancs;

UPDATE survey SET comment = REGEXP_REPLACE(comment, @blancs, '') WHERE comment REGEXP @blancs;

UPDATE hall_of_fame SET team_name = REGEXP_REPLACE(team_name, @blancs, '') WHERE team_name REGEXP @blancs;

UPDATE gymnase
SET nom       = REGEXP_REPLACE(nom, @blancs, ''),
    adresse   = REGEXP_REPLACE(adresse, @blancs, ''),
    ville     = REGEXP_REPLACE(ville, @blancs, ''),
    gps       = REGEXP_REPLACE(gps, @blancs, ''),
    remarques = REGEXP_REPLACE(remarques, @blancs, '')
WHERE nom REGEXP @blancs OR adresse REGEXP @blancs OR ville REGEXP @blancs
   OR gps REGEXP @blancs OR remarques REGEXP @blancs;
