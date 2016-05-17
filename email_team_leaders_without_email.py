# coding=latin-1
import email_manager
import sql_manager

team_leaders_without_email = sql_manager.sql_get_team_leaders_without_email()
if len(team_leaders_without_email) <= 0:
    exit()
email_manager.email_login()
email_manager.email_team_leaders_without_email(team_leaders_without_email)
email_manager.email_logout()
#TODO Add python script to Jenkins