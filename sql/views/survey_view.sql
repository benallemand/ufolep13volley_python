-- DEV: reDONE 250721
-- PROD: reDONE 250727
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
