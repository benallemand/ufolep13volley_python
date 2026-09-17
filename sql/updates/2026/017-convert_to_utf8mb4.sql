-- Issue #334 : passer la base en utf8mb4.
--
-- SYMPTOME. Un responsable de club n'a pas pu renommer son equipe de Coupe
-- 6x6 Feminin. Le formulaire a renvoye :
--
--   Conversion from collation utf8mb3_general_ci into latin1_swedish_ci
--   impossible for parameter
--
-- CAUSE. `register` est en latin1, la connexion PHP annonce utf8, et MySQL
-- refuse de convertir un parametre lie qui contient un caractere absent de
-- latin1. Le « latin1 » de MySQL est en realite cp1252, ce qui explique que
-- les accents, l'apostrophe courbe, le tiret cadratin, les points de
-- suspension et l'euro passent -- et que l'emoji, le « check » U+2713 et
-- l'espace insecable ETROITE U+202F echouent.
--
-- Le cas le plus penible est U+202F : iOS en francais l'insere tout seul avant
-- « ? », « ! », « ; » et « : ». Il est invisible. L'utilisateur ne peut ni le
-- voir ni le corriger, et le message d'erreur ne lui apprend rien.
--
-- La panne n'a rien de specifique a l'inscription : elle attend toute saisie
-- hors cp1252, n'importe ou -- nom d'equipe, news, remarques, commentaire
-- d'activite, corps d'email.
--
-- COLLATION RETENUE : utf8mb4_0900_ai_ci, celle que portent deja la base,
-- `live_scores` et `calendar_events`, en dev comme en prod (serveur 8.0.46).
-- La retenir evite d'avoir a toucher a la valeur par defaut de la base : une
-- table creee plus tard sans clause COLLATE tombera juste.
--
-- PREREQUIS, a verifier AVANT de jouer ce script : aucune colonne latin1 ne
-- doit contenir d'UTF-8 double-encode. Si des octets UTF-8 avaient ete ecrits
-- tels quels dans une colonne latin1 (connexion mal declaree), la conversion
-- les figerait en mojibake au lieu de les reparer. Le marqueur est l'octet
-- 0xC3 ou 0xC2, qui vaut « A tilde » / « A circonflexe » en latin1 :
--
--   SELECT count(*) FROM clubs      WHERE INSTR(CAST(nom AS BINARY), 0xC3) > 0;
--   SELECT count(*) FROM equipes    WHERE INSTR(CAST(nom_equipe AS BINARY), 0xC3) > 0;
--   SELECT count(*) FROM news       WHERE INSTR(CAST(text AS BINARY), 0xC3) > 0;
--   SELECT count(*) FROM activity   WHERE INSTR(CAST(comment AS BINARY), 0xC3) > 0;
--
-- Doivent renvoyer 0. Le balayage complet des 67 colonnes latin1 a ete fait en
-- dev le 17/09/2026 : zero partout, les accents y sont bien stockes sur un
-- seul octet (0xE9 pour « e accent aigu »). La conversion est donc SANS PERTE,
-- MySQL relisant les octets latin1 pour les reencoder.
--
-- NE PAS comparer avec un LIKE : latin1_swedish_ci assimile les lettres
-- accentuees a leur lettre de base, donc LIKE '%A tilde%' ramene toute chaine
-- contenant un « a ». D'ou le CAST(... AS BINARY).
--
-- CE QUI A ETE VERIFIE EN AMONT
--
--  - Longueur des index : un seul depasse 767 octets une fois converti,
--    `comptes_acces.uq_email` sur varchar(200), soit 800. Or les 33 tables
--    sont en ROW_FORMAT=Dynamic, ou la limite InnoDB est de 3072 octets.
--    Aucun index a raccourcir, aucun prefixe a poser.
--  - Index UNIQUE : changer de collation peut rendre egales deux valeurs
--    jusque-la distinctes, et faire echouer l'ALTER en plein milieu. Les trois
--    index UNIQUE portes par une colonne texte (`comptes_acces.uq_email`,
--    `matches.code_match`, `register.new_team_name`) ont ete testes sous
--    utf8mb4_0900_ai_ci : zero collision.
--  - Cles etrangeres : les 30 FK du schema portent toutes sur des colonnes
--    numeriques. Aucune ne contraint deux colonnes texte a garder le meme jeu
--    de caracteres pendant la conversion, donc rien a desactiver.
--  - Colonnes generees : aucune.
--
-- DUREE. La conversion reconstruit chaque table. Les deux plus grosses sont
-- `activity` (~9 000 lignes) et `emails` (~6 200) : c'est l'affaire de
-- secondes, mais a jouer hors trafic.

-- ---------------------------------------------------------------------------
-- 1. les tables encore en latin1 (26)
-- ---------------------------------------------------------------------------
-- `zz_backup_clubs_responsable_327` est volontairement laissee de cote : c'est
-- la sauvegarde de l'issue #327, destinee a disparaitre, et elle n'est jointe
-- a rien.
ALTER TABLE activity CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE blacklist_by_city CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE blacklist_date CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE blacklist_gymnase CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE blacklist_team CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE blacklist_teams CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE classements CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE clubs CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE commission CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE commission_division CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE comptes_acces CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE creneau CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE dates_limite CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE emails CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE equipes CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE friendships CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE hall_of_fame CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE joueur_equipe CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE match_player CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE matches CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE news CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE register CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE registry CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE survey CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE users_clubs CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE users_teams CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------------
-- 2. les tables en utf8mb3 (4)
-- ---------------------------------------------------------------------------
-- Elles acceptent deja le « check » et l'espace etroite, mais pas les
-- caracteres sur 4 octets (emoji) : utf8mb3 s'arrete au plan multilingue de
-- base. Et tant qu'elles different de leurs voisines, chaque jointure sur une
-- colonne texte traine une conversion implicite -- c'est cette divergence
-- entre `comptes_acces` (latin1) et `joueurs` (utf8mb3) qui avait motive la
-- cle etrangere explicite `joueurs.id_compte` de l'issue #326.
ALTER TABLE competitions CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE gymnase CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE joueurs CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE photos CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------------
-- 3. la fonction stockee
-- ---------------------------------------------------------------------------
-- `SPLIT_STRING` date de 2019 et declare « RETURNS varchar(255) CHARSET
-- latin1 » : elle avait herite du jeu par defaut de la base de l'epoque. Plus
-- aucun appel ne subsiste dans le code, mais la laisser en latin1 remettrait
-- le probleme dans le schema le jour ou on s'en resservirait -- son resultat
-- ne pourrait pas etre compare a une colonne convertie sans erreur de melange
-- de collations.
--
-- Corps repris a l'identique du script 025 de 2019, jeux de caracteres rendus
-- explicites : sans eux, la fonction herite a nouveau du defaut de la base.
-- Le corps tient en une seule instruction, donc pas de BEGIN/END et pas de
-- DELIMITER a manipuler.
DROP FUNCTION IF EXISTS SPLIT_STRING;
CREATE FUNCTION SPLIT_STRING(str VARCHAR(255) CHARSET utf8mb4,
                             delim VARCHAR(12) CHARSET utf8mb4,
                             pos INT)
    RETURNS VARCHAR(255) CHARSET utf8mb4
    RETURN REPLACE(SUBSTRING(SUBSTRING_INDEX(str, delim, pos),
                             LENGTH(SUBSTRING_INDEX(str, delim, pos - 1)) + 1),
                   delim, '');

-- ---------------------------------------------------------------------------
-- 4. le defaut de la base -- non bloquant
-- ---------------------------------------------------------------------------
-- Ne change aucune donnee : c'est le jeu de caracteres dont heriteront les
-- tables creees plus tard sans clause explicite. La base de dev est deja en
-- utf8mb4_0900_ai_ci ; l'instruction n'y fait rien. Sur le mutualise OVH, le
-- compte applicatif peut ne pas avoir le privilege ALTER sur le schema : si
-- elle echoue, ce n'est pas grave, la conversion ci-dessus est deja faite.
-- Il faudra alors penser a declarer CHARSET/COLLATE dans les CREATE TABLE a
-- venir, comme le faisaient deja les scripts 002 et 012.
--
-- Le nom de base est omis a dessein : il differe entre dev (`ufolep_13volley`)
-- et prod (`ufolepvocbufolep`), et MySQL applique alors l'instruction a la
-- base courante.
ALTER DATABASE CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------------
-- 5. les vues, a rejouer APRES la conversion
-- ---------------------------------------------------------------------------
-- MySQL ne stocke pas le texte qu'on lui donne : il le normalise, et injecte
-- lui-meme un `convert(... using utf8mb3)` partout ou un CONCAT melangeait une
-- colonne latin1 et une colonne utf8mb3. Ces conversions ne sont donc PAS dans
-- les fichiers de `sql/views/` -- il suffit de les rejouer tels quels pour
-- qu'elles disparaissent.
--
-- Les laisser ne serait pas cosmetique : elles RETRONQUERAIENT en utf8mb3 ce
-- qu'on vient de convertir, et un emoji dans un nom d'equipe ressortirait en
-- « ? » a l'affichage alors qu'il serait intact en base.
--
-- Deux vues sont concernees (verifie sur les sept) :
--
--   sql/views/teams_view.sql     (6 conversions injectees)
--   sql/views/players_view.sql   (5 conversions injectees)
--
-- Les cinq autres n'en portent aucune et suivront d'elles-memes.
--
-- Controle apres coup -- doit renvoyer 0 partout :
--
--   SELECT TABLE_NAME,
--          (LENGTH(VIEW_DEFINITION) - LENGTH(REPLACE(VIEW_DEFINITION, 'using utf8mb3', ''))) / 13 AS nb
--   FROM information_schema.VIEWS
--   WHERE TABLE_SCHEMA = DATABASE();

-- ---------------------------------------------------------------------------
-- 6. cote depot applicatif
-- ---------------------------------------------------------------------------
--   pwsh .github/ci/dump-schema.ps1
--
-- ORDRE IMPOSE avec le deploiement : LE CODE D'ABORD, contrairement a #327.
-- La connexion passe de `utf8` a `utf8mb4` dans `classes/Database.php`. Tant
-- que les tables sont en latin1, cette connexion se comporte exactement comme
-- avant -- meme jeu de caracteres refuse, aucune regression -- alors que
-- l'inverse (tables converties, connexion restee en utf8mb3) laisserait les
-- emoji se faire refuser sans raison visible.
--
--   1. deployer le code, connexion en utf8mb4        (neutre)
--   2. jouer ce script                                (la conversion)
--   3. rejouer teams_view.sql puis players_view.sql   (les conversions injectees)
