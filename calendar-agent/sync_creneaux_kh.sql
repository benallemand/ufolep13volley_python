-- ============================================================================
-- Script de synchronisation des créneaux KH depuis la table register
-- Exécuter AVANT la génération du calendrier KH
-- ============================================================================

-- 0. Vérification: équipes avec créneau incomplet (gymnase ou jour manquant)
-- Ces équipes ont au moins un champ rempli mais il manque gymnase ou jour
SELECT 
    r.new_team_name AS equipe,
    'Créneau 1' AS creneau,
    CASE WHEN r.id_court_1 IS NULL THEN 'MANQUANT' ELSE 'OK' END AS gymnase,
    CASE WHEN r.day_court_1 IS NULL OR r.day_court_1 = '' THEN 'MANQUANT' ELSE 'OK' END AS jour,
    CASE WHEN r.hour_court_1 IS NULL OR r.hour_court_1 = '' THEN '20:00 (défaut)' ELSE r.hour_court_1 END AS heure
FROM register r
WHERE r.id_competition = 18
AND (r.id_court_1 IS NOT NULL OR r.day_court_1 IS NOT NULL OR r.hour_court_1 IS NOT NULL)
AND (r.id_court_1 IS NULL OR r.day_court_1 IS NULL OR r.day_court_1 = '')

UNION ALL

SELECT 
    r.new_team_name AS equipe,
    'Créneau 2' AS creneau,
    CASE WHEN r.id_court_2 IS NULL THEN 'MANQUANT' ELSE 'OK' END AS gymnase,
    CASE WHEN r.day_court_2 IS NULL OR r.day_court_2 = '' THEN 'MANQUANT' ELSE 'OK' END AS jour,
    CASE WHEN r.hour_court_2 IS NULL OR r.hour_court_2 = '' THEN '20:00 (défaut)' ELSE r.hour_court_2 END AS heure
FROM register r
WHERE r.id_competition = 18
AND (r.id_court_2 IS NOT NULL OR r.day_court_2 IS NOT NULL OR r.hour_court_2 IS NOT NULL)
AND (r.id_court_2 IS NULL OR r.day_court_2 IS NULL OR r.day_court_2 = '');

-- Si la requête ci-dessus retourne des lignes, corriger les données avant de continuer!

-- 1. Supprimer les créneaux existants des équipes inscrites à KH
DELETE FROM creneau 
WHERE id_equipe IN (
    SELECT id_equipe FROM classements WHERE code_competition = 'kh'
);

-- 2. Insérer les créneaux depuis register (créneau 1)
-- Heure par défaut: 20:00 si non renseignée
INSERT INTO creneau (id_gymnase, jour, heure, id_equipe, usage_priority)
SELECT 
    r.id_court_1,
    r.day_court_1,
    COALESCE(NULLIF(r.hour_court_1, ''), '20:00'),
    c.id_equipe,
    1
FROM register r
JOIN classements c ON c.code_competition = 'kh'
JOIN equipes e ON e.id_equipe = c.id_equipe AND e.nom_equipe = r.new_team_name
WHERE r.id_competition = 18
AND r.id_court_1 IS NOT NULL
AND r.day_court_1 IS NOT NULL AND r.day_court_1 != '';

-- 3. Insérer les créneaux depuis register (créneau 2, si présent)
-- Heure par défaut: 20:00 si non renseignée
INSERT INTO creneau (id_gymnase, jour, heure, id_equipe, usage_priority)
SELECT 
    r.id_court_2,
    r.day_court_2,
    COALESCE(NULLIF(r.hour_court_2, ''), '20:00'),
    c.id_equipe,
    2
FROM register r
JOIN classements c ON c.code_competition = 'kh'
JOIN equipes e ON e.id_equipe = c.id_equipe AND e.nom_equipe = r.new_team_name
WHERE r.id_competition = 18
AND r.id_court_2 IS NOT NULL
AND r.day_court_2 IS NOT NULL AND r.day_court_2 != '';

-- 4. Vérification: afficher les créneaux créés
SELECT 
    e.nom_equipe,
    c.jour,
    c.heure,
    g.nom as gymnase,
    c.usage_priority
FROM creneau c
JOIN equipes e ON e.id_equipe = c.id_equipe
JOIN gymnase g ON g.id = c.id_gymnase
JOIN classements cl ON cl.id_equipe = c.id_equipe AND cl.code_competition = 'kh'
ORDER BY e.nom_equipe, c.usage_priority;
