-- DEV: reDONE 241105
-- PROD: reDONE 241105
CREATE OR REPLACE VIEW players_view AS
SELECT CONCAT(UPPER(j.nom), ' ', j.prenom, ' (', IFNULL(j.num_licence, ''), ')')        AS full_name,
       j.prenom,
       UPPER(j.nom)                                                                     AS nom,
       j.telephone,
       j.email,
       j.num_licence,
       CONCAT(LPAD(j.departement_affiliation, 3, '0'), j.num_licence)                   AS num_licence_ext,
       p.path_photo,
       REPLACE(p.path_photo, 'players_pics', 'players_pics_low')                        AS path_photo_low,
       j.sexe,
       j.departement_affiliation,
       CASE
           WHEN (j.date_homologation IS NULL) THEN 0
           WHEN (j.date_homologation > CURRENT_TIMESTAMP) THEN 0
           WHEN (j.num_licence IS NULL) THEN 0
           -- si la compet est en 1ere 1/2 saison (commence en 2022 finit en 2023)
           WHEN MONTH(comp.start_date) > 7 THEN
               CASE
                   -- si homologué la même année
                   WHEN YEAR(j.date_homologation) = YEAR(comp.start_date)
                       -- licence aout+
                       AND MONTH(j.date_homologation) > 7 THEN 1
                   -- si homologué l'année suivante
                   WHEN YEAR(j.date_homologation) = YEAR(comp.start_date) + 1
                       THEN 1
                   ELSE 0
                   END
           -- si la compet est en 2e 1/2 saison (commence et finit en 2023)
           WHEN MONTH(comp.start_date) <= 7 THEN
               CASE
                   -- si homologué l'année précédente
                   WHEN YEAR(j.date_homologation) = YEAR(comp.start_date) - 1
                       -- licence aout+
                       AND MONTH(j.date_homologation) > 7
                       THEN 1
                   -- si homologué la même année
                   WHEN YEAR(j.date_homologation) = YEAR(comp.start_date)
                       THEN 1
                   ELSE 0
                   END
           -- si dans aucune équipe
           WHEN je.id_joueur IS NULL THEN
               CASE
                   -- si la compet est en 1ere 1/2 saison (commence en 2022 finit en 2023)
                   WHEN MONTH(min_comp.start_date) > 7 THEN
                       CASE
                           -- si homologué la même année
                           WHEN YEAR(j.date_homologation) = YEAR(min_comp.start_date)
                               -- licence aout+
                               AND MONTH(j.date_homologation) > 7 THEN 1
                           -- si homologué l'année suivante
                           WHEN YEAR(j.date_homologation) = YEAR(min_comp.start_date) + 1
                               THEN 1
                           ELSE 0
                           END
                   -- si la compet est en 2e 1/2 saison (commence et finit en 2023)
                   WHEN MONTH(min_comp.start_date) <= 7 THEN
                       CASE
                           -- si homologué l'année précédente
                           WHEN YEAR(j.date_homologation) = YEAR(min_comp.start_date) - 1
                               -- licence aout+
                               AND MONTH(j.date_homologation) > 7
                               THEN 1
                           -- si homologué la même année
                           WHEN YEAR(j.date_homologation) = YEAR(min_comp.start_date)
                               THEN 1
                           ELSE 0
                           END
                   END
           ELSE 0
           END                                                                          AS est_actif,
       j.id_club,
       c.nom                                                                            AS club,
       j.telephone2,
       j.email2,
       j.est_responsable_club + 0                                                       AS est_responsable_club,
       IF(j.id IN (SELECT id_joueur FROM joueur_equipe WHERE is_captain = 1), 1, 0)     AS is_captain,
       IF(j.id IN (SELECT id_joueur FROM joueur_equipe WHERE is_vice_leader = 1), 1, 0) AS is_vice_leader,
       IF(j.id IN (SELECT id_joueur FROM joueur_equipe WHERE is_leader = 1), 1, 0)      AS is_leader,
       GROUP_CONCAT(DISTINCT je_cap.id_equipe SEPARATOR ',')                            AS id_captain,
       GROUP_CONCAT(DISTINCT je_vl.id_equipe SEPARATOR ',')                             AS id_vl,
       GROUP_CONCAT(DISTINCT je_l.id_equipe SEPARATOR ',')                              AS id_l,
       j.show_photo + 0                                                                 AS show_photo,
       j.id,
       GROUP_CONCAT(DISTINCT
                    CASE WHEN cl.id IS NOT NULL THEN concat(e.nom_equipe, ' (', comp.libelle, ')') END
                    SEPARATOR '<br/>'
       )                                                                                AS active_teams_list,
       GROUP_CONCAT(DISTINCT
                    CASE WHEN cl.id IS NULL THEN concat(e.nom_equipe, ' (', comp.libelle, ')') END
                    SEPARATOR '<br/>'
       )                                                                                AS inactive_teams_list,
       GROUP_CONCAT(DISTINCT concat(e.nom_equipe, ' (', comp.libelle, ')')
                    SEPARATOR
                    '<br/>')                                                            AS teams_list,
       GROUP_CONCAT(DISTINCT e_l.nom_equipe SEPARATOR '<br/>')                          AS team_leader_list,
       DATE_FORMAT(j.date_homologation, '%d/%m/%Y')                                     AS date_homologation
FROM joueurs j
         LEFT JOIN joueur_equipe je_cap ON je_cap.id_joueur = j.id AND je_cap.is_captain = 1
         LEFT JOIN joueur_equipe je_vl ON je_vl.id_joueur = j.id AND je_vl.is_vice_leader = 1
         LEFT JOIN joueur_equipe je_l ON je_l.id_joueur = j.id AND je_l.is_leader = 1
         LEFT JOIN joueur_equipe je ON je.id_joueur = j.id
         LEFT JOIN equipes e ON e.id_equipe = je.id_equipe
         LEFT JOIN equipes e_l ON e_l.id_equipe = je_l.id_equipe
         LEFT JOIN clubs c ON c.id = j.id_club
         LEFT JOIN photos p ON p.id = j.id_photo
         LEFT JOIN classements cl ON cl.id_equipe = e.id_equipe
         LEFT JOIN competitions comp ON comp.code_competition = e.code_competition
         JOIN competitions min_comp ON min_comp.start_date = (SELECT MIN(start_date) FROM competitions)
WHERE 1 = 1
GROUP BY j.id, j.sexe, UPPER(j.nom)
ORDER BY j.sexe, UPPER(j.nom);