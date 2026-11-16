-- DEV: reDONE 250721
-- PROD: reDONE 250727
-- issue #350 : filtre sur scale_version (migration 2026/018)
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
         -- équipe qui a rempli le sondage (ufolep13volley#482, migration 2026/033)
         JOIN equipes e_sondeuse on e_sondeuse.id_equipe = s.id_equipe
                                AND e_sondeuse.id_equipe IN (m.id_equipe_dom, m.id_equipe_ext)
         JOIN equipes e_sondee
              on e_sondee.id_equipe = IF(s.id_equipe = m.id_equipe_dom, m.id_equipe_ext, m.id_equipe_dom)
         JOIN clubs c_sondee ON e_sondee.id_club = c_sondee.id
         JOIN classements c ON e_sondee.id_equipe = c.id_equipe AND c.code_competition = m.code_competition
-- Issue #350 : seule l'échelle courante (-- - = + ++, en -2..+2) compte. Un
-- sondage tout à `=` vaut 0 : l'ancien filtre « somme > 0 » l'aurait écarté.
WHERE s.scale_version = 2
  -- un sondage par équipe et par match : le dernier envoyé. Les envois
  -- répétés comptaient chacun dans la note de fair-play (#482).
  AND s.id = (SELECT MAX(s2.id) FROM survey s2 WHERE s2.id_match = s.id_match AND s2.id_equipe = s.id_equipe)
ORDER BY id;