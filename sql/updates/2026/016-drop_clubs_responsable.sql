-- Issue #327 : retrait des coordonnees libres du responsable de club.
--
-- `clubs.nom_responsable`, `prenom_responsable`, `tel1_responsable`,
-- `tel2_responsable` et `email_responsable` faisaient doublon avec le compte du
-- club (`users_clubs` -> `comptes_acces`) et avec la personne qui le porte
-- (`joueurs.id_compte`, pose par #326).
--
-- Elles n'etaient jamais decoratives : c'etait le contact de DERNIER RECOURS
-- quand une equipe n'a pas de responsable, et une adresse d'EXPEDITION dans
-- trois envois (recapitulatifs d'equipe, licences manquantes, factures et
-- relances d'inscription). Les cinq requetes concernees sont passees au compte
-- du club dans le depot applicatif.
--
-- PREREQUIS, a verifier AVANT de jouer ce script : aucun club engage ne doit
-- etre sans compte, sinon il perd toute coordonnee.
--
--   SELECT COUNT(DISTINCT c.id) AS clubs_engages_sans_compte
--   FROM clubs c
--            JOIN equipes e ON e.id_club = c.id
--            JOIN classements cl ON cl.id_equipe = e.id_equipe
--   WHERE NOT EXISTS (SELECT 1 FROM users_clubs uc WHERE uc.club_id = c.id);
--
-- Doit renvoyer 0. L'indicateur « Clubs engages sans compte de club » du
-- tableau de bord dit la meme chose, en plus lisible.

-- 1. sauvegarde : le DROP est irreversible, et ces colonnes portent les seules
--    coordonnees saisies a la main depuis des annees. 39 lignes en dev, c'est
--    gratuit. A supprimer quand la bascule aura fait une saison.
--    Le prefixe `zz_backup_` est une convention : `dump-schema.ps1` ecarte ces
--    tables du schema de CI, qui n'a pas a les porter.
CREATE TABLE zz_backup_clubs_responsable_327 AS
SELECT id,
       nom,
       nom_responsable,
       prenom_responsable,
       tel1_responsable,
       tel2_responsable,
       email_responsable
FROM clubs;

-- 2. les colonnes. Aucune vue ne les reference : la verification a ete faite
--    sur les sept vues du schema, seule la table `clubs` les portait.
ALTER TABLE clubs
    DROP COLUMN nom_responsable,
    DROP COLUMN prenom_responsable,
    DROP COLUMN tel1_responsable,
    DROP COLUMN tel2_responsable,
    DROP COLUMN email_responsable;

-- 3. cote depot applicatif, regenerer le schema de CI :
--    pwsh .github/ci/dump-schema.ps1
--
-- ORDRE IMPOSE avec le deploiement : le SQL EN DERNIER, ici. Le code doit avoir
-- cesse de lire ces colonnes avant qu'elles ne disparaissent — c'est l'inverse
-- des migrations #325 et #326, qui ajoutaient ce que le code allait lire.
