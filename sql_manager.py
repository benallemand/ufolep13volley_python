# coding=latin-1
import pymysql
import environment

if environment.environment is "DEV":
    pass
elif environment.environment is "PROD":
    pass
else:
    raise EnvironmentError("Environnement inconnu")

db = None


def sql_connect():
    global db
    db = pymysql.connect(host=environment.globSqlHost,
                         user=environment.globSqlUser,
                         passwd=environment.globSqlPassword,
                         db=environment.globSqlDbName)


def sql_update_email_sent_flag(id_user):
    global db
    sql_connect()
    cur = db.cursor()
    cur.execute("UPDATE comptes_acces SET is_email_sent = 'O' WHERE id = :id_user", id_user=id_user)
    cur.close()
    db.commit()
    db.close()
    return


def sql_get_accounts():
    global db
    sql_connect()
    cur = db.cursor()
    cur.execute("""
    SELECT
    e.nom_equipe,
    c.libelle AS competition,
    ca.login,
    ca.password,
    ca.email,
    ca.id
    FROM comptes_acces ca
    JOIN equipes e ON e.id_equipe=ca.id_equipe
    JOIN competitions c ON c.code_competition=e.code_competition
    WHERE ca.is_email_sent = 'N'
    """)
    list_result = []
    for row in cur.fetchall():
        list_result.append(
            {
                'nom_equipe': row[0],
                'competition': row[1],
                'login': row[2],
                'password': str(row[3]),
                'email': row[4],
                'id': row[5]
            }
        )
    cur.close()
    db.close()
    return list_result


def sql_get_ids_team_requesting_next_matches():
    global db
    sql_connect()
    cur = db.cursor()
    cur.execute("""
    SELECT
    REPLACE(REPLACE(registry_key, '.is_remind_matches',''), 'users.','') AS team_id
    FROM registry
    WHERE registry_key LIKE 'users.%.is_remind_matches'
    AND registry_value = 'on'
    """)
    list_result = []
    for row in cur.fetchall():
        list_result.append(row[0])
    cur.close()
    db.close()
    return list_result


def sql_get_next_matches_for_team(team_id):
    global db
    sql_connect()
    cur = db.cursor()
    cur.execute("""
    SELECT
    e1.nom_equipe AS equipe_domicile,
    e2.nom_equipe AS equipe_exterieur,
    m.code_match as code_match,
    DATE_FORMAT(m.date_reception, '%d/%m/%Y') AS date,
    cr.heure AS heure,
    CONCAT(jresp.prenom, ' ', jresp.nom) AS responsable,
    jresp.telephone,
    jresp.email,
    GROUP_CONCAT(
        CONCAT(CONCAT(g.ville, ' - ', g.nom, ' - ', g.adresse, ' - ', g.gps), ' (',cr.jour, ' à ', cr.heure,')')
        SEPARATOR ', ')
        AS creneaux
    FROM matches m
    JOIN equipes e1 ON e1.id_equipe = m.id_equipe_dom
    JOIN equipes e2 ON e2.id_equipe = m.id_equipe_ext
    LEFT JOIN creneau cr ON cr.id_equipe = e1.id_equipe AND cr.jour = ELT(WEEKDAY(m.date_reception) + 2,
                                  'Dimanche',
                                  'Lundi',
                                  'Mardi',
                                  'Mercredi',
                                  'Jeudi',
                                  'Vendredi',
                                  'Samedi')
    LEFT JOIN gymnase g ON g.id = cr.id_gymnase
    LEFT JOIN joueur_equipe jeresp ON jeresp.id_equipe=e1.id_equipe AND jeresp.is_leader+0 > 0
    LEFT JOIN joueurs jresp ON jresp.id=jeresp.id_joueur
    """ + """
    WHERE
     (m.id_equipe_dom = %s OR id_equipe_ext = %s)
     AND
    (
    m.date_reception >= CURDATE()
    AND
    m.date_reception < DATE_ADD(CURDATE(), INTERVAL 7 DAY)
    )
    GROUP BY e1.id_equipe
    ORDER BY date_reception ASC
    """ % (team_id, team_id))
    list_result = []
    for row in cur.fetchall():
        list_result.append(
            {
                'equipe_domicile': row[0],
                'equipe_exterieur': row[1],
                'code_match': row[2],
                'date': row[3],
                'heure': row[4],
                'responsable': row[5],
                'telephone': row[6],
                'email': row[7],
                'creneaux': row[8]
            }
        )
    cur.close()
    db.close()
    return list_result


def sql_get_email_from_team_id(team_id):
    global db
    sql_connect()
    cur = db.cursor()
    cur.execute("""
    SELECT j.email
    FROM joueurs j
    JOIN joueur_equipe je ON
        je.id_equipe = %(id)s
        AND je.id_joueur = j.id
        AND je.is_leader+0 > 0
    """, {
        'id': team_id
    })
    result = cur.fetchone()
    email = result[0]
    cur.close()
    db.close()
    return email


def sql_get_activity():
    global db
    sql_connect()
    cur = db.cursor()
    cur.execute("""
    SELECT
    DATE_FORMAT(a.activity_date, '%d/%m/%Y') AS date,
    e.nom_equipe,
    c.libelle AS competition,
    a.comment AS description,
    ca.login AS utilisateur,
    ca.email AS email_utilisateur
    FROM activity a
    LEFT JOIN comptes_acces ca ON ca.id=a.user_id
    LEFT JOIN equipes e ON e.id_equipe=ca.id_equipe
    LEFT JOIN competitions c ON c.code_competition=e.code_competition
    WHERE a.activity_date > DATE_SUB(NOW(), INTERVAL 2 DAY)
    ORDER BY a.id DESC""")
    list_result = []
    for row in cur.fetchall():
        list_result.append(
            {
                'date': str(row[0]),
                'nom_equipe': row[1],
                'competition': row[2],
                'description': row[3],
                'utilisateur': str(row[4]),
                'email_utilisateur': row[5]
            }
        )
    cur.close()
    db.close()
    return list_result


def sql_get_players_without_licence_number():
    global db
    sql_connect()
    cur = db.cursor()
    cur.execute("""
        SELECT
        GROUP_CONCAT(CONCAT(j.nom, ' ', j.prenom) SEPARATOR ', ') AS joueurs,
        c.nom AS club,
        CONCAT(e.nom_equipe, ' (', comp.libelle, ')') AS equipe,
        jresp.email AS responsable
        FROM joueur_equipe je
        JOIN joueurs j ON j.id = je.id_joueur
        JOIN equipes e ON e.id_equipe = je.id_equipe
        JOIN joueur_equipe jeresp ON jeresp.id_equipe = e.id_equipe AND jeresp.is_leader+0 > 0
        JOIN joueurs jresp ON jresp.id = jeresp.id_joueur
        JOIN competitions comp ON comp.code_competition = e.code_competition
        JOIN clubs c ON c.id = j.id_club
        WHERE j.num_licence = ''
        AND e.id_equipe IN (SELECT id_equipe FROM classements)
        GROUP BY jresp.email
        ORDER BY equipe ASC
    """)
    list_result = []
    for row in cur.fetchall():
        list_result.append(
            {
                'joueurs': row[0],
                'club': row[1],
                'equipe': row[2],
                'responsable': row[3]
            }
        )
    cur.close()
    db.close()
    return list_result


def activate_players(licences):
    global db
    sql_connect()
    cur = db.cursor()
    for licence in licences:
        cur.execute("""
        UPDATE joueurs SET
          est_actif = 1,
          date_homologation = STR_TO_DATE('{activation_date}', '%d/%m/%Y')
        WHERE num_licence = '{licence_number}'""".format(
            activation_date=licence['activation_date'],
            licence_number=licence['licence_number'].replace(' ','')))
    cur.close()
    db.commit()
    db.close()
    return


def sql_get_matches_not_reported():
    global db
    sql_connect()
    cur = db.cursor()
    cur.execute("""
        SELECT
        m.code_match,
        c1.nom AS club_reception,
        CONCAT(e1.nom_equipe, ' (', comp.libelle, ')') AS equipe_reception,
        jresp1.email AS responsable_reception,
        c2.nom AS club_visiteur,
        CONCAT(e2.nom_equipe, ' (', comp.libelle, ')') AS equipe_visiteur,
        jresp2.email AS responsable_visiteur,
        DATE_FORMAT(m.date_reception, '%d/%m/%Y') AS date_reception
        FROM matches m
        JOIN competitions comp ON comp.code_competition = m.code_competition
        JOIN equipes e1 ON e1.id_equipe = m.id_equipe_dom
        JOIN equipes e2 ON e2.id_equipe = m.id_equipe_ext
        JOIN joueur_equipe jeresp1 ON jeresp1.id_equipe = e1.id_equipe AND jeresp1.is_leader+0 > 0
        JOIN joueur_equipe jeresp2 ON jeresp2.id_equipe = e2.id_equipe AND jeresp2.is_leader+0 > 0
        JOIN joueurs jresp1 ON jresp1.id = jeresp1.id_joueur
        JOIN joueurs jresp2 ON jresp2.id = jeresp2.id_joueur
        JOIN clubs c1 ON c1.id = jresp1.id_club
        JOIN clubs c2 ON c2.id = jresp2.id_club
        WHERE
        (
        (m.score_equipe_dom+m.score_equipe_ext+0=0)
        OR
        ((m.set_1_dom+m.set_1_ext=0) AND (m.score_equipe_dom+m.score_equipe_ext>0))
        OR
        ((m.set_1_dom+m.set_1_ext>0) AND (m.score_equipe_dom+m.score_equipe_ext+0=0))
        )
        AND m.date_reception < CURDATE() - INTERVAL 10 DAY
        ORDER BY m.code_match ASC
    """)
    list_result = []
    for row in cur.fetchall():
        list_result.append(
            {
                'code_match': row[0],
                'club_reception': row[1],
                'equipe_reception': row[2],
                'responsable_reception': row[3],
                'club_visiteur': row[4],
                'equipe_visiteur': row[5],
                'responsable_visiteur': row[6],
                'date_reception': row[7]
            }
        )
    cur.close()
    db.close()
    return list_result


def sql_get_team_leaders_without_email():
    global db
    sql_connect()
    cur = db.cursor()
    cur.execute("""
SELECT DISTINCT
  j.prenom,
  j.nom,
  c.libelle,
  e.nom_equipe
FROM classements cl
  JOIN joueur_equipe je ON je.id_equipe = cl.id_equipe
  JOIN joueurs j ON j.id = je.id_joueur
  JOIN equipes e ON e.id_equipe = je.id_equipe
  JOIN competitions c ON c.code_competition = e.code_competition
WHERE je.is_leader + 0 > 0
      AND j.email = ''
    """)
    list_result = []
    for row in cur.fetchall():
        list_result.append(
            {
                'prenom': row[0],
                'nom': row[1],
                'competition': row[2],
                'equipe': row[3]
            }
        )
    cur.close()
    db.close()
    return list_result
