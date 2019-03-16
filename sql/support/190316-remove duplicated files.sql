DELETE f1
FROM files f1,
     files f2
WHERE f1.id > f2.id
  AND f1.hash = f2.hash;