-- ============================================================================
-- Comparaison des créneaux: register vs table creneau (toutes compétitions)
-- Note: register contient les équipes via la compétition parente (id_compet_maitre)
--       ex: équipe en coupe 'c' -> register avec id_competition de 'm'
-- ============================================================================

-- 1. Créneaux dans REGISTER mais PAS dans CRENEAU (ou différents) - Créneau 1
SELECT comp_enfant.libelle AS competition,
       'REGISTER'          AS source,
       r.new_team_name     AS equipe,
       g1.nom              AS gymnase_register,
       r.day_court_1       AS jour_register,
       r.hour_court_1      AS heure_register,
       g2.nom              AS gymnase_creneau,
       cr.jour             AS jour_creneau,
       cr.heure            AS heure_creneau,
       CASE
           WHEN cr.id IS NULL THEN 'ABSENT dans creneau'
           WHEN r.id_court_1 != cr.id_gymnase THEN 'GYMNASE différent'
           WHEN r.day_court_1 != cr.jour THEN 'JOUR différent'
           WHEN COALESCE(r.hour_court_1, '20:00') != cr.heure THEN 'HEURE différente'
           ELSE 'OK'
           END             AS ecart
FROM register r
         JOIN competitions comp_parent ON comp_parent.id = r.id_competition
         JOIN competitions comp_enfant ON comp_enfant.id_compet_maitre = comp_parent.code_competition
         JOIN equipes e ON (r.old_team_id IS NOT NULL AND e.id_equipe = r.old_team_id) 
                        OR (r.old_team_id IS NULL AND e.nom_equipe = r.new_team_name)
         JOIN classements cl ON cl.id_equipe = e.id_equipe AND cl.code_competition = comp_enfant.code_competition
         LEFT JOIN gymnase g1 ON g1.id = r.id_court_1
         LEFT JOIN creneau cr ON cr.id_equipe = e.id_equipe AND cr.usage_priority = 1
         LEFT JOIN gymnase g2 ON g2.id = cr.id_gymnase
WHERE r.id_court_1 IS NOT NULL
  AND (
    cr.id IS NULL
        OR r.id_court_1 != cr.id_gymnase
        OR r.day_court_1 != cr.jour
        OR COALESCE(r.hour_court_1, '20:00') != cr.heure
    )

UNION ALL

-- Créneau 2
SELECT comp_enfant.libelle AS competition,
       'REGISTER'          AS source,
       r.new_team_name     AS equipe,
       g1.nom              AS gymnase_register,
       r.day_court_2       AS jour_register,
       r.hour_court_2      AS heure_register,
       g2.nom              AS gymnase_creneau,
       cr.jour             AS jour_creneau,
       cr.heure            AS heure_creneau,
       CASE
           WHEN cr.id IS NULL THEN 'ABSENT dans creneau'
           WHEN r.id_court_2 != cr.id_gymnase THEN 'GYMNASE différent'
           WHEN r.day_court_2 != cr.jour THEN 'JOUR différent'
           WHEN COALESCE(r.hour_court_2, '20:00') != cr.heure THEN 'HEURE différente'
           ELSE 'OK'
           END             AS ecart
FROM register r
         JOIN competitions comp_parent ON comp_parent.id = r.id_competition
         JOIN competitions comp_enfant ON comp_enfant.id_compet_maitre = comp_parent.code_competition
         JOIN equipes e ON (r.old_team_id IS NOT NULL AND e.id_equipe = r.old_team_id) 
                        OR (r.old_team_id IS NULL AND e.nom_equipe = r.new_team_name)
         JOIN classements cl ON cl.id_equipe = e.id_equipe AND cl.code_competition = comp_enfant.code_competition
         LEFT JOIN gymnase g1 ON g1.id = r.id_court_2
         LEFT JOIN creneau cr ON cr.id_equipe = e.id_equipe AND cr.usage_priority = 2
         LEFT JOIN gymnase g2 ON g2.id = cr.id_gymnase
WHERE r.id_court_2 IS NOT NULL
  AND (
    cr.id IS NULL
        OR r.id_court_2 != cr.id_gymnase
        OR r.day_court_2 != cr.jour
        OR COALESCE(r.hour_court_2, '20:00') != cr.heure
    )

UNION ALL

-- 2. Créneaux dans CRENEAU mais PAS dans REGISTER (équipes engagées uniquement)
SELECT COALESCE(comp_enfant.libelle, cl.code_competition) AS competition,
       'CRENEAU'                                          AS source,
       e.nom_equipe                                       AS equipe,
       NULL                                               AS gymnase_register,
       NULL                                               AS jour_register,
       NULL                                               AS heure_register,
       g.nom                                              AS gymnase_creneau,
       cr.jour                                            AS jour_creneau,
       cr.heure                                           AS heure_creneau,
       'ABSENT dans register'                             AS ecart
FROM creneau cr
         JOIN equipes e ON e.id_equipe = cr.id_equipe
         JOIN classements cl ON cl.id_equipe = e.id_equipe
         JOIN gymnase g ON g.id = cr.id_gymnase
         LEFT JOIN competitions comp_enfant ON comp_enfant.code_competition = cl.code_competition
         LEFT JOIN competitions comp_parent ON comp_parent.code_competition = comp_enfant.id_compet_maitre
         LEFT JOIN register r ON r.id_competition = comp_parent.id 
                              AND ((r.old_team_id IS NOT NULL AND r.old_team_id = e.id_equipe) 
                                OR (r.old_team_id IS NULL AND r.new_team_name = e.nom_equipe))
WHERE r.id IS NULL

ORDER BY competition, equipe, source;
