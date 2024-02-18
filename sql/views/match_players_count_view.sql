-- DEV: DONE 240218
-- PROD: DONE 240218
CREATE OR REPLACE VIEW match_players_count_view AS
SELECT a.id_match,
       a.code_competition,
       SUM(a.count_dom)      AS count_dom,
       SUM(a.count_masc_dom) AS count_masc_dom,
       SUM(a.count_fem_dom)  AS count_fem_dom,
       SUM(a.count_ext)      AS count_ext,
       SUM(a.count_masc_ext) AS count_masc_ext,
       SUM(a.count_fem_ext)  AS count_fem_ext,
       CASE
           WHEN a.code_competition IN ('kh', 'kf', 'ut') AND SUM(a.count_fem_dom) < 2
               THEN 'pas assez de filles à domicile'
           WHEN a.code_competition IN ('kh', 'kf', 'ut') AND SUM(a.count_fem_ext) < 2
               THEN 'pas assez de filles à l\'extérieur'
           WHEN a.code_competition IN ('mo', 'ut') AND (SUM(a.count_masc_dom) = 0 OR SUM(a.count_fem_dom) = 0)
               THEN 'mixité obligatoire à domicile non respectée'
           WHEN a.code_competition IN ('mo', 'ut') AND (SUM(a.count_masc_ext) = 0 OR SUM(a.count_fem_ext) = 0)
               THEN 'mixité obligatoire à l\'extérieur non respectée'
           END               AS count_status
FROM ((select m.id_match,
              m.code_competition,
              COUNT(DISTINCT mp.id_player) AS count_dom,
              COUNT(DISTINCT j_masc.id)    AS count_masc_dom,
              COUNT(DISTINCT j_fem.id)     AS count_fem_dom,
              0                            AS count_ext,
              0                            AS count_masc_ext,
              0                            AS count_fem_ext
       FROM match_player mp
                JOIN matches m on mp.id_match = m.id_match
                JOIN joueur_equipe jed
                     on jed.id_equipe = m.id_equipe_dom and jed.id_joueur = mp.id_player
                LEFT JOIN joueurs j_masc ON jed.id_joueur = j_masc.id AND j_masc.sexe IN ('M')
                LEFT JOIN joueurs j_fem ON jed.id_joueur = j_fem.id AND j_fem.sexe IN ('F')
       WHERE m.match_status = 'CONFIRMED'
       GROUP BY m.id_match, m.code_competition)
      UNION ALL
      (select m.id_match,
              m.code_competition,
              0                            AS count_dom,
              0                            AS count_masc_dom,
              0                            AS count_fem_dom,
              COUNT(DISTINCT mp.id_player) AS count_ext,
              COUNT(DISTINCT j_masc.id)    AS count_masc_ext,
              COUNT(DISTINCT j_fem.id)     AS count_fem_ext
       FROM match_player mp
                JOIN matches m on mp.id_match = m.id_match
                JOIN joueur_equipe jee
                     on jee.id_equipe = m.id_equipe_ext and jee.id_joueur = mp.id_player
                LEFT JOIN joueurs j_masc ON jee.id_joueur = j_masc.id AND j_masc.sexe IN ('M')
                LEFT JOIN joueurs j_fem ON jee.id_joueur = j_fem.id AND j_fem.sexe IN ('F')
       WHERE m.match_status = 'CONFIRMED'
       GROUP BY m.id_match, m.code_competition)) a
GROUP BY a.id_match, a.code_competition
HAVING SUM(a.count_dom) >= IF(a.code_competition IN ('m', 'c', 'cf'), 5, 3)
   AND SUM(a.count_ext) >= IF(a.code_competition IN ('m', 'c', 'cf'), 5, 3)