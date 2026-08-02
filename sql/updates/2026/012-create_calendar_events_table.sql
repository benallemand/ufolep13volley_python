-- =============================================================================
-- Issue #253 — Calendrier de la home : evenements en base
--
-- A jouer sur la base ufolep_13volley.
-- Les evenements etaient codes en dur dans pages/components/panel/Home.js
-- (tableau eventsBySeason) ; ils sont repris ici a l'identique.
--
-- date_end NULL = evenement ponctuel (affiche comme un point dans le
-- calendrier) ; sinon periode.
-- Une heure a 00:00:00 sur un evenement ponctuel signifie "toute la journee" :
-- l'API n'emet alors pas d'heure, pour ne pas afficher "a 00:00" sur les feries.
-- =============================================================================

CREATE TABLE IF NOT EXISTS `calendar_events` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `season` VARCHAR(9) NOT NULL COMMENT 'ex. 2026-2027',
  `label` VARCHAR(100) NOT NULL,
  `date_start` DATETIME NOT NULL,
  `date_end` DATETIME DEFAULT NULL COMMENT 'NULL = evenement ponctuel',
  PRIMARY KEY (`id`),
  KEY `idx_calendar_events_season` (`season`, `date_start`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `calendar_events` (`season`, `label`, `date_start`, `date_end`) VALUES
  ('2025-2026', 'Réunion calendrier', '2025-09-03 19:30:00', NULL),
  ('2025-2026', 'Inscriptions championnats', '2025-09-03 23:59:00', '2025-10-03 23:59:00'),
  ('2025-2026', 'Inscriptions coupe 4x4 Khoury Hanna', '2025-09-03 23:59:00', '2025-11-28 23:59:00'),
  ('2025-2026', 'Réunion début de saison', '2025-10-06 19:30:00', NULL),
  ('2025-2026', 'Tournoi(s) de bienvenue', '2025-10-09 00:00:00', '2025-10-13 23:59:00'),
  ('2025-2026', 'Championnats', '2025-11-03 00:00:00', '2025-12-19 23:59:00'),
  ('2025-2026', 'Vacances', '2025-12-20 00:00:00', '2026-01-04 23:59:00'),
  ('2025-2026', 'Reports', '2026-01-05 00:00:00', '2026-01-09 23:59:00'),
  ('2025-2026', 'Tirage des coupes', '2026-01-07 19:30:00', NULL),
  ('2025-2026', 'Réunion fin de demi-saison', '2026-01-12 19:30:00', NULL),
  ('2025-2026', 'Coupes', '2026-01-19 00:00:00', '2026-02-13 23:59:00'),
  ('2025-2026', 'Vacances', '2026-02-14 00:00:00', '2026-02-27 23:59:00'),
  ('2025-2026', 'Championnats', '2026-03-02 00:00:00', '2026-04-10 23:59:00'),
  ('2025-2026', 'Vacances', '2026-04-11 00:00:00', '2026-04-26 23:59:00'),
  ('2025-2026', 'Championnats', '2026-04-27 00:00:00', '2026-05-29 23:59:00'),
  ('2025-2026', 'Réunion fin de saison', '2026-06-16 19:30:00', NULL),
  ('2025-2026', 'Phases finales Coupes', '2026-06-01 00:00:00', '2026-06-19 23:59:00'),
  ('2025-2026', 'Finales + récompenses à Marignane', '2026-06-26 19:30:00', NULL),
  ('2026-2027', 'Réunion calendrier', '2026-09-02 19:30:00', NULL),
  ('2026-2027', 'Inscriptions championnats', '2026-09-02 23:59:00', '2026-10-02 23:59:00'),
  ('2026-2027', 'Inscriptions coupe 4x4 Khoury Hanna', '2026-09-02 23:59:00', '2026-11-27 23:59:00'),
  ('2026-2027', 'Réunion début de saison', '2026-10-05 19:30:00', NULL),
  ('2026-2027', 'Tournoi(s) de bienvenue', '2026-10-08 00:00:00', '2026-10-12 23:59:00'),
  ('2026-2027', 'Championnats', '2026-11-02 00:00:00', '2026-12-18 23:59:00'),
  ('2026-2027', 'Férié / pont', '2026-11-11 00:00:00', NULL),
  ('2026-2027', 'Vacances', '2026-12-19 00:00:00', '2027-01-03 23:59:00'),
  ('2026-2027', 'Reports', '2027-01-04 00:00:00', '2027-01-08 23:59:00'),
  ('2026-2027', 'Tirage des coupes', '2027-01-06 19:30:00', NULL),
  ('2026-2027', 'Réunion fin de demi-saison', '2027-01-11 19:30:00', NULL),
  ('2026-2027', 'Coupes', '2027-01-18 00:00:00', '2027-02-05 23:59:00'),
  ('2026-2027', 'Reports', '2027-02-08 00:00:00', '2027-02-12 23:59:00'),
  ('2026-2027', 'Vacances', '2027-02-20 00:00:00', '2027-03-07 23:59:00'),
  ('2026-2027', 'Championnats', '2027-03-08 00:00:00', '2027-04-16 23:59:00'),
  ('2026-2027', 'Férié / pont', '2027-03-29 00:00:00', NULL),
  ('2026-2027', 'Vacances', '2027-04-17 00:00:00', '2027-05-02 23:59:00'),
  ('2026-2027', 'Coupes - 1/8 de finale', '2027-05-03 00:00:00', '2027-05-14 23:59:00'),
  ('2026-2027', 'Coupes - 1/4 de finale', '2027-05-17 00:00:00', '2027-05-21 23:59:00'),
  ('2026-2027', 'Coupes - 1/2 finales', '2027-05-24 00:00:00', '2027-05-28 23:59:00'),
  ('2026-2027', 'Férié / pont', '2027-05-06 00:00:00', NULL),
  ('2026-2027', 'Férié / pont', '2027-05-07 00:00:00', NULL),
  ('2026-2027', 'Férié / pont', '2027-05-17 00:00:00', NULL),
  ('2026-2027', 'Championnats', '2027-05-31 00:00:00', '2027-06-04 23:59:00'),
  ('2026-2027', 'Reports', '2027-06-07 00:00:00', '2027-06-11 23:59:00'),
  ('2026-2027', 'Réunion fin de saison', '2027-06-15 19:30:00', NULL),
  ('2026-2027', 'Finales + récompenses', '2027-06-25 19:30:00', NULL);
