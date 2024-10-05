@ECHO OFF

ECHO Running script
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" --default-character-set=utf8 -h localhost -u root -ptest sys < support\\_01-recreate_database.sql
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" --default-character-set=utf8 -h localhost -u root -ptest ufolep_13volley < ufolepvocbufolep.sql

ECHO Finished!