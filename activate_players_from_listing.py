# coding=latin-1
import data_manager
import sql_manager


licences = data_manager.get_listing_volley_licences()
if len(licences) <= 0:
    exit()
sql_manager.activate_players(licences)
