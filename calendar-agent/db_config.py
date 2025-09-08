# -*- coding: utf-8 -*-
"""
Configuration de la base de données MySQL UFOLEP.
Modifiez ces paramètres selon votre environnement.
"""

# Configuration de connexion MySQL
DB_CONFIG = {
    'host': 'localhost',  # Adresse de votre serveur MySQL
    'port': 3306,         # Port MySQL (généralement 3306)
    'database': 'ufolep_13volley',  # Nom de votre base de données
    'user': 'root',          # Votre nom d'utilisateur MySQL
    'password': 'test',      # Votre mot de passe MySQL
    'charset': 'utf8mb4',
    'autocommit': True
}

# Noms des tables dans votre base de données
# Modifiez selon vos noms de tables réels
TABLE_NAMES = {
    'clubs': 'clubs',
    'equipes': 'equipes', 
    'gymnases': 'gymnase',
    'creneaux': 'creneau',
    'classements': 'classements',  # Table de liaison équipes ↔ divisions
    'matchs': 'matches'  # Table où seront insérés les matchs générés
}

# Mapping des colonnes (adaptez selon votre structure)
COLUMN_MAPPING = {
    'clubs': {
        'id': 'id',
        'nom': 'nom',
        'adresse': 'affiliation_number',
        'contact': 'email_responsable'
    },
    'equipes': {
        'id': 'id_equipe',
        'nom': 'nom_equipe',
        'club_id': 'id_club',
        # 'division_id': 'division_id'
    },
    'classements': {
        'id': 'id',
        'code_competition': 'code_competition',
        'division': 'division',  # 1,2,3,4...
        'id_equipe': 'id_equipe'
    },
    'gymnases': {
        'id': 'id',
        'nom': 'nom',
        'adresse': 'adresse',
        'nb_terrains': 'nb_terrain'  # Nombre de terrains disponibles
    },
    'creneaux': {
        'id': 'id',
        'equipe_id': 'id_equipe',  # Créneau appartient à une équipe
        'gymnase_id': 'id_gymnase',
        'jour_semaine': 'jour',  # 1=Lundi, 2=Mardi, etc.
        'heure_debut': 'heure'
    },
    'matches': {
        'id_match': 'id_match',
        'code_match': 'code_match',
        'code_competition': 'code_competition',
        'division': 'division',
        'id_equipe_dom': 'id_equipe_dom',
        'id_equipe_ext': 'id_equipe_ext',
        'date_reception': 'date_reception',
        'match_status': 'match_status',
        'id_gymnasium': 'id_gymnasium'
    }
}
