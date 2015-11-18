# coding=latin-1
import environment
import email_manager
import sql_manager

accounts = sql_manager.sql_get_accounts()
if len(accounts) <= 0:
    exit()
email_manager.email_login()
for account in accounts:
    if environment.environment is "DEV":
        account['email'] = "benallemand@gmail.com"
    email_manager.email_send_account_recap(account)
    sql_manager.sql_update_email_sent_flag(account['id'])
email_manager.email_logout()
