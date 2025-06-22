-- DEV: reDONE 240303
-- PROD: reDONE 240303
CREATE OR REPLACE VIEW match_players_count_view AS
SELECT a.id_match,
       a.code_match,
       a.code_competition,
       SUM(a.count_dom)      AS count_dom,
       SUM(a.count_masc_dom) AS count_masc_dom,
       SUM(a.count_fem_dom)  AS count_fem_dom,
       SUM(a.count_ext)      AS count_ext,
       SUM(a.count_masc_ext) AS count_masc_ext,
       SUM(a.count_fem_ext)  AS count_fem_ext,
       SUM(a.count_renfort)  AS count_renfort,
       CASE
           WHEN SUM(a.count_dom) = 0 AND SUM(a.count_ext) = 0
               THEN 'fiches équipes non remplies'
           WHEN SUM(a.count_dom) = 0
               THEN 'fiche équipe à domicile non remplie'
           WHEN SUM(a.count_ext) = 0
               THEN 'fiche équipe à l\'extérieur non remplie'
           WHEN a.code_competition IN ('kh', 'kf', 'ut') AND SUM(a.count_fem_dom) < 2
               THEN 'pas assez de filles à domicile'
           WHEN a.code_competition IN ('kh', 'kf', 'ut') AND SUM(a.count_fem_ext) < 2
               THEN 'pas assez de filles à l\'extérieur'
           WHEN a.code_competition IN ('mo', 'ut') AND (SUM(a.count_masc_dom) = 0 OR SUM(a.count_fem_dom) = 0)
               THEN 'mixité obligatoire à domicile non respectée'
           WHEN a.code_competition IN ('mo', 'ut') AND (SUM(a.count_masc_ext) = 0 OR SUM(a.count_fem_ext) = 0)
               THEN 'mixité obligatoire à l\'extérieur non respectée'
           END               AS count_status
FROM ((SELECT m.id_match,
              m.code_match,
              m.code_competition,
              COUNT(DISTINCT CASE WHEN jed.id_equipe = m.id_equipe_dom THEN mp_dom.id_player END) AS count_dom,
              COUNT(DISTINCT CASE WHEN jed.id_equipe = m.id_equipe_dom THEN j_masc_dom.id END)    AS count_masc_dom,
              COUNT(DISTINCT CASE WHEN jed.id_equipe = m.id_equipe_dom THEN j_fem_dom.id END)     AS count_fem_dom,
              0                                                                                   AS count_ext,
              0                                                                                   AS count_masc_ext,
              0                                                                                   AS count_fem_ext,
              0                                                                                   AS count_renfort
       FROM matches m
                LEFT JOIN match_player mp_dom ON mp_dom.id_match = m.id_match
                LEFT JOIN joueur_equipe jed ON jed.id_joueur = mp_dom.id_player
                LEFT JOIN joueurs j_masc_dom ON jed.id_joueur = j_masc_dom.id AND j_masc_dom.sexe IN ('M')
                LEFT JOIN joueurs j_fem_dom ON jed.id_joueur = j_fem_dom.id AND j_fem_dom.sexe IN ('F')
       WHERE m.match_status = 'CONFIRMED'
       GROUP BY m.id_match, m.code_match, m.code_competition)
      UNION ALL
      (SELECT m.id_match,
              m.code_match,
              m.code_competition,
              0                                                                                   AS count_dom,
              0                                                                                   AS count_masc_dom,
              0                                                                                   AS count_fem_dom,
              COUNT(DISTINCT CASE WHEN jee.id_equipe = m.id_equipe_ext THEN mp_ext.id_player END) AS count_ext,
              COUNT(DISTINCT CASE WHEN jee.id_equipe = m.id_equipe_ext THEN j_masc_ext.id END)    AS count_masc_ext,
              COUNT(DISTINCT CASE WHEN jee.id_equipe = m.id_equipe_ext THEN j_fem_ext.id END)     AS count_fem_ext,
              0                                                                                   AS count_renfort
       FROM matches m
                LEFT JOIN match_player mp_ext ON mp_ext.id_match = m.id_match
                LEFT JOIN joueur_equipe jee ON jee.id_joueur = mp_ext.id_player
                LEFT JOIN joueurs j_masc_ext ON jee.id_joueur = j_masc_ext.id AND j_masc_ext.sexe IN ('M')
                LEFT JOIN joueurs j_fem_ext ON jee.id_joueur = j_fem_ext.id AND j_fem_ext.sexe IN ('F')
       WHERE m.match_status = 'CONFIRMED'
       GROUP BY m.id_match, m.code_match, m.code_competition)
      UNION ALL
      (SELECT m.id_match,
              m.code_match,
              m.code_competition,
              0                                    AS count_dom,
              0                                    AS count_masc_dom,
              0                                    AS count_fem_dom,
              0                                    AS count_ext,
              0                                    AS count_masc_ext,
              0                                    AS count_fem_ext,
              COUNT(DISTINCT mp_renfort.id_player) AS count_renfort
       FROM matches m
                LEFT JOIN match_player mp_renfort ON mp_renfort.id_match = m.id_match
       WHERE mp_renfort.id_player NOT IN
             (SELECT id_joueur FROM joueur_equipe WHERE id_equipe IN (m.id_equipe_dom, m.id_equipe_ext))
         AND m.match_status = 'CONFIRMED'
       GROUP BY m.id_match, m.code_match, m.code_competition)) a
GROUP BY a.id_match, a.code_match, a.code_competition
HAVING ((SUM(a.count_dom) + SUM(a.count_renfort)) >= IF(a.code_competition IN ('m', 'c', 'cf'), 5, 3)
    AND (SUM(a.count_ext) + SUM(a.count_renfort)) >= IF(a.code_competition IN ('m', 'c', 'cf'), 5, 3))
    OR count_status IS NOT NULL