DELETE
FROM activity
WHERE (comment LIKE 'Ajout de %') ||
      (comment LIKE '% a ete supprime de %')
        AND activity_date < STR_TO_DATE(:date_debut_compet, '%d/%m/%Y');