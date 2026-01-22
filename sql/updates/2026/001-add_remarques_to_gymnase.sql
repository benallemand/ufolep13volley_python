-- Issue #175: Ajouter un champ "remarques" pour les gymnases
-- Permet de stocker des informations pratiques (ex: code portillon)

-- DEV: DONE 260122
-- PROD: DONE 260122

ALTER TABLE gymnase 
ADD COLUMN remarques TEXT NULL 
AFTER nb_terrain;
