#!/usr/bin/env python3
"""Script pour vérifier les équipes par division."""

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

    # Identifier les équipes 20 et 532 (match non programmé)
    query = """
    SELECT e.id_equipe, e.nom_equipe
    FROM equipes e
    WHERE e.id_equipe IN (20, 532)
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    print("Match non programme (m/1):")
    print("=" * 60)
    for row in rows:
        print(f"ID {row['id_equipe']}: {row['nom_equipe']}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
