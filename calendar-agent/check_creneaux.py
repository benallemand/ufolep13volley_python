#!/usr/bin/env python3
"""Script de vérification des créneaux: compare register vs table creneau."""

import mysql.connector

def main():
    conn = mysql.connector.connect(
        host='localhost',
        port=3306,
        database='ufolep_13volley',
        user='root',
        password='test'
    )
    cursor = conn.cursor(dictionary=True)

    # Requête pour comparer register vs creneau pour m, f, mo
    query = """
    SELECT comp_enfant.libelle AS competition,
           'REGISTER' AS source,
           r.new_team_name AS equipe,
           g1.nom AS gymnase_register,
           r.day_court_1 AS jour_register,
           r.hour_court_1 AS heure_register,
           g2.nom AS gymnase_creneau,
           cr.jour AS jour_creneau,
           cr.heure AS heure_creneau,
           CASE
               WHEN cr.id IS NULL THEN 'ABSENT dans creneau'
               WHEN r.id_court_1 != cr.id_gymnase THEN 'GYMNASE different'
               WHEN r.day_court_1 != cr.jour THEN 'JOUR different'
               WHEN COALESCE(r.hour_court_1, '20:00') != cr.heure THEN 'HEURE differente'
               ELSE 'OK'
           END AS ecart
    FROM register r
    JOIN competitions comp_parent ON comp_parent.id = r.id_competition
    JOIN competitions comp_enfant ON comp_enfant.id_compet_maitre = comp_parent.code_competition
    JOIN equipes e ON (r.old_team_id IS NOT NULL AND e.id_equipe = r.old_team_id) 
                   OR (r.old_team_id IS NULL AND e.nom_equipe = r.new_team_name)
    JOIN classements cl ON cl.id_equipe = e.id_equipe AND cl.code_competition = comp_enfant.code_competition
    LEFT JOIN gymnase g1 ON g1.id = r.id_court_1
    LEFT JOIN creneau cr ON cr.id_equipe = e.id_equipe AND cr.usage_priority = 1
    LEFT JOIN gymnase g2 ON g2.id = cr.id_gymnase
    WHERE r.id_court_1 IS NOT NULL
      AND comp_enfant.code_competition IN ('m', 'f', 'mo')
      AND (
        cr.id IS NULL
        OR r.id_court_1 != cr.id_gymnase
        OR r.day_court_1 != cr.jour
        OR COALESCE(r.hour_court_1, '20:00') != cr.heure
      )
    ORDER BY competition, equipe
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    if rows:
        print(f"ECARTS TROUVES: {len(rows)} lignes")
        print("=" * 100)
        for row in rows:
            print(f"{row['competition']:15} | {row['equipe']:30} | {row['ecart']}")
            print(f"   Register: {row['gymnase_register']} - {row['jour_register']} {row['heure_register']}")
            print(f"   Creneau:  {row['gymnase_creneau']} - {row['jour_creneau']} {row['heure_creneau']}")
            print()
    else:
        print("Aucun ecart trouve pour le creneau 1 - les creneaux sont synchronises!")

    # Vérifier aussi le créneau 2
    query2 = """
    SELECT comp_enfant.libelle AS competition,
           r.new_team_name AS equipe,
           g1.nom AS gymnase_register,
           r.day_court_2 AS jour_register,
           r.hour_court_2 AS heure_register,
           g2.nom AS gymnase_creneau,
           cr.jour AS jour_creneau,
           cr.heure AS heure_creneau,
           CASE
               WHEN cr.id IS NULL THEN 'ABSENT dans creneau'
               WHEN r.id_court_2 != cr.id_gymnase THEN 'GYMNASE different'
               WHEN r.day_court_2 != cr.jour THEN 'JOUR different'
               WHEN COALESCE(r.hour_court_2, '20:00') != cr.heure THEN 'HEURE differente'
               ELSE 'OK'
           END AS ecart
    FROM register r
    JOIN competitions comp_parent ON comp_parent.id = r.id_competition
    JOIN competitions comp_enfant ON comp_enfant.id_compet_maitre = comp_parent.code_competition
    JOIN equipes e ON (r.old_team_id IS NOT NULL AND e.id_equipe = r.old_team_id) 
                   OR (r.old_team_id IS NULL AND e.nom_equipe = r.new_team_name)
    JOIN classements cl ON cl.id_equipe = e.id_equipe AND cl.code_competition = comp_enfant.code_competition
    LEFT JOIN gymnase g1 ON g1.id = r.id_court_2
    LEFT JOIN creneau cr ON cr.id_equipe = e.id_equipe AND cr.usage_priority = 2
    LEFT JOIN gymnase g2 ON g2.id = cr.id_gymnase
    WHERE r.id_court_2 IS NOT NULL
      AND comp_enfant.code_competition IN ('m', 'f', 'mo')
      AND (
        cr.id IS NULL
        OR r.id_court_2 != cr.id_gymnase
        OR r.day_court_2 != cr.jour
        OR COALESCE(r.hour_court_2, '20:00') != cr.heure
      )
    ORDER BY competition, equipe
    """

    cursor.execute(query2)
    rows2 = cursor.fetchall()

    if rows2:
        print(f"\nECARTS CRENEAU 2: {len(rows2)} lignes")
        print("=" * 100)
        for row in rows2:
            print(f"{row['competition']:15} | {row['equipe']:30} | {row['ecart']}")
            print(f"   Register: {row['gymnase_register']} - {row['jour_register']} {row['heure_register']}")
            print(f"   Creneau:  {row['gymnase_creneau']} - {row['jour_creneau']} {row['heure_creneau']}")
            print()
    else:
        print("\nAucun ecart trouve pour le creneau 2")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
