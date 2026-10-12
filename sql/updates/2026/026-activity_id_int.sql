-- Issue #423 : `activity.id` était un SMALLINT, plafonné à 32 767. Au
-- 12/10/2026 en prod : 28 329, environ 95 lignes par jour (les lignes
-- anciennes sont purgées, l'auto-incrément continue). Limite atteinte vers fin
-- novembre 2026, et avec elle l'échec de `Generic::addActivity`, donc de la
-- plupart des écritures du site.
--
-- `user_id` reste un SMALLINT : il suit `comptes_acces.id`.

-- 1. À regarder avant : type actuel et marge.
SELECT column_type, (SELECT MAX(id) FROM activity) AS max_id
FROM information_schema.columns
WHERE table_schema = DATABASE() AND table_name = 'activity' AND column_name = 'id';

-- 2. La correction (clés et auto-incrément conservés).
ALTER TABLE activity MODIFY id INT NOT NULL AUTO_INCREMENT;
