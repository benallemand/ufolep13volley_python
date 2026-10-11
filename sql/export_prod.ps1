<#
.SYNOPSIS
    Exporte la base de prod par SSH dans sql/ufolepvocbufolep.sql, sans
    phpMyAdmin, puis la réimporte en local avec -Import.

.DESCRIPTION
    Le dump est fait sur l'hébergement (alias SSH `ovh-ufolep`, voir
    ~\.ssh\config), avec les identifiants du `.env` du site : rien de secret
    ici ni dans le fichier produit, à part les données elles-mêmes.

    Le mysqldump de l'hébergement est celui de MariaDB 10.3, face à un
    serveur MySQL 8.0 : il s'arrête sans message (code 2) sur les triggers.
    Ils sont donc exportés à part, depuis information_schema.

    sql/ufolepvocbufolep.sql n'est pas versionné (.gitignore).

.EXAMPLE
    pwsh sql/export_prod.ps1            # export seul
    pwsh sql/export_prod.ps1 -Import    # export puis import en local (comme import_db.bat)
#>
param(
    [string]$SshHost = 'ovh-ufolep',
    [switch]$Import,
    [string]$Database = 'ufolep_13volley',
    [string]$LocalPassword = 'test',
    [string]$Mysql = 'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe'
)

$ErrorActionPreference = 'Stop'
$outFile = Join-Path $PSScriptRoot 'ufolepvocbufolep.sql'
$gzFile = "$outFile.gz"

# CHAR(96) : l'accent grave, qu'on ne peut pas écrire tel quel dans une chaîne
# bash entre guillemets doubles.
$remote = @'
set -eo pipefail
cd ~/www
set -a; . ./.env; set +a
export MYSQL_PWD="$DB_PASSWORD"
C="-h $DB_SERVER -P ${DB_PORT:-3306} -u $DB_USER"
{
  mysqldump $C --single-transaction --quick --no-tablespaces --routines --skip-triggers \
    --hex-blob --default-character-set=utf8mb4 "$DB_NAME"
  mysql $C --default-character-set=utf8mb4 -N -B --raw "$DB_NAME" -e "
    SELECT CONCAT('DROP TRIGGER IF EXISTS ', CHAR(96), trigger_name, CHAR(96), ';\nDELIMITER ;;\n',
                  'CREATE TRIGGER ', CHAR(96), trigger_name, CHAR(96), ' ', action_timing, ' ',
                  event_manipulation, ' ON ', CHAR(96), event_object_table, CHAR(96),
                  ' FOR EACH ROW ', action_statement, ';;\nDELIMITER ;')
    FROM information_schema.triggers WHERE trigger_schema = DATABASE()"
} | gzip > ~/export_prod.sql.gz
'@ -replace "`r`n", "`n"

Write-Host "Export de la base de prod sur $SshHost..."
# En base64 : passé par l'entrée standard, PowerShell ajoutait un retour
# chariot à la dernière ligne, et le fichier distant s'appelait
# « export_prod.sql.gz\r ».
$encoded = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($remote))
ssh $SshHost "echo $encoded | base64 -d | bash"
if ($LASTEXITCODE -ne 0) { throw "Export distant en échec (code $LASTEXITCODE)" }

scp -q "${SshHost}:export_prod.sql.gz" $gzFile
if ($LASTEXITCODE -ne 0) { throw "Rapatriement en échec (code $LASTEXITCODE)" }
ssh $SshHost 'rm -f ~/export_prod.sql.gz'

$in = [System.IO.File]::OpenRead($gzFile)
$out = [System.IO.File]::Create($outFile)
try {
    $gzip = New-Object System.IO.Compression.GZipStream($in, [System.IO.Compression.CompressionMode]::Decompress)
    $gzip.CopyTo($out)
}
finally {
    $out.Dispose()
    $in.Dispose()
}
Remove-Item $gzFile

# Lu et réécrit octet pour octet (Latin1) : en UTF-8, la relecture remplaçait
# par U+FFFD les octets invalides, ceux de document_cache.content notamment.
$bytes = [System.Text.Encoding]::Latin1
$sql = [System.IO.File]::ReadAllText($outFile, $bytes)
# Autour de la fonction SPLIT_STRING, mysqldump bascule le jeu de caractères de
# la base en la nommant (`ufolepvocbufolep`), base qui n'existe pas en local
# (ufolep_13volley) : l'import s'arrêtait là, sans les vues.
$sql = [regex]::Replace($sql, '(?m)^ALTER DATABASE `[^`]+` CHARACTER SET .*\r?\n', '')
[System.IO.File]::WriteAllText($outFile, $sql, $bytes)
$tables = ([regex]::Matches($sql, 'CREATE TABLE')).Count
$triggers = ([regex]::Matches($sql, 'CREATE TRIGGER')).Count
if (-not $sql.Contains('-- Dump completed') -or ($triggers -gt 0 -and -not $sql.TrimEnd().EndsWith('DELIMITER ;'))) {
    throw "Export incomplet : $outFile"
}
Write-Host ("Export : {0} tables, {1} trigger(s), {2:N1} Mo -> {3}" -f $tables, $triggers,
    ((Get-Item $outFile).Length / 1MB), $outFile)

if ($Import) {
    # Comme import_db.bat : base recréée de zéro, puis l'export.
    Write-Host "Import en local dans $Database..."
    $recreate = Join-Path $PSScriptRoot 'support\_01-recreate_database.sql'
    foreach ($step in @(@('sys', $recreate), @($Database, $outFile))) {
        & $Mysql --default-character-set=utf8mb4 -h localhost -u root "-p$LocalPassword" $step[0] `
            -e "source $($step[1])" 2>&1 | Where-Object { "$_" -notmatch 'Using a password' }
        if ($LASTEXITCODE -ne 0) { throw "Import en échec ($($step[1]), code $LASTEXITCODE)" }
    }
    Write-Host 'Import terminé.'
}
