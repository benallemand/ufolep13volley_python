-- DEV: DONE 250202
-- PROD: DONE 250202
CREATE OR REPLACE VIEW ranks_view AS
SELECT
    z.code_competition,
    z.division,
    RANK() OVER (PARTITION BY z.code_competition, z.division ORDER BY z.points DESC, z.diff DESC, z.rank_start) AS rang,
    z.id_equipe,
    z.equipe,
    z.points,
    z.joues,
    z.gagnes,
    z.perdus,
    z.sets_pour,
    z.sets_contre,
    z.diff,
    z.penalites,
    z.matches_lost_by_forfeit_count,
    z.report_count
FROM (
    SELECT
        c.code_competition,
        c.division,
        e.id_equipe,
        e.nom_equipe AS equipe,
        SUM(IF(e.id_equipe = m.id_equipe_dom AND m.score_equipe_dom = 3, 3, 0)) +
        SUM(IF(e.id_equipe = m.id_equipe_ext AND m.score_equipe_ext = 3, 3, 0)) +
        SUM(IF(e.id_equipe = m.id_equipe_dom AND m.score_equipe_ext = 3 AND m.forfait_dom = 0, 1, 0)) +
        SUM(IF(e.id_equipe = m.id_equipe_ext AND m.score_equipe_dom = 3 AND m.forfait_ext = 0, 1, 0)) - c.penalite AS points,
        SUM(IF(e.id_equipe = m.id_equipe_dom AND m.score_equipe_dom = 3, 1, 0)) +
        SUM(IF(e.id_equipe = m.id_equipe_ext AND m.score_equipe_ext = 3, 1, 0)) +
        SUM(IF(e.id_equipe = m.id_equipe_dom AND m.score_equipe_ext = 3, 1, 0)) +
        SUM(IF(e.id_equipe = m.id_equipe_ext AND m.score_equipe_dom = 3, 1, 0)) AS joues,
        SUM(IF(e.id_equipe = m.id_equipe_dom AND m.score_equipe_dom = 3, 1, 0)) +
        SUM(IF(e.id_equipe = m.id_equipe_ext AND m.score_equipe_ext = 3, 1, 0)) AS gagnes,
        SUM(IF(e.id_equipe = m.id_equipe_dom AND m.score_equipe_ext = 3, 1, 0)) +
        SUM(IF(e.id_equipe = m.id_equipe_ext AND m.score_equipe_dom = 3, 1, 0)) AS perdus,
        SUM(IF(e.id_equipe = m.id_equipe_dom, m.score_equipe_dom, m.score_equipe_ext)) AS sets_pour,
        SUM(IF(e.id_equipe = m.id_equipe_dom, m.score_equipe_ext, m.score_equipe_dom)) AS sets_contre,
        SUM(IF(e.id_equipe = m.id_equipe_dom, m.score_equipe_dom, m.score_equipe_ext)) -
        SUM(IF(e.id_equipe = m.id_equipe_dom, m.score_equipe_ext, m.score_equipe_dom)) AS diff,
        c.penalite AS penalites,
        SUM(IF(e.id_equipe = m.id_equipe_dom AND m.forfait_dom = 1, 1, 0)) +
        SUM(IF(e.id_equipe = m.id_equipe_ext AND m.forfait_ext = 1, 1, 0)) AS matches_lost_by_forfeit_count,
        c.report_count,
        c.rank_start
    FROM classements c
    JOIN equipes e ON e.id_equipe = c.id_equipe
    LEFT JOIN matchs_view m ON
        m.code_competition = c.code_competition
        AND m.division = c.division
        AND (m.id_equipe_dom = e.id_equipe OR m.id_equipe_ext = e.id_equipe)
        AND m.match_status != 'ARCHIVED'
    GROUP BY c.code_competition, c.division, e.id_equipe, e.nom_equipe, c.penalite, c.report_count, c.rank_start
) z;
