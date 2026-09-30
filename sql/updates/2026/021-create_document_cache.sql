-- Issue #342 : les règlements sont lus dans le dossier Google Drive de la
-- commission (un sous-dossier par saison, nommé « AAAA-AAAA »).
--
-- Le serveur récupère la liste des dossiers et les exports HTML et PDF des
-- documents, et les garde ici : une visite ne déclenche pas d'appel à Google
-- tant que le cache est frais (15 min), et si Google ne répond pas, la
-- dernière version reste servie.
-- En base plutôt que sur disque : le code n'est pas inscriptible dans tous les
-- environnements (image Docker du home server, conteneur de la CI).
--
-- `cache_key` : `rules.<folder|html|pdf>.<identifiant Google>`.
-- `source_id` : identifiant Google du dossier ou du document.
-- `checked_at` : dernière tentative, réussie ou non (on ne relance pas Google
-- plus d'une fois toutes les 5 min quand il ne répond pas).

CREATE TABLE document_cache
(
    cache_key    VARCHAR(64)  NOT NULL,
    source_id    VARCHAR(100) NOT NULL,
    content      MEDIUMBLOB   NULL,
    content_type VARCHAR(100) NOT NULL,
    fetched_at   DATETIME     NULL,
    checked_at   DATETIME     NOT NULL,
    PRIMARY KEY (cache_key)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci;

-- Le dossier des règlements se désigne APRÈS la migration, dans l'admin
-- (« Base de registres ») : clé `rules.folder`, valeur = URL du dossier ou son
-- identifiant. Il n'est volontairement PAS écrit ici : ce dépôt est public, et
-- l'adresse d'un dossier Drive n'a rien à y faire. Tant que la clé manque, la
-- page des règlements affiche « momentanément indisponibles ».
-- ⚠️ Dès la clé posée, le site affiche les documents du dossier : ils doivent
-- être à jour avant.

-- côté dépôt applicatif, regénérer le schéma de CI :
--    pwsh .github/ci/dump-schema.ps1
