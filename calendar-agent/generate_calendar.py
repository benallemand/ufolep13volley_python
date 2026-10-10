#!/usr/bin/env python3
"""
Script de génération du calendrier UFOLEP Volleyball.

Usage:
    python generate_calendar.py                  # Génère pour coupes (c) et kh
    python generate_calendar.py c kh             # Idem
    python generate_calendar.py m f mo           # Championnats uniquement
    python generate_calendar.py c                # Coupes uniquement
    python generate_calendar.py m f mo --reference insert_matches_m_f_mo.sql
                                                 # Garde au mieux un calendrier
                                                 # déjà généré : seules bougent
                                                 # les rencontres que les
                                                 # changements de créneaux,
                                                 # d'équipes ou de fermetures
                                                 # de gymnases imposent
    python generate_calendar.py m f mo --reference insert_matches_m_f_mo.sql --temps 1200
                                                 # Laisse 20 min au solveur (5 min
                                                 # par défaut) : moins de
                                                 # rencontres déplacées par
                                                 # ricochet
"""

import sys
from ufolep_mysql_final import main

if __name__ == "__main__":
    args = sys.argv[1:]
    reference_file = None
    if '--reference' in args:
        index = args.index('--reference')
        if index + 1 >= len(args):
            sys.exit("--reference attend un fichier insert_matches_*.sql")
        reference_file = args[index + 1]
        del args[index:index + 2]
    max_time = 300.0
    if '--temps' in args:
        index = args.index('--temps')
        if index + 1 >= len(args) or not args[index + 1].isdigit():
            sys.exit("--temps attend une durée en secondes")
        max_time = float(args[index + 1])
        del args[index:index + 2]

    # Récupérer les codes de compétition depuis les arguments
    if args:
        competition_codes = args
    else:
        # Par défaut: coupes et kh
        competition_codes = ['c', 'kh']

    print(f"Génération du calendrier pour: {', '.join(competition_codes)}")
    if reference_file:
        print(f"Calendrier de référence: {reference_file}")
    print("=" * 60)

    main(competition_codes, reference_file, max_time)
