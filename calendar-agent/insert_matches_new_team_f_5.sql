-- Fichier SQL généré automatiquement - NOUVELLE EQUIPE
-- Date de génération: 2026-02-07 10:41:37
-- Division: Division f 5
-- Nombre de matchs: 6
-- Supprime d'abord les éventuels matchs NOT_CONFIRMED de la nouvelle équipe
-- puis insère les nouveaux matchs

DELETE FROM matches
WHERE (id_equipe_dom = '721' OR id_equipe_ext = '721')
AND match_status = 'NOT_CONFIRMED';

INSERT INTO matches (
    code_match,
    code_competition,
    division,
    id_equipe_dom,
    id_equipe_ext,
    date_reception,
    match_status,
    id_gymnasium
) VALUES
('F_5_20260528_001', 'f', '5', '157', '721', '2026-05-28', 'NOT_CONFIRMED', '7'),
('F_5_20260504_002', 'f', '5', '466', '721', '2026-05-04', 'NOT_CONFIRMED', '10'),
('F_5_20260316_003', 'f', '5', '721', '637', '2026-03-16', 'NOT_CONFIRMED', '22'),
('F_5_20260403_004', 'f', '5', '721', '686', '2026-04-03', 'NOT_CONFIRMED', '22'),
('F_5_20260518_005', 'f', '5', '721', '688', '2026-05-18', 'NOT_CONFIRMED', '22'),
('F_5_20260430_006', 'f', '5', '720', '721', '2026-04-30', 'NOT_CONFIRMED', '5');
