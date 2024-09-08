-- DEV: reDONE 240908
-- PROD: reDONE 240908
CREATE OR REPLACE VIEW matchs_view AS
SELECT m.id_match,
       IF(m.forfait_dom + m.forfait_ext > 0, 1, 0)                               AS is_forfait,
       IF(m.score_equipe_dom = 3 OR m.score_equipe_ext = 3, 1, 0)                AS is_match_score_filled,
       IF(mpcv.id_match IS NOT NULL, 1, 0)                                       AS is_match_player_filled,
       mpcv.count_status                                                         AS count_status,
       IF(mpcv.id_match IS NULL
              AND (m.forfait_dom + m.forfait_ext = 0)
              AND (m.certif = 0), 1, 0)                                          AS is_match_player_requested,
       IF(m.id_match IN (SELECT id_match
                         FROM match_player
                                  JOIN players_view j2 on match_player.id_player = j2.id
                         WHERE (j2.est_actif = 0 OR
                                STR_TO_DATE(j2.date_homologation, '%d/%m/%Y') > m.date_reception
                             OR j2.date_homologation IS NULL
                             OR j2.num_licence IS NULL))
           , 1,
          0)                                                                     AS has_forbidden_player,
       m.code_match,
       m.code_competition,
       c.id_compet_maitre                                                        AS parent_code_competition,
       c.libelle                                                                 AS libelle_competition,
       m.division,
       j.numero                                                                  AS numero_journee,
       j.id                                                                      AS id_journee,
       CONCAT(j.nommage,
              ' : ',
              'Semaine du ',
              DATE_FORMAT(j.start_date, '%W %d %M'),
              ' au ',
              DATE_FORMAT(ADDDATE(j.start_date, INTERVAL 4 DAY), '%W %d %M %Y')) AS journee,
       m.id_equipe_dom,
       e1.nom_equipe                                                             AS equipe_dom,
       m.id_equipe_ext,
       e2.nom_equipe                                                             AS equipe_ext,
       m.score_equipe_dom + 0                                                    AS score_equipe_dom,
       m.score_equipe_ext + 0                                                    AS score_equipe_ext,
       m.set_1_dom,
       m.set_1_ext,
       m.set_2_dom,
       m.set_2_ext,
       m.set_3_dom,
       m.set_3_ext,
       m.set_4_dom,
       m.set_4_ext,
       m.set_5_dom,
       m.set_5_ext,
       cr.heure                                                                  AS heure_reception,
       m.id_gymnasium,
       g.nom                                                                     AS gymnasium,
       DATE_FORMAT(m.date_reception, '%d/%m/%Y')                                 AS date_reception,
       UNIX_TIMESTAMP(m.date_reception + INTERVAL 23 HOUR + INTERVAL 59 MINUTE) *
       1000                                                                      AS date_reception_raw,
       DATE_FORMAT(m.date_original, '%d/%m/%Y')                                  AS date_original,
       UNIX_TIMESTAMP(m.date_original + INTERVAL 23 HOUR + INTERVAL 59 MINUTE) *
       1000                                                                      AS date_original_raw,
       m.forfait_dom                                                             AS forfait_dom,
       m.forfait_ext                                                             AS forfait_ext,
       CASE
           WHEN m.is_sign_team_ext = 1
               AND m.is_sign_team_dom = 1
               AND m.is_sign_match_ext = 1
               AND m.is_sign_match_dom = 1 THEN 1
           ELSE m.sheet_received END                                             AS sheet_received,
       m.note,
       m.certif                                                                  AS certif,
       m.report_status,
       (
           CASE
               WHEN (m.score_equipe_dom + m.score_equipe_ext > 0) THEN 0
               WHEN m.date_reception >= curdate() THEN 0
               WHEN curdate() >= DATE_ADD(m.date_reception, INTERVAL 10 DAY) THEN 2
               WHEN curdate() >= DATE_ADD(m.date_reception, INTERVAL 5 DAY) THEN 1
               END
           )                                                                     AS retard,
       IF(mf.id_file IS NOT NULL, 1, 0)                                          AS is_file_attached,
       m.match_status,
       GROUP_CONCAT(f.path_file SEPARATOR '|')                                   AS files_paths,
       m.is_sign_match_dom,
       m.is_sign_match_ext,
       m.is_sign_team_dom,
       m.is_sign_team_ext,
       jresp_dom.email                                                           AS email_dom,
       jresp_ext.email                                                           AS email_ext,
       m.referee,
       IF(s_dom.id IS NOT NULL, 1, 0)                                            AS is_survey_filled_dom,
       IF(s_ext.id IS NOT NULL, 1, 0)                                            AS is_survey_filled_ext
FROM matches m
         JOIN competitions c ON c.code_competition = m.code_competition
         JOIN equipes e1 ON e1.id_equipe = m.id_equipe_dom
         LEFT JOIN joueur_equipe jeresp_dom on jeresp_dom.id_equipe = e1.id_equipe AND jeresp_dom.is_leader = 1
         LEFT JOIN joueurs jresp_dom ON jeresp_dom.id_joueur = jresp_dom.id
         JOIN equipes e2 ON e2.id_equipe = m.id_equipe_ext
         LEFT JOIN joueur_equipe jeresp_ext on jeresp_ext.id_equipe = e2.id_equipe AND jeresp_ext.is_leader = 1
         LEFT JOIN joueurs jresp_ext ON jeresp_ext.id_joueur = jresp_ext.id
         LEFT JOIN journees j ON m.id_journee = j.id
         LEFT JOIN creneau cr ON cr.id_equipe = m.id_equipe_dom
    AND cr.jour = ELT(WEEKDAY(m.date_reception) + 2,
                      'Dimanche',
                      'Lundi',
                      'Mardi',
                      'Mercredi',
                      'Jeudi',
                      'Vendredi',
                      'Samedi')
    AND cr.id_gymnase = m.id_gymnasium
         LEFT JOIN gymnase g ON m.id_gymnasium = g.id
         LEFT JOIN matches_files mf ON mf.id_match = m.id_match
         LEFT JOIN files f on mf.id_file = f.id
         LEFT JOIN match_players_count_view mpcv ON mpcv.id_match = m.id_match
         LEFT JOIN survey s_dom ON m.id_match = s_dom.id_match AND s_dom.user_id IN (SELECT ca.id
                                                                                     FROM comptes_acces ca
                                                                                     WHERE ca.id_equipe = m.id_equipe_dom)
         LEFT JOIN survey s_ext ON m.id_match = s_ext.id_match AND s_ext.user_id IN (SELECT ca.id
                                                                                     FROM comptes_acces ca
                                                                                     WHERE ca.id_equipe = m.id_equipe_ext)
WHERE 1 = 1
GROUP BY code_competition, division, numero_journee, code_match
ORDER BY code_competition, division, numero_journee, code_match;