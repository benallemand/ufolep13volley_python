# coding=latin-1
import email_manager
import sql_manager

activities = sql_manager.sql_get_activity()
if len(activities) <= 0:
    exit()
email_manager.email_login()
email_manager.send_emails_for_activity(activities)
email_manager.email_logout()
