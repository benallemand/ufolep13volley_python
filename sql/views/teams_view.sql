-- DEV: DONE 251004
-- PROD: DONE 251004
CREATE OR REPLACE VIEW teams_view AS
SELECT e.code_competition,
       comp.libelle                                    AS libelle_competition,
       e.nom_equipe,
       CONCAT(e.nom_equipe, ' (', c.nom, ') - ',
              GROUP_CONCAT(DISTINCT CONCAT(comp.libelle, IFNULL(CONCAT('(', cl.division, ')'), '')) ORDER BY
                           comp.libelle))              AS team_full_name,
       e.id_club,
       c.nom                                           AS club,
       e.id_equipe,
       CONCAT(jresp.prenom, ' ', jresp.nom)            AS responsable,
       TO_BASE64(CONCAT(jresp.prenom, ' ', jresp.nom)) AS responsable_base64,
       jresp.telephone                                 AS telephone_1,
       TO_BASE64(jresp.telephone)                      AS telephone_1_base64,
       jsupp.telephone                                 AS telephone_2,
       TO_BASE64(jsupp.telephone)                      AS telephone_2_base64,
       jresp.email,
       TO_BASE64(jresp.email)                          AS email_base64,
       GROUP_CONCAT(DISTINCT CONCAT(CONCAT(g.ville, ' - ', g.nom, ' - ', g.adresse, ' - ', g.gps), ' (', cr.jour, ' à ',
                                    cr.heure, ')', IF(cr.has_time_constraint > 0, ' (CONTRAINTE HORAIRE FORTE)', ''))
                    SEPARATOR ', ')                    AS gymnasiums_list,
       e.web_site,
       e.id_photo,
       p.path_photo,
       e.is_cup_registered,
       IF(cl.id IS NULL, 0, 1)                         AS is_active_team
FROM equipes e
         LEFT JOIN classements cl ON cl.id_equipe = e.id_equipe
         LEFT JOIN photos p ON p.id = e.id_photo
         JOIN clubs c ON c.id = e.id_club
         JOIN competitions comp ON comp.code_competition = IFNULL(cl.code_competition, e.code_competition)
         LEFT JOIN joueur_equipe jeresp ON jeresp.id_equipe = e.id_equipe AND jeresp.is_leader + 0 > 0
         LEFT JOIN joueur_equipe jesupp ON jesupp.id_equipe = e.id_equipe AND jesupp.is_vice_leader + 0 > 0
         LEFT JOIN joueurs jresp ON jresp.id = jeresp.id_joueur
         LEFT JOIN joueurs jsupp ON jsupp.id = jesupp.id_joueur
         LEFT JOIN creneau cr ON cr.id_equipe = e.id_equipe
         LEFT JOIN gymnase g ON g.id = cr.id_gymnase
WHERE 1 = 1
GROUP BY id_equipe, nom_equipe
ORDER BY nom_equipe