-- DEV: DONE 250721
-- PROD: DONE 250727

-- table n-n users_teams
CREATE TABLE users_teams
(
    user_id smallint not null,
    team_id smallint not null,
    primary key (user_id, team_id),
    constraint fk_ut_u
        foreign key (user_id) references comptes_acces (id)
            on delete cascade,
    constraint fk_ut_t
        foreign key (team_id) references equipes (id_equipe)
            on delete cascade
);

INSERT INTO users_teams (user_id, team_id)
SELECT u.id,
       u.id_equipe
FROm comptes_acces u
         JOIN users_profiles up on u.id = up.user_id
         JOIN profiles p ON up.profile_id = p.id
WHERE p.name IN ('RESPONSABLE_EQUIPE');

-- table n-n users_clubs
CREATE TABLE users_clubs
(
    user_id smallint not null,
    club_id smallint not null,
    primary key (user_id, club_id),
    constraint fk_uc_u
        foreign key (user_id) references comptes_acces (id)
            on delete cascade,
    constraint fk_uc_c
        foreign key (club_id) references clubs (id)
            on delete cascade
);

-- suppression du champ obsolète
ALTER TABLE comptes_acces
    DROP COLUMN id_equipe;

-- cleanup des comptes
DELETE
FROM comptes_acces
WHERE id NOT IN (SELECT user_id FROM users_profiles);

CREATE OR REPLACE VIEW matchs_view AS
WITH computed_forfait AS (SELECT m.id_match,
                                 IF(m.set_1_dom = 25 AND m.set_1_ext = 0
                                        AND m.set_2_dom = 25 AND m.set_2_ext = 0
                                        AND m.set_3_dom = 25 AND m.set_3_ext = 0
                                        AND m.is_sign_match_dom AND m.is_sign_match_ext,
                                    1, 0)                                                      AS forfait_ext,
                                 IF(m.set_1_dom = 0 AND m.set_1_ext = 25
                                        AND m.set_2_dom = 0 AND m.set_2_ext = 25
                                        AND m.set_3_dom = 0 AND m.set_3_ext = 25
                                        AND m.is_sign_match_dom AND m.is_sign_match_ext, 1, 0) AS forfait_dom,
                                 IF((m.set_1_dom = 25 AND m.set_1_ext = 0 AND
                                     m.set_2_dom = 25 AND m.set_2_ext = 0 AND
                                     m.set_3_dom = 25 AND m.set_3_ext = 0
                                     AND m.is_sign_match_dom AND m.is_sign_match_ext) OR
                                    (m.set_1_dom = 0 AND m.set_1_ext = 25 AND
                                     m.set_2_dom = 0 AND m.set_2_ext = 25 AND
                                     m.set_3_dom = 0 AND m.set_3_ext = 25
                                        AND m.is_sign_match_dom AND m.is_sign_match_ext),
                                    1,
                                    0)                                                         AS is_forfait
                          FROM matches m),
     computed_score AS (SELECT m.id_match,
                               IF(m.set_1_dom >= 25 AND m.set_1_dom >= m.set_1_ext + 2, 1, 0) +
                               IF(m.set_2_dom >= 25 AND m.set_2_dom >= m.set_2_ext + 2, 1, 0) +
                               IF(m.set_3_dom >= 25 AND m.set_3_dom >= m.set_3_ext + 2, 1, 0) +
                               IF(m.set_4_dom >= 25 AND m.set_4_dom >= m.set_4_ext + 2, 1, 0) +
                               IF(m.set_5_dom >= 15 AND m.set_5_dom >= m.set_5_ext + 2, 1, 0) AS score_equipe_dom,
                               IF(m.set_1_ext >= 25 AND m.set_1_ext >= m.set_1_dom + 2, 1, 0) +
                               IF(m.set_2_ext >= 25 AND m.set_2_ext >= m.set_2_dom + 2, 1, 0) +
                               IF(m.set_3_ext >= 25 AND m.set_3_ext >= m.set_3_dom + 2, 1, 0) +
                               IF(m.set_4_ext >= 25 AND m.set_4_ext >= m.set_4_dom + 2, 1, 0) +
                               IF(m.set_5_ext >= 15 AND m.set_5_ext >= m.set_5_dom + 2, 1, 0) AS score_equipe_ext
                        FROM matches m)
SELECT m.id_match,
       cf.forfait_dom,
       cf.forfait_ext,
       cf.is_forfait,
       IF(cs.score_equipe_dom = 3 OR cs.score_equipe_ext = 3, 1, 0)              AS is_match_score_filled,
       IF(mpcv.id_match IS NOT NULL, 1, 0)                                       AS is_match_player_filled,
       mpcv.count_status                                                         AS count_status,
       IF(mpcv.id_match IS NULL
              AND cf.is_forfait = 0
              AND m.certif = 0, 1, 0)                                            AS is_match_player_requested,
       IF(m.id_match IN (SELECT id_match
                         FROM match_player
                                  JOIN players_view j2 on match_player.id_player = j2.id
                         WHERE (j2.est_actif = 0 OR
                                STR_TO_DATE(j2.date_homologation, '%d/%m/%Y') > m.date_reception
                             OR j2.date_homologation IS NULL
                             OR j2.num_licence IS NULL)) AND cf.is_forfait = 0
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
       cs.score_equipe_dom,
       cs.score_equipe_ext,
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
       IF(m.is_sign_team_ext = 1
              AND m.is_sign_team_dom = 1
              AND m.is_sign_match_ext = 1
              AND m.is_sign_match_dom = 1, 1, 0)                                 AS sheet_received,
       m.note,
       m.certif,
       m.report_status,
       (
           CASE
               WHEN (cs.score_equipe_dom + cs.score_equipe_ext > 0) THEN 0
               WHEN m.date_reception >= curdate() THEN 0
               WHEN curdate() >= DATE_ADD(m.date_reception, INTERVAL 10 DAY) THEN 2
               WHEN curdate() >= DATE_ADD(m.date_reception, INTERVAL 5 DAY) THEN 1
               END
           )                                                                     AS retard,
       m.match_status,
       m.is_sign_match_dom,
       m.is_sign_match_ext,
       m.is_sign_team_dom,
       m.is_sign_team_ext,
       jresp_dom.email                                                           AS email_dom,
       jresp_ext.email                                                           AS email_ext,
       m.referee,
       IF(s_dom.id IS NOT NULL, 1, 0)                                            AS is_survey_filled_dom,
       IF(s_ext.id IS NOT NULL, 1, 0)                                            AS is_survey_filled_ext,
       GROUP_CONCAT(DISTINCT com.email)                                          AS contact_com
FROM matches m
         JOIN computed_forfait cf ON m.id_match = cf.id_match
         JOIN computed_score cs ON m.id_match = cs.id_match
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
         LEFT JOIN match_players_count_view mpcv ON mpcv.id_match = m.id_match
         LEFT JOIN survey s_dom ON m.id_match = s_dom.id_match AND s_dom.user_id IN (SELECT ca.id
                                                                                     FROM comptes_acces ca
                                                                                              JOIN users_teams ut ON ca.id = ut.user_id
                                                                                     WHERE ut.team_id = m.id_equipe_dom)
         LEFT JOIN survey s_ext ON m.id_match = s_ext.id_match AND s_ext.user_id IN (SELECT ca.id
                                                                                     FROM comptes_acces ca
                                                                                              JOIN users_teams ut ON ca.id = ut.user_id
                                                                                     WHERE ut.team_id = m.id_equipe_ext)
         LEFT JOIN commission_division cd ON cd.division = CONCAT('d', m.division, m.code_competition)
         LEFT JOIN commission com ON cd.id_commission = com.id_commission
WHERE 1 = 1
GROUP BY m.id_match, code_competition, division, numero_journee, code_match
ORDER BY code_competition, division, numero_journee, code_match;

CREATE OR REPLACE view survey_view_raw AS
SELECT s.id,
       e_sondeuse.id_equipe    AS id_team_sondeuse,
       m.code_match,
       m.id_match,
       e_sondee.nom_equipe     AS equipe,
       c_sondee.nom            AS club,
       s.on_time,
       2                       AS coef_on_time,
       s.spirit,
       3                       AS coef_spirit,
       CASE
           WHEN m.referee = 'HOME' AND m.id_equipe_dom = e_sondeuse.id_equipe THEN 0
           WHEN m.referee = 'AWAY' AND m.id_equipe_ext = e_sondeuse.id_equipe THEN 0
           WHEN m.referee = 'BOTH' THEN 0
           ELSE s.referee END  AS referee,
       CASE
           WHEN m.referee = 'HOME' AND m.id_equipe_dom = e_sondeuse.id_equipe THEN 0
           WHEN m.referee = 'AWAY' AND m.id_equipe_ext = e_sondeuse.id_equipe THEN 0
           WHEN m.referee = 'BOTH' THEN 0
           ELSE 3 END          as coef_referee,
       CASE
           WHEN m.id_equipe_dom = e_sondeuse.id_equipe THEN 0
           ELSE s.catering END AS catering,
       CASE
           WHEN m.id_equipe_dom = e_sondeuse.id_equipe THEN 0
           ELSE 2 END          AS coef_catering,
       s.global,
       5                       as coef_global,
       c.penalite              AS nb_penalites
FROM survey s
         JOIN matches m on s.id_match = m.id_match
         JOIN comptes_acces ca on ca.id = s.user_id
         JOIN users_teams ut on ca.id = ut.user_id
         JOIN equipes e_sondeuse on ut.team_id = e_sondeuse.id_equipe
         JOIN equipes e_sondee
              on ((e_sondee.id_equipe IN (m.id_equipe_dom, m.id_equipe_ext) AND
                   e_sondeuse.id_equipe IN (m.id_equipe_dom, m.id_equipe_ext))
                  AND e_sondee.id_equipe != e_sondeuse.id_equipe)
         JOIN clubs c_sondee ON e_sondee.id_club = c_sondee.id
         JOIN classements c ON e_sondee.id_equipe = c.id_equipe AND c.code_competition = m.code_competition
WHERE s.on_time + s.spirit + s.referee + s.catering + s.global > 0
ORDER BY id;

CREATE OR REPLACE view survey_view AS
SELECT SUM(s1.on_time * s1.coef_on_time + s1.spirit * s1.coef_spirit + s1.referee * s1.coef_referee +
           s1.catering * s1.coef_catering +
           s1.global * s1.coef_global) /
       (s1.coef_on_time + s1.coef_spirit + s1.coef_referee + s1.coef_catering + s1.coef_global) AS note,
       COUNT(DISTINCT s1.code_match)                                                            AS nb_matchs,
       SUM(s1.on_time * s1.coef_on_time + s1.spirit * s1.coef_spirit + s1.referee * s1.coef_referee +
           s1.catering * s1.coef_catering +
           s1.global * s1.coef_global) /
       (s1.coef_on_time + s1.coef_spirit + s1.coef_referee + s1.coef_catering + s1.coef_global) /
       count(DISTINCT s1.code_match)                                                            AS moyenne,
       s1.club
FROM survey_view_raw s1
GROUP BY s1.club
ORDER BY moyenne desc;
