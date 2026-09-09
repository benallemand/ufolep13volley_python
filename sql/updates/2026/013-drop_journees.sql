-- Issue #279 (lot 3) : suppression de la notion de journee.
--
-- La generation des calendriers est passee aux scripts Python de ce depot
-- (`calendar-agent/`), qui inserent les matchs sans `id_journee` et ne
-- touchent jamais `journees`. Le moteur PHP qui alimentait la table a ete
-- retire du depot applicatif ; la table n'etait plus lue que par `matchs_view`,
-- pour un regroupement d'affichage vide en pratique.
--
-- AVANT DE JOUER CE SCRIPT, verifier que la prod est dans le meme etat que le
-- dev (0 match rattache a une journee) :
--
--   SELECT COUNT(*) FROM matches WHERE id_journee IS NOT NULL;
--
-- Si le compte n'est pas nul, ce sont des matchs anciens : le rattachement sera
-- perdu (il n'etait qu'affiche, jamais utilise dans un calcul de classement).
--
-- Ordre impose : la vue reference la colonne, elle doit etre recreee avant que
-- la colonne ne disparaisse.

-- 1. matchs_view sans `numero_journee`, `id_journee` ni `journee`
--    (definition de la vue existante, moins ces trois colonnes et la jointure)
CREATE OR REPLACE VIEW `matchs_view` AS
with `computed_forfait` as (select `m`.`id_match` AS `id_match`,if(((`m`.`set_1_dom` = 25) and (`m`.`set_1_ext` = 0) and (`m`.`set_2_dom` = 25) and (`m`.`set_2_ext` = 0) and (`m`.`set_3_dom` = 25) and (`m`.`set_3_ext` = 0) and (0 <> `m`.`is_sign_match_dom`) and (0 <> `m`.`is_sign_match_ext`)),1,0) AS `forfait_ext`,if(((`m`.`set_1_dom` = 0) and (`m`.`set_1_ext` = 25) and (`m`.`set_2_dom` = 0) and (`m`.`set_2_ext` = 25) and (`m`.`set_3_dom` = 0) and (`m`.`set_3_ext` = 25) and (0 <> `m`.`is_sign_match_dom`) and (0 <> `m`.`is_sign_match_ext`)),1,0) AS `forfait_dom`,if((((`m`.`set_1_dom` = 25) and (`m`.`set_1_ext` = 0) and (`m`.`set_2_dom` = 25) and (`m`.`set_2_ext` = 0) and (`m`.`set_3_dom` = 25) and (`m`.`set_3_ext` = 0) and (0 <> `m`.`is_sign_match_dom`) and (0 <> `m`.`is_sign_match_ext`)) or ((`m`.`set_1_dom` = 0) and (`m`.`set_1_ext` = 25) and (`m`.`set_2_dom` = 0) and (`m`.`set_2_ext` = 25) and (`m`.`set_3_dom` = 0) and (`m`.`set_3_ext` = 25) and (0 <> `m`.`is_sign_match_dom`) and (0 <> `m`.`is_sign_match_ext`))),1,0) AS `is_forfait` from `matches` `m`), `computed_score` as (select `m`.`id_match` AS `id_match`,((((if(((`m`.`set_1_dom` >= 25) and (`m`.`set_1_dom` >= (`m`.`set_1_ext` + 2))),1,0) + if(((`m`.`set_2_dom` >= 25) and (`m`.`set_2_dom` >= (`m`.`set_2_ext` + 2))),1,0)) + if(((`m`.`set_3_dom` >= 25) and (`m`.`set_3_dom` >= (`m`.`set_3_ext` + 2))),1,0)) + if(((`m`.`set_4_dom` >= 25) and (`m`.`set_4_dom` >= (`m`.`set_4_ext` + 2))),1,0)) + if(((`m`.`set_5_dom` >= 15) and (`m`.`set_5_dom` >= (`m`.`set_5_ext` + 2))),1,0)) AS `score_equipe_dom`,((((if(((`m`.`set_1_ext` >= 25) and (`m`.`set_1_ext` >= (`m`.`set_1_dom` + 2))),1,0) + if(((`m`.`set_2_ext` >= 25) and (`m`.`set_2_ext` >= (`m`.`set_2_dom` + 2))),1,0)) + if(((`m`.`set_3_ext` >= 25) and (`m`.`set_3_ext` >= (`m`.`set_3_dom` + 2))),1,0)) + if(((`m`.`set_4_ext` >= 25) and (`m`.`set_4_ext` >= (`m`.`set_4_dom` + 2))),1,0)) + if(((`m`.`set_5_ext` >= 15) and (`m`.`set_5_ext` >= (`m`.`set_5_dom` + 2))),1,0)) AS `score_equipe_ext` from `matches` `m`) select `m`.`id_match` AS `id_match`,`cf`.`forfait_dom` AS `forfait_dom`,`cf`.`forfait_ext` AS `forfait_ext`,`cf`.`is_forfait` AS `is_forfait`,if(((`cs`.`score_equipe_dom` = 3) or (`cs`.`score_equipe_ext` = 3)),1,0) AS `is_match_score_filled`,if((`mpcv`.`id_match` is not null),1,0) AS `is_match_player_filled`,`mpcv`.`count_status` AS `count_status`,if(((`mpcv`.`id_match` is null) and (`cf`.`is_forfait` = 0) and (`m`.`certif` = 0)),1,0) AS `is_match_player_requested`,if((`m`.`id_match` in (select `match_player`.`id_match` from (`match_player`
    join `players_view` `j2` on((`match_player`.`id_player` = `j2`.`id`))) where ((`j2`.`est_actif` = 0) or (str_to_date(`j2`.`date_homologation`,'%d/%m/%Y') > `m`.`date_reception`) or (`j2`.`date_homologation` is null) or (`j2`.`num_licence` is null))) and (`cf`.`is_forfait` = 0)),1,0) AS `has_forbidden_player`,`m`.`code_match` AS `code_match`,`m`.`code_competition` AS `code_competition`,`c`.`id_compet_maitre` AS `parent_code_competition`,`c`.`libelle` AS `libelle_competition`,`m`.`division` AS `division`,`m`.`id_equipe_dom` AS `id_equipe_dom`,`e1`.`nom_equipe` AS `equipe_dom`,`m`.`id_equipe_ext` AS `id_equipe_ext`,`e2`.`nom_equipe` AS `equipe_ext`,`cs`.`score_equipe_dom` AS `score_equipe_dom`,`cs`.`score_equipe_ext` AS `score_equipe_ext`,`m`.`set_1_dom` AS `set_1_dom`,`m`.`set_1_ext` AS `set_1_ext`,`m`.`set_2_dom` AS `set_2_dom`,`m`.`set_2_ext` AS `set_2_ext`,`m`.`set_3_dom` AS `set_3_dom`,`m`.`set_3_ext` AS `set_3_ext`,`m`.`set_4_dom` AS `set_4_dom`,`m`.`set_4_ext` AS `set_4_ext`,`m`.`set_5_dom` AS `set_5_dom`,`m`.`set_5_ext` AS `set_5_ext`,`cr`.`heure` AS `heure_reception`,`m`.`id_gymnasium` AS `id_gymnasium`,`g`.`nom` AS `gymnasium`,date_format(`m`.`date_reception`,'%d/%m/%Y') AS `date_reception`,(unix_timestamp(((`m`.`date_reception` + interval 23 hour) + interval 59 minute)) * 1000) AS `date_reception_raw`,date_format(`m`.`date_original`,'%d/%m/%Y') AS `date_original`,(unix_timestamp(((`m`.`date_original` + interval 23 hour) + interval 59 minute)) * 1000) AS `date_original_raw`,if(((`m`.`is_sign_team_ext` = 1) and (`m`.`is_sign_team_dom` = 1) and (`m`.`is_sign_match_ext` = 1) and (`m`.`is_sign_match_dom` = 1)),1,0) AS `sheet_received`,`m`.`note` AS `note`,`m`.`certif` AS `certif`,`m`.`report_status` AS `report_status`,(case when ((`cs`.`score_equipe_dom` + `cs`.`score_equipe_ext`) > 0) then 0 when (`m`.`date_reception` >= curdate()) then 0 when (curdate() >= (`m`.`date_reception` + interval 10 day)) then 2 when (curdate() >= (`m`.`date_reception` + interval 5 day)) then 1 end) AS `retard`,`m`.`match_status` AS `match_status`,`m`.`is_sign_match_dom` AS `is_sign_match_dom`,`m`.`is_sign_match_ext` AS `is_sign_match_ext`,`m`.`is_sign_team_dom` AS `is_sign_team_dom`,`m`.`is_sign_team_ext` AS `is_sign_team_ext`,`jresp_dom`.`email` AS `email_dom`,`jresp_ext`.`email` AS `email_ext`,`m`.`referee` AS `referee`,if((`s_dom`.`id` is not null),1,0) AS `is_survey_filled_dom`,if((`s_ext`.`id` is not null),1,0) AS `is_survey_filled_ext`,group_concat(distinct `com`.`email` separator ',') AS `contact_com` from (((((((((((((((((`matches` `m`
    join `computed_forfait` `cf` on((`m`.`id_match` = `cf`.`id_match`)))
    join `computed_score` `cs` on((`m`.`id_match` = `cs`.`id_match`)))
    join `competitions` `c` on((`c`.`code_competition` = `m`.`code_competition`)))
    join `equipes` `e1` on((`e1`.`id_equipe` = `m`.`id_equipe_dom`)))
    left join `joueur_equipe` `jeresp_dom` on(((`jeresp_dom`.`id_equipe` = `e1`.`id_equipe`) and (`jeresp_dom`.`is_leader` = 1))))
    left join `joueurs` `jresp_dom` on((`jeresp_dom`.`id_joueur` = `jresp_dom`.`id`)))
    join `equipes` `e2` on((`e2`.`id_equipe` = `m`.`id_equipe_ext`)))
    left join `joueur_equipe` `jeresp_ext` on(((`jeresp_ext`.`id_equipe` = `e2`.`id_equipe`) and (`jeresp_ext`.`is_leader` = 1))))
    left join `joueurs` `jresp_ext` on((`jeresp_ext`.`id_joueur` = `jresp_ext`.`id`))))
    left join `creneau` `cr` on(((`cr`.`id_equipe` = `m`.`id_equipe_dom`) and (`cr`.`jour` = elt((weekday(`m`.`date_reception`) + 2),'Dimanche','Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi')) and (`cr`.`id_gymnase` = `m`.`id_gymnasium`))))
    left join `gymnase` `g` on((`m`.`id_gymnasium` = `g`.`id`)))
    left join `match_players_count_view` `mpcv` on((`mpcv`.`id_match` = `m`.`id_match`)))
    left join `survey` `s_dom` on(((`m`.`id_match` = `s_dom`.`id_match`) and `s_dom`.`user_id` in (select `ca`.`id` from (`comptes_acces` `ca`
    join `users_teams` `ut` on((`ca`.`id` = `ut`.`user_id`))) where (`ut`.`team_id` = `m`.`id_equipe_dom`)))))
    left join `survey` `s_ext` on(((`m`.`id_match` = `s_ext`.`id_match`) and `s_ext`.`user_id` in (select `ca`.`id` from (`comptes_acces` `ca`
    join `users_teams` `ut` on((`ca`.`id` = `ut`.`user_id`))) where (`ut`.`team_id` = `m`.`id_equipe_ext`)))))
    left join `commission_division` `cd` on((`cd`.`division` = concat(`m`.`code_competition`,'/',`m`.`division`))))
    left join `commission` `com` on((`cd`.`id_commission` = `com`.`id_commission`)))
    where (1 = 1) group by `m`.`id_match`,`m`.`code_competition`,`m`.`division`,`m`.`code_match`
    order by `m`.`code_competition`,`m`.`division`,`m`.`code_match`;

-- 2. matches.id_journee
ALTER TABLE `matches` DROP FOREIGN KEY `fk_matches_journees`;
ALTER TABLE `matches` DROP INDEX `fk_matches_journees`;
ALTER TABLE `matches` DROP COLUMN `id_journee`;

-- 3. la table elle-meme
DROP TABLE `journees`;
