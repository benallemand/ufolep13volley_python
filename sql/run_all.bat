@ECHO OFF

ECHO Running script
"C:\Program Files\MySQL\MySQL Server 5.7\bin\mysql.exe" --default-character-set=utf8 -h localhost -u root ufolep_13volley < support\\_01-recreate_database.sql
"C:\Program Files\MySQL\MySQL Server 5.7\bin\mysql.exe" --default-character-set=utf8 -h localhost -u root ufolep_13volley < ufolepvocbufolep.sql

ECHO Finished!
pause