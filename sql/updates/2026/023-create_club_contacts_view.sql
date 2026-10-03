-- Issue #395 : à qui écrire pour un club, règle écrite une seule fois.
--
-- Le référent d'un club, c'est son compte (`users_clubs` → `comptes_acces`,
-- issue #326). À défaut de compte, on retombe sur les emails des responsables
-- d'équipe du club. C'était la règle de l'indicateur « Clubs sans aucune
-- inscription » (#338) ; les indicateurs de préparation de saison la
-- reprennent désormais par cette vue.
--
-- `contact` vaut NULL pour un club sans compte ni responsable avec email.

CREATE OR REPLACE VIEW club_contacts_view AS
SELECT cl.id AS id_club,
       COALESCE(
               NULLIF((SELECT GROUP_CONCAT(DISTINCT ca.email ORDER BY ca.email SEPARATOR ', ')
                       FROM users_clubs uc
                                JOIN comptes_acces ca ON ca.id = uc.user_id
                       WHERE uc.club_id = cl.id), ''),
               (SELECT GROUP_CONCAT(DISTINCT j.email ORDER BY j.email SEPARATOR ', ')
                FROM joueurs j
                WHERE j.id_club = cl.id
                  AND NULLIF(TRIM(j.email), '') IS NOT NULL
                  AND EXISTS (SELECT 1
                              FROM joueur_equipe je
                              WHERE je.id_joueur = j.id
                                AND je.is_leader + 0 > 0))
       ) AS contact
FROM clubs cl;

-- côté dépôt applicatif, regénérer le schéma de CI :
--    pwsh .github/ci/dump-schema.ps1
