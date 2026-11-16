-- DEV: reDONE 250721
-- PROD: reDONE 250727
-- ufolep13volley#484 : chaque sondage est d'abord ramené à sa propre note
-- (somme pondérée / somme de SES coefficients), puis on fait la moyenne des
-- sondages. Avant, la somme pondérée de tous les sondages du club était divisée
-- par les coefficients d'une seule ligne, prise au hasard par le GROUP BY : or
-- l'arbitrage et l'apéro ne comptent pas pour l'équipe qui arbitre ou reçoit,
-- donc la moyenne changeait selon la ligne retenue et pouvait dépasser ++ (2).
-- Elle était aussi divisée par le nombre de matchs, et non de sondages.
CREATE OR REPLACE view survey_view AS
SELECT SUM(s1.note_sondage)          AS note,
       COUNT(DISTINCT s1.code_match) AS nb_matchs,
       AVG(s1.note_sondage)          AS moyenne,
       s1.club
FROM (SELECT r.club,
             r.code_match,
             (r.on_time * r.coef_on_time + r.spirit * r.coef_spirit + r.referee * r.coef_referee +
              r.catering * r.coef_catering + r.global * r.coef_global) /
             (r.coef_on_time + r.coef_spirit + r.coef_referee + r.coef_catering + r.coef_global) AS note_sondage
      FROM survey_view_raw r) s1
GROUP BY s1.club
ORDER BY moyenne desc;
