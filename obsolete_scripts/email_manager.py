# coding=latin-1
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
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
    server.ehlo()
    try:
        server.starttls()
    except:
        server = smtplib.SMTP(environment.globEmailSmtp)
        server.ehlo()
        server.login(username, password)
        return
    server.login(username, password)
    return


def email_send_account_recap(account):
    me = 'noreply@ufolep13volley.org'
    msg = MIMEMultipart('alternative')
    you = account['email']
    msg['Subject'] = Header("R�capitulatif de vos identifiants Ufolep13Volley", 'latin-1')
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
    msg['Subject'] = Header("Activit�", 'latin-1')
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
    msg['Subject'] = Header("[UFOLEP13VOLLEY]Joueurs sans num�ro de licence", 'latin-1')
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


def email_send_test():
    email_login()
    me = 'noreply@ufolep13volley.org'
    msg = MIMEMultipart('alternative')
    you = "benallemand@gmail.com"
    msg['Subject'] = "Email test"
    msg['From'] = me
    msg['To'] = you
    string_message = "This is a test"
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


def email_match_not_reported(match_not_reported):
    me = 'noreply@ufolep13volley.org'
    recipients = [
        match_not_reported['responsable_reception'],
        match_not_reported['responsable_visiteur'],
        'benallemand@gmail.com'
    ]
    if environment.environment is "DEV":
        recipients = ['benallemand@gmail.com']
    you = ", ".join(recipients)
    msg = MIMEMultipart('alternative')
    msg['Subject'] = Header("[UFOLEP13VOLLEY]Saisie Internet des r�sultats", 'latin-1')
    msg['From'] = me
    msg['To'] = you
    string_message = """
    <p>
        Aux �quipes de %s et %s<br/>
        <br/>
        Comme vous avez d� le lire sur le r�glement, la saisie des informations sur le site internet doit �tre rigoureuse (pour le suivi de la commission Volley et pour l'int�r�t qu'y portent les joueurs)<br/>
        <br/>
        Pour r�sumer, sur le site, 10 jours apr�s la date indiqu�e pour le match (qui peut �tre en rouge si le match a �t� report�e), il doit y avoir un r�sultat affich�.<br/>
        <br/>
        Pour votre match du <b>%s</b> cela n'est pas le cas. Nous vous demandons donc :<br/>
        <br/>
        - soit que le r�sultat soit indiqu�<br/>
        - soit qu'une autre date de match soit affich�e (pour cela il faut la communiquer au responsable des classements)<br/>
        <br/>
        Je vous rappelle que les deux �quipes doivent veiller � ce que cette r�gle soit suivie: les deux pourraient donc �tre p�nalis�es.<br/>
        <br/>
        Bonne journ�e<br/>
        <br/>
        Cordialement,<br/>
        La CTSD<br/>
        http://www.ufolep13volley.org<br/>
    </p>""" % (
        match_not_reported['equipe_reception'],
        match_not_reported['equipe_visiteur'],
        match_not_reported['date_reception']
    )
    html = """
    <html>
        <head></head>
        <body>
            %s
        </body>
    </html>
    """ % string_message
    msg.attach(MIMEText(html, 'html'))
    server.sendmail(me, recipients, msg.as_string())
    return


def email_team_leaders_without_email(team_leaders_without_email):
    me = 'noreply@ufolep13volley.org'
    recipients = [
        'laurent.gorlier@ufolep13volley.org',
        'benallemand@gmail.com'
    ]
    you = ", ".join(recipients)
    msg = MIMEMultipart('alternative')
    msg['Subject'] = Header("Responsables d'�quipe sans adresse email", 'latin-1')
    msg['From'] = me
    msg['To'] = you
    string_message = """
    <p>
        Bonjour Laurent,<br/>
        <br/>
        Certains responsables d'�quipe n'ont pas encore renseign� leur adresse email sur le site.<br/>
        <br/>
        De ce fait il est impossible de les contacter pour une demande de report ou pour leur rappeler de saisir un r�sultat de match.<br/>
        <br/>
        Peux-tu leur rappeler de consulter les alertes lorsqu'ils se connectent au portail Ufolep 13 Volley ? Il y a d�j� une alerte qui leur indiquera la marche � suivre.<br/>
        <br/>
        Bonne journ�e<br/>
        <br/>
        Cordialement,<br/>
        La CTSD<br/>
        http://www.ufolep13volley.org<br/>
    </p>"""
    string_team_leaders_without_email = ""
    for team_leader_without_email in team_leaders_without_email:
        string_team_leaders_without_email = """
        %s
        <tr>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
        </tr>
        """ % (string_team_leaders_without_email,
               team_leader_without_email['prenom'],
               team_leader_without_email['nom'],
               team_leader_without_email['competition'],
               team_leader_without_email['equipe'])
    html = """
    <html>
        <head></head>
        <body>
            %s
            <table border="1">
                <tr>
                    <th>Pr�nom</th>
                    <th>Nom</th>
                    <th>Comp�tition</th>
                    <th>Equipe</th>
                </tr>
                %s
            </table>
        </body>
    </html>
    """ % (string_message, string_team_leaders_without_email)
    msg.attach(MIMEText(html, 'html'))
    server.sendmail(me, recipients, msg.as_string())
    return
