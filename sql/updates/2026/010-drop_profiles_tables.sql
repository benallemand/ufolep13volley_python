-- Issue #245 (phase finale) : suppression du mécanisme de profils exclusifs.
-- Les rôles sont dérivés et cumulables depuis les migrations 008/009 :
--   admin           -> comptes_acces.is_admin
--   resp. d'équipe  -> existence d'une ligne users_teams
--   resp. de club   -> existence d'une ligne users_clubs
-- Plus aucun code ne lit profiles/users_profiles : on droppe.

DROP TABLE users_profiles;

DROP TABLE profiles;
