-- Issue #245 : refonte des rôles.
-- Les rôles deviennent dérivés et cumulables :
--   admin           -> comptes_acces.is_admin = 1
--   resp. d'équipe  -> existence d'une ligne users_teams
--   resp. de club   -> existence d'une ligne users_clubs
-- Cette migration ajoute le flag et le remplit depuis les anciens profils.
-- Les tables profiles/users_profiles seront supprimées dans une migration
-- ultérieure, après validation en production.

ALTER TABLE comptes_acces
    ADD COLUMN is_admin TINYINT(1) NOT NULL DEFAULT 0;

UPDATE comptes_acces ca
SET ca.is_admin = 1
WHERE EXISTS (SELECT 1
              FROM users_profiles up
                       JOIN profiles p ON p.id = up.profile_id
              WHERE up.user_id = ca.id
                AND p.name IN ('ADMINISTRATEUR', 'COMMISSION', 'SUPPORT'));
