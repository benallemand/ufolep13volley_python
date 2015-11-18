# coding=latin-1
import environment
import email_manager
import sql_manager

players_without_licence_number = sql_manager.sql_get_players_without_licence_number()
if len(players_without_licence_number) <= 0:
    exit()
email_manager.email_login()
for players_without_licence_number_per_leader in players_without_licence_number:
    email_manager.email_players_without_licence_number_per_leader(players_without_licence_number_per_leader)
email_manager.email_logout()
