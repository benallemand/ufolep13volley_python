-- DEV: reDONE 250721
-- PROD: reDONE 250727
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