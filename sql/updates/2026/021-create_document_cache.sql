-- Issue #342 : le règlement général est lu dans Google Docs.
--
-- Le serveur récupère les exports HTML et PDF du document et les garde ici :
-- une visite ne déclenche pas d'appel à Google tant que le cache est frais
-- (15 min), et si Google ne répond pas, la dernière version reste servie.
-- En base plutôt que sur disque : le code n'est pas inscriptible dans tous les
-- environnements (image Docker du home server, conteneur de la CI).
--
-- `source_id` : identifiant du document mis en cache, pour qu'un changement de
-- document dans le registre invalide l'ancien contenu.
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

-- Le document du règlement général, modifiable ensuite dans l'admin (« Base de
-- registres »). URL complète ou identifiant seul : les deux sont acceptés.
-- ⚠️ Dès cette ligne en place, le site affiche le contenu du document : il doit
-- être à jour AVANT la migration.
INSERT INTO registry (registry_key, registry_value)
SELECT 'rules.general.document', 'https://docs.google.com/document/d/1__0tiCfP-6Rs0bq6Ir2rkLgMrN5DvJ50/'
WHERE NOT EXISTS (SELECT 1 FROM registry WHERE registry_key = 'rules.general.document');

-- côté dépôt applicatif, regénérer le schéma de CI :
--    pwsh .github/ci/dump-schema.ps1
