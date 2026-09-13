-- Issue #326 : le referent d'un club, c'est son compte.
--
-- La personne derriere un compte etait jusqu'ici retrouvee, quand on en avait
-- besoin, en joignant `comptes_acces.email` a `joueurs.email`. C'est fragile :
--
--   * `joueurs` porte `email` ET `email2` : le referent peut avoir donne l'un
--     au club et l'autre a la ligue, et la jointure rate silencieusement ;
--   * les collations divergent (comptes_acces en latin1, joueurs en utf8mb3) :
--     la comparaison force une conversion et rend l'index inutilisable ;
--   * en dev au 13/09/2026, 6 comptes sur 146 correspondent a PLUSIEURS
--     personnes (adresses de famille, adresse generique de club, doublon de
--     saisie). Une jointure sur l'email en choisit une au hasard.
--
-- Le compte reste la source de verite pour l'email et le login ; `joueurs` ne
-- fournit plus que l'habillage (nom, prenom, telephone, photo).
--
-- Ordre impose : `players_view` reference `est_responsable_club`, elle doit
-- etre recreee avant que la colonne ne disparaisse.

-- 0. `date_homologation = '0000-00-00'` : 9 lignes en dev, toutes anciennes et
--    sans equipe. Ajouter une colonne reconstruit la table, et le sql_mode
--    (NO_ZERO_DATE, STRICT_TRANS_TABLES) refuse alors ces valeurs :
--
--      ERROR 1292 (22007): Incorrect date value: '0000-00-00'
--                          for column 'date_homologation'
--
--    Les passer a NULL ne change aucun comportement — `players_view.est_actif`
--    vaut 0 dans les deux cas, et `matchs_view.has_forbidden_player` s'appuie
--    deja sur `est_actif` — et fait afficher « — » au lieu de « 00/00/0000 ».
--
--    Pour les compter avant :
--      SELECT COUNT(*) FROM joueurs WHERE CAST(date_homologation AS CHAR) = '0000-00-00';
UPDATE joueurs
SET date_homologation = NULL
WHERE CAST(date_homologation AS CHAR) = '0000-00-00';

-- 1. le lien personne -> compte
--    UNIQUE : un compte, c'est au plus une personne. La colonne est nullable,
--    et MySQL autorise autant de NULL qu'on veut dans un index unique.
ALTER TABLE joueurs
    ADD COLUMN id_compte SMALLINT NULL,
    ADD CONSTRAINT uq_joueurs_compte UNIQUE (id_compte),
    ADD CONSTRAINT fk_joueurs_compte FOREIGN KEY (id_compte)
        REFERENCES comptes_acces (id) ON DELETE SET NULL;

-- 2. reprise initiale par correspondance d'email, SANS LES AMBIGUS.
--    La table derivee ne garde que les emails portes par une seule personne :
--    les 6 cas ambigus restent a NULL, a trancher a la main. Les lier au
--    jugé serait exactement le defaut qu'on cherche a supprimer.
--    134 liens poses en dev.
UPDATE joueurs j
    JOIN comptes_acces ca ON ca.email = j.email
    JOIN (SELECT email
          FROM joueurs
          WHERE email IS NOT NULL
            AND email <> ''
          GROUP BY email
          HAVING COUNT(*) = 1) unique_email ON unique_email.email = j.email
SET j.id_compte = ca.id;

-- 3. players_view sans `est_responsable_club` : rejouer
--    sql/views/players_view.sql (la definition est maintenue la-bas).

-- 4. `joueurs.est_responsable_club` n'etait JAMAIS lu : ni droit, ni
--    indicateur, ni requete. C'etait un champ editable expose par la vue, et
--    rien de plus — un troisieme marqueur de l'idee que porte desormais
--    `users_clubs`.
ALTER TABLE joueurs
    DROP COLUMN est_responsable_club;

-- 5. cote depot applicatif, regenerer le schema de CI :
--    pwsh .github/ci/dump-schema.ps1
--
-- Comptes de club manquants : la migration ne les cree pas. L'indicateur
-- « Clubs actifs sans compte club » du tableau de bord les liste, et l'action
-- « Créer le compte du club » de l'ecran Clubs les cree un par un (17 clubs
-- actifs sur 35 avaient un compte en dev au 13/09/2026).
