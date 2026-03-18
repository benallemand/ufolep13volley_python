-- Fichier SQL généré automatiquement par le générateur UFOLEP
-- Date de génération: 2026-03-18 20:27:52
-- Compétition: cf
-- Nombre de matchs: 8
-- À exécuter dans phpMyAdmin

-- Suppression uniquement des matchs NOT_CONFIRMED
DELETE FROM matches 
WHERE code_competition IN ('cf')
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
('CF_1_20260601_001', 'cf', '1', '467', '159', '2026-06-01', 'NOT_CONFIRMED', '23'),
('CF_1_20260603_002', 'cf', '1', '642', '45', '2026-06-03', 'NOT_CONFIRMED', '71'),
('CF_1_20260602_003', 'cf', '1', '532', '4', '2026-06-02', 'NOT_CONFIRMED', '67'),
('CF_1_20260604_004', 'cf', '1', '156', '20', '2026-06-04', 'NOT_CONFIRMED', '7'),
('CF_1_20260601_005', 'cf', '1', '644', '1', '2026-06-01', 'NOT_CONFIRMED', '10'),
('CF_1_20260603_006', 'cf', '1', '640', '75', '2026-06-03', 'NOT_CONFIRMED', '72'),
('CF_1_20260605_007', 'cf', '1', '78', '694', '2026-06-05', 'NOT_CONFIRMED', '2'),
('CF_1_20260602_008', 'cf', '1', '32', '54', '2026-06-02', 'NOT_CONFIRMED', '18');

-- Statistiques
-- Total matchs: 8
-- Division cf1: 8 matchs
