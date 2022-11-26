-- DEV: reDONE 221126
-- PROD: reDONE 221126
CREATE OR REPLACE VIEW players_view AS
SELECT CONCAT(UPPER(j.nom), ' ', j.prenom, ' (', IFNULL(j.num_licence, ''), ')') AS full_name,
       j.prenom,
       UPPER(j.nom)                                                              AS nom,
       j.telephone,
       j.email,
       j.num_licence,
       CONCAT(LPAD(j.departement_affiliation, 3, '0'), j.num_licence)            AS num_licence_ext,
       p.path_photo,
       j.sexe,
       j.departement_affiliation,
       CASE
           WHEN (j.date_homologation IS NULL) THEN 0
           WHEN (j.date_homologation > CURRENT_TIMESTAMP) THEN 0
           WHEN (j.num_licence IS NULL) THEN 0
           WHEN j.id NOT IN (SELECT id_joueur
                             FROM joueur_equipe
                             WHERE id_equipe IN (SELECT id_equipe
                                                 FROM classements))
               THEN 0
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
           ELSE 0
           END                                                                   AS est_actif,
       j.id_club,
       c.nom                                                                     AS club,
       j.telephone2,
       j.email2,
       j.est_responsable_club + 0                                                AS est_responsable_club,
       je.is_captain + 0                                                         AS is_captain,
       je.is_vice_leader + 0                                                     AS is_vice_leader,
       je.is_leader + 0                                                          AS is_leader,
       j.show_photo + 0                                                          AS show_photo,
       j.id,
       GROUP_CONCAT(DISTINCT concat(e.nom_equipe, ' (', comp.libelle, ')', ' (D', cl.division, ')') SEPARATOR
                    '<br/>')                                                     AS teams_list,
       GROUP_CONCAT(DISTINCT e2.nom_equipe SEPARATOR '<br/>')                    AS team_leader_list,
       DATE_FORMAT(j.date_homologation, '%d/%m/%Y')                              AS date_homologation
FROM joueurs j
         LEFT JOIN joueur_equipe je ON je.id_joueur = j.id
         LEFT JOIN joueur_equipe je2 ON je2.id_joueur = j.id AND je2.is_leader + 0 > 0
         LEFT JOIN equipes e ON e.id_equipe = je.id_equipe
         LEFT JOIN equipes e2 ON e2.id_equipe = je2.id_equipe
         LEFT JOIN clubs c ON c.id = j.id_club
         LEFT JOIN photos p ON p.id = j.id_photo
         LEFT JOIN classements cl ON cl.id_equipe = e.id_equipe
         LEFT JOIN competitions comp ON comp.code_competition = e.code_competition
         LEFT JOIN dates_limite dl ON dl.code_competition = comp.code_competition
WHERE 1 = 1
GROUP BY j.id, j.sexe, UPPER(j.nom)
ORDER BY j.sexe, UPPER(j.nom);