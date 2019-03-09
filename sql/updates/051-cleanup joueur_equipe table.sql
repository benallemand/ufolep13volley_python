DELETE
FROM joueur_equipe
WHERE
  id_equipe NOT IN (
    SELECT id_equipe
    FROM equipes
  )
  OR id_joueur NOT IN (
    SELECT id
    FROM joueurs
  );