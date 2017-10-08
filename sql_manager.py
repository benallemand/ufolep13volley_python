# coding=latin-1
import os

import MySQLdb
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
    db = MySQLdb.connect(host=environment.globSqlHost,
                         user=environment.globSqlUser,
                         passwd=environment.globSqlPassword,
                         db=environment.globSqlDbName)


def activate_players(licences):
    global db
    sql_connect()
    cur = db.cursor()
    current = 0
    for licence in licences:
        current += 1
        print "Activating licence %s/%s, licence number %s with validation date at %s..." % (
            current,
            len(licences),
            licence['licence_number'],
            licence['activation_date']
        )
        cur.execute("""
        UPDATE joueurs SET
          est_actif = 1,
          date_homologation = STR_TO_DATE('{activation_date}', '%d/%m/%Y')
        WHERE num_licence = '{licence_number}'""".format(
            activation_date=licence['activation_date'],
            licence_number=licence['licence_number'].replace(' ', '')))
    cur.close()
    db.commit()
    db.close()
    return


def sql_get_unused_photo_paths():
    global db
    sql_connect()
    cur = db.cursor()
    cur.execute("""
    SELECT
      p.path_photo,
      p.id
    FROM photos p
      LEFT JOIN equipes e ON e.id_photo = p.id
      LEFT JOIN joueurs j ON j.id_photo = p.id
    WHERE e.id_photo IS NULL AND j.id_photo IS NULL
    ORDER BY p.path_photo ASC
        """)
    list_result = []
    for row in cur.fetchall():
        list_result.append(
            {
                'path_photo': row[0],
                'id': int(row[1])
            }
        )
    cur.close()
    db.close()
    return list_result


def delete_photo(id_photo=None):
    global db
    sql_connect()
    cur = db.cursor()
    cur.execute("DELETE FROM photos WHERE id = %(id_photo)s", {
        'id_photo': id_photo
    })
    cur.close()
    db.commit()
    db.close()
    return


def is_photo_path_in_database(photo_path):
    global db
    sql_connect()
    cur = db.cursor()
    cur.execute("""
        SELECT
          p.path_photo
        FROM photos p
        WHERE p.path_photo = '{photo_path}'
            """.format(photo_path=photo_path.replace(os.path.sep, '/')))
    list_result = []
    for row in cur.fetchall():
        list_result.append(
            {
                'path_photo': row[0]
            }
        )
    cur.close()
    db.close()
    return len(list_result) > 0
