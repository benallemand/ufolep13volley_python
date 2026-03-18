-- Fichier SQL généré automatiquement par le générateur UFOLEP
-- Date de génération: 2026-03-18 20:27:52
-- Compétition: kf
-- Nombre de matchs: 8
-- À exécuter dans phpMyAdmin

-- Suppression uniquement des matchs NOT_CONFIRMED
DELETE FROM matches 
WHERE code_competition IN ('kf')
AND match_status = 'NOT_CONFIRMED';

-- Insertion des nouveaux matchs
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
('KF_1_20260601_001', 'kf', '1', '705', '620', '2026-06-01', 'NOT_CONFIRMED', '40'),
('KF_1_20260605_002', 'kf', '1', '718', '604', '2026-06-05', 'NOT_CONFIRMED', '22'),
('KF_1_20260605_003', 'kf', '1', '606', '719', '2026-06-05', 'NOT_CONFIRMED', '16'),
('KF_1_20260601_004', 'kf', '1', '611', '613', '2026-06-01', 'NOT_CONFIRMED', '33'),
('KF_1_20260605_005', 'kf', '1', '625', '704', '2026-06-05', 'NOT_CONFIRMED', '36'),
('KF_1_20260605_006', 'kf', '1', '709', '619', '2026-06-05', 'NOT_CONFIRMED', '23'),
('KF_1_20260602_007', 'kf', '1', '670', '615', '2026-06-02', 'NOT_CONFIRMED', '18'),
('KF_1_20260605_008', 'kf', '1', '673', '706', '2026-06-05', 'NOT_CONFIRMED', '23');

-- Statistiques
-- Total matchs: 8
-- Division kf1: 8 matchs
