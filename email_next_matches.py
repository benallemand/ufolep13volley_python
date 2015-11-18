# coding=latin-1
import environment
import email_manager
import sql_manager

team_ids = sql_manager.sql_get_ids_team_requesting_next_matches()
if len(team_ids) <= 0:
    exit()
email_manager.email_login()
for team_id in team_ids:
    next_matches = sql_manager.sql_get_next_matches_for_team(team_id)
    if len(next_matches) <= 0:
        continue
    team_email = sql_manager.sql_get_email_from_team_id(team_id)
    if environment.environment is "DEV":
        team_email = "benallemand@gmail.com"
    email_manager.email_next_matches_to_email(next_matches, team_email)
email_manager.email_logout()
