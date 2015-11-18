# coding=latin-1
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import environment

if environment.environment is "DEV":
    pass
elif environment.environment is "PROD":
    pass
else:
    raise EnvironmentError("Environnement inconnu")

server = None


def email_logout():
    server.quit()
    return


def email_login():
    global server
    # Credentials (if needed)
    username = environment.globEmailUserName
    password = environment.globEmailPassword
    # The actual mail send
    server = smtplib.SMTP(environment.globEmailSmtp)
    server.starttls()
    server.login(username, password)
    return


def email_send_account_recap(account):
    me = 'noreply@ufolep13volley.org'
    msg = MIMEMultipart('alternative')
    you = account['email']
    msg['Subject'] = "R�capitulatif de vos identifiants Ufolep13Volley"
    msg['From'] = me
    msg['To'] = you
    string_message = """
    <p>
        Bonjour,<br/>
        <br/>
        Veuillez trouver ci-joint vos identifiants pour le site ufolep13volley.org :<br/>
        <br/>
        Email: %s<br/>
        <br/>
        Identifiant: %s<br/>
        <br/>
        Mot de passe: %s<br/>
        <br/>
        Equipe li�e: %s<br/>
        <br/>
        Competition: %s<br/>
        <br/>
        <br/>
        Si ce compte n'est plus valable (mauvaise adresse email, mauvaise �quipe...),
        n'h�sitez pas � cr�er de nouveau un compte ou � contacter la CTSD.<br/>
        Cordialement,<br/>
        La CTSD<br/>
        http://www.ufolep13volley.org<br/>
    </p>
    """ % (account['email'], account['login'], account['password'], account['nom_equipe'], account['competition'])
    html = """
    <html>
        <head></head>
        <body>
            %s
        </body>
    </html>
    """ % string_message
    msg.attach(MIMEText(html, 'html'))
    server.sendmail(me, you, msg.as_string())
    return


def send_emails_for_activity(activities):
    me = 'noreply@ufolep13volley.org'
    recipients = [
        'benallemand@gmail.com',
        'philipvolley@free.fr'
    ]
    you = ", ".join(recipients)
    if environment.environment is "DEV":
        you = "benallemand@gmail.com"
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Activit�"
    msg['From'] = me
    msg['To'] = you
    string_message = """
    <p>
        Bonjour,<br/>
        <br/>
        Voici l'activit� r�cente du site ufolep13volley.org (2  derniers jours)<br/>
        <br/>
        Bonne journ�e<br/>
        <br/>
        Cordialement,<br/>
        La CTSD<br/>
        http://www.ufolep13volley.org<br/>
    </p>"""
    string_activity = ""
    for activity in activities:
        string_activity = """
        %s
        <tr>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
        </tr>
        """ % (
            string_activity,
            activity['date'],
            activity['nom_equipe'],
            activity['competition'],
            activity['description'],
            activity['utilisateur'],
            activity['email_utilisateur'])
    html = """
    <html>
        <head></head>
        <body>
            %s
            <table border="1">
                <tr>
                    <th>Date</th>
                    <th>Nom d'�quipe</th>
                    <th>Comp�tition</th>
                    <th>Description</th>
                    <th>Utilisateur</th>
                    <th>Email</th>
                </tr>
                %s
            </table>
        </body>
    </html>
    """ % (string_message, string_activity)
    msg.attach(MIMEText(html, 'html'))
    server.sendmail(me, recipients, msg.as_string())
    return


def email_next_matches_to_email(next_matches, team_email):
    me = 'noreply@ufolep13volley.org'
    recipients = [
        team_email,
        'benallemand@gmail.com'
    ]
    you = ", ".join(recipients)
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Liste des matches de la semaine"
    msg['From'] = me
    msg['To'] = you
    string_message = """
    <p>
        Bonjour,<br/>
        <br/>
        Voici vos matches de la semaine.<br/>
        <br/>
        Bonne journ�e<br/>
        <br/>
        Cordialement,<br/>
        La CTSD<br/>
        http://www.ufolep13volley.org<br/>
    </p>"""
    string_next_matches = ""
    for next_match in next_matches:
        string_next_matches = """
        %s
        <tr>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
        </tr>
        """ % (string_next_matches,
               next_match['equipe_domicile'],
               next_match['equipe_exterieur'],
               next_match['code_match'],
               next_match['date'],
               next_match['heure'],
               next_match['responsable'],
               next_match['telephone'],
               next_match['email'],
               next_match['creneaux'])
    html = """
    <html>
        <head></head>
        <body>
            %s
            <table border="1">
                <tr>
                    <th>Domicile</th>
                    <th>Ext�rieur</th>
                    <th>Code Match</th>
                    <th>Date</th>
                    <th>Heure</th>
                    <th>Responsable</th>
                    <th>T�l�phone</th>
                    <th>Email</th>
                    <th>Creneaux</th>
                </tr>
                %s
            </table>
        </body>
    </html>
    """ % (string_message, string_next_matches)
    msg.attach(MIMEText(html, 'html'))
    server.sendmail(me, recipients, msg.as_string())
    return


def email_players_without_licence_number_per_leader(players_without_licence_number_per_leader):
    me = 'noreply@ufolep13volley.org'
    recipients = [
        players_without_licence_number_per_leader['responsable'],
        'benallemand@gmail.com'
    ]
    if environment.environment is "DEV":
        recipients = ['benallemand@gmail.com']
    you = ", ".join(recipients)
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "[UFOLEP13VOLLEY]Joueurs sans num�ro de licence"
    msg['From'] = me
    msg['To'] = you
    string_message = """
    <p>
        Bonjour,<br/>
        <br/>
        Vous recevez cet email car au moins un de vos joueurs n'a pas encore son num�ro de licence renseign� sur le site de l'UFOLEP 13 VOLLEY.<br/>
        <br/>
        Merci de mettre � jour ce num�ro de licence d�s que vous le connaissez, afin que l'UFOLEP puisse activer votre joueur sur la fiche �quipe.<br/>
        <br/>
        La liste des joueurs concern�s est en pi�ce jointe.<br/>
        <br/>
        Bonne journ�e<br/>
        <br/>
        Cordialement,<br/>
        La CTSD<br/>
        http://www.ufolep13volley.org<br/>
    </p>"""
    html = """
    <html>
        <head></head>
        <body>
            %s
            <table border="1">
                <tr>
                    <th>Joueurs</th>
                    <th>Club</th>
                    <th>Equipe</th>
                    <th>Responsable</th>
                </tr>
                <tr>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                </tr>
            </table>
        </body>
    </html>
    """ % (string_message,
           players_without_licence_number_per_leader['joueurs'],
           players_without_licence_number_per_leader['club'],
           players_without_licence_number_per_leader['equipe'],
           players_without_licence_number_per_leader['responsable'])
    msg.attach(MIMEText(html, 'html'))
    server.sendmail(me, recipients, msg.as_string())
    return
