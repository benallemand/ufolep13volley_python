#!/usr/bin/env python3
"""
Script de génération du calendrier UFOLEP Volleyball.

Usage:
    python generate_calendar.py                  # Génère pour coupes (c) et kh
    python generate_calendar.py c kh             # Idem
    python generate_calendar.py m f mo           # Championnats uniquement
    python generate_calendar.py c                # Coupes uniquement
"""

import sys
from ufolep_mysql_final import main

if __name__ == "__main__":
    # Récupérer les codes de compétition depuis les arguments
    if len(sys.argv) > 1:
        competition_codes = sys.argv[1:]
    else:
        # Par défaut: coupes et kh
        competition_codes = ['c', 'kh']
    
    print(f"Génération du calendrier pour: {', '.join(competition_codes)}")
    print("=" * 60)
    
    main(competition_codes)
