-- Issue #454 : date de naissance des joueurs, lue sur la licence à chaque
-- import. Elle distingue un homonyme d'un joueur qui a changé de club et de
-- numéro de licence : avant, l'import refusait ce cas (« un homonyme d'un
-- autre club a déjà la licence… »).
--
-- Vide pour les fiches existantes : elle se remplit au prochain import de
-- leur licence. Donnée personnelle : aucune vue ne la reprend (players_view
-- liste ses colonnes), et le journal d'activité n'en montre jamais la valeur.
--
-- Après la migration : régénérer le schéma de la CI
-- (`pwsh .github/ci/dump-schema.ps1` dans le dépôt ufolep13volley).

ALTER TABLE joueurs
    ADD COLUMN date_naissance DATE NULL DEFAULT NULL AFTER sexe;
