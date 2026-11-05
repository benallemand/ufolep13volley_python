-- Issue #458 : annuler une pénalité automatique depuis l'administration.
--
-- Une pénalité annulée garde sa ligne : la clé unique (match, équipe, motif)
-- empêche alors le cron de pénaliser le match une seconde fois. Elle ne
-- compte plus dans l'indicateur « Pénalités automatiques » ni dans les
-- alertes des responsables d'équipe.
--
-- Après la migration : régénérer le schéma de la CI
-- (`pwsh .github/ci/dump-schema.ps1` dans le dépôt ufolep13volley).

ALTER TABLE match_penalties
    ADD COLUMN cancelled_at DATETIME NULL DEFAULT NULL AFTER created_at;
