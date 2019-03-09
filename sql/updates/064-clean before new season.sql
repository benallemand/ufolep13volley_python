DELETE FROM activity where activity_date < '2017-10-03';
DELETE FROM joueur_equipe;
DELETE FROM creneau;
DELETE FROM files;
UPDATE joueurs SET est_actif = 0;
UPDATE classements SET penalite = 0;
UPDATE classements SET report_count = 0;
