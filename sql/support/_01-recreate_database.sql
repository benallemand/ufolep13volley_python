SET GLOBAL log_bin_trust_function_creators = 1;
SET PERSIST sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''));
DROP DATABASE IF EXISTS ufolep_13volley;
CREATE DATABASE ufolep_13volley;