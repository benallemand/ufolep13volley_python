-- Issue #325 : un membre d'equipe peut ne pas y jouer.
--
-- Le cas type est un joueur du championnat masculin qui est aussi responsable
-- d'une equipe feminine. Il doit etre rattache a l'equipe pour la piloter, mais
-- il n'en est pas un membre jouant : il ne compte pas dans l'effectif, n'a pas
-- besoin de licence a ce titre, et n'est pas presentable en match.
--
-- Le drapeau porte sur l'APPARTENANCE et non sur la personne : un flag sur
-- `joueurs` ne saurait pas dire « jouant en masculin, non jouant en feminin ».
--
-- Le defaut a 1 rend la migration neutre : toutes les appartenances existantes
-- restent jouantes.
--
-- Ordre impose : `players_view` lit la colonne, elle doit donc exister avant
-- que la vue ne soit recreee.

-- 1. la colonne
ALTER TABLE joueur_equipe
    ADD COLUMN est_jouant BIT(1) NOT NULL DEFAULT b'1' AFTER id_equipe;

-- 2. reprise des cas connus : les hommes responsables d'une equipe feminine.
--    Deux lignes en dev au 13/09/2026 (Les novas, Fees No Men de Velaux). A
--    verifier en prod avant de jouer, la requete de controle etant :
--
--      SELECT e.nom_equipe, j.nom, j.prenom
--      FROM joueur_equipe je
--               JOIN joueurs j ON j.id = je.id_joueur
--               JOIN equipes e ON e.id_equipe = je.id_equipe
--      WHERE e.code_competition = 'f' AND j.sexe = 'M';
--
--    Les membres masculins d'une equipe feminine qui ne sont PAS responsables
--    ne sont pas repris automatiquement : ce serait une anomalie a trancher au
--    cas par cas, pas un membre non jouant.
UPDATE joueur_equipe je
    JOIN joueurs j ON j.id = je.id_joueur
    JOIN equipes e ON e.id_equipe = je.id_equipe
SET je.est_jouant = b'0'
WHERE e.code_competition = 'f'
  AND j.sexe = 'M'
  AND je.is_leader + 0 > 0;

-- 3. players_view gagne `non_playing_teams_list` : rejouer
--    sql/views/players_view.sql (la definition est maintenue la-bas, la
--    dupliquer ici la ferait diverger au prochain changement).

-- 4. cote depot applicatif, regenerer le schema de CI :
--    pwsh .github/ci/dump-schema.ps1
