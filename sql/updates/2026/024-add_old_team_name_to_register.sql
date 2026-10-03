-- Issue #402 : nom de l'ancienne équipe au moment de la réinscription.
--
-- Une réinscription désigne son ancienne équipe (`old_team_id`), et
-- « Équipes / comptes » comme « Initialiser la saison » renomment cette équipe
-- sans changer son identifiant. L'ancien nom n'était conservé nulle part :
-- l'écran de réorganisation des divisions ne pouvait plus dire qui était une
-- équipe la saison passée.
--
-- `Register::register()` renseigne la colonne quand le club fait sa demande,
-- avant tout renommage, et ne la touche plus ensuite.

ALTER TABLE register
    ADD COLUMN old_team_name VARCHAR(50) NULL AFTER old_team_id;

-- Reprise : seulement les équipes pas encore renommées. Quand l'équipe porte
-- déjà le nom demandé, impossible de savoir si elle a été renommée ou si le
-- club a gardé son nom : la colonne reste vide, et l'écran n'affiche pas
-- d'ancien nom.
UPDATE register r
    JOIN equipes e ON e.id_equipe = r.old_team_id
SET r.old_team_name = e.nom_equipe
WHERE r.old_team_name IS NULL
  AND e.nom_equipe <> r.new_team_name;

-- côté dépôt applicatif, regénérer le schéma de CI :
--    pwsh .github/ci/dump-schema.ps1
