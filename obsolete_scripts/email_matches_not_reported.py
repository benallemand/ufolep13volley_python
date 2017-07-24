import email_manager
import sql_manager

matches_not_reported = sql_manager.sql_get_matches_not_reported()
if len(matches_not_reported) <= 0:
    exit()
email_manager.email_login()
for match_not_reported in matches_not_reported:
    email_manager.email_match_not_reported(match_not_reported)
email_manager.email_logout()
