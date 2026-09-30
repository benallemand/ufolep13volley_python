-- Issue #376 : une demande d'inscription peut être refusée par la commission
-- (par exemple une équipe « volante », sans gymnase de réception, désormais
-- interdite).
--
-- REFUSED s'ajoute à PENDING / VALIDATED. Le motif est obligatoire côté
-- application ; il est envoyé au club par email et affiché dans son espace.
-- Le club peut corriger sa demande refusée : l'enregistrer la remet en
-- PENDING, motif effacé.

ALTER TABLE register
    MODIFY status ENUM ('PENDING', 'VALIDATED', 'REFUSED') NOT NULL DEFAULT 'PENDING',
    ADD COLUMN refusal_reason VARCHAR(1000) NULL AFTER validation_date,
    ADD COLUMN refusal_date   DATETIME      NULL AFTER refusal_reason;

-- côté dépôt applicatif, regénérer le schéma de CI :
--    pwsh .github/ci/dump-schema.ps1
