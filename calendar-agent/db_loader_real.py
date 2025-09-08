# -*- coding: utf-8 -*-
"""
Module de chargement des données UFOLEP depuis MySQL - Structure réelle.
Adapté à votre vraie structure avec table classements et créneaux par équipe.
"""

import mysql.connector
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, time
from db_config import DB_CONFIG


@dataclass
class ClubData:
    """Données d'un club depuis la BDD."""
    id: str
    nom: str
    affiliation_number: str
    email_responsable: str
    equipes: List['EquipeData']


@dataclass
class GymnaseData:
    """Données d'un gymnase depuis la BDD (indépendant des clubs)."""
    id: str
    nom: str
    adresse: str
    nb_terrains: int


@dataclass
class CreneauData:
    """Données d'un créneau depuis la BDD (appartient à une équipe)."""
    id: str
    equipe_id: str
    gymnase_id: str
    jour_semaine: int  # 1=Lundi, 2=Mardi, etc.
    heure_debut: time


@dataclass
class ClassementData:
    """Données de classement (liaison équipe-division)."""
    id: str
    code_competition: str  # M, F, MIXTE
    division: int  # 1,2,3,4...
    id_equipe: str


@dataclass
class EquipeData:
    """Données d'une équipe depuis la BDD."""
    id: str
    nom: str
    club_id: str
    classement: Optional[ClassementData]
    creneaux: List[CreneauData]


@dataclass
class DivisionVirtuelle:
    """Division reconstituée depuis les classements."""
    id: str  # ex: "M_1", "F_2", "MIXTE_3"
    nom: str  # ex: "Division Masculine 1"
    code_competition: str  # M, F, MIXTE
    division: int  # 1,2,3,4...
    equipes: List[str]  # IDs des équipes


class UfolepDatabaseLoader:
    """Chargeur de données UFOLEP depuis MySQL adapté à la structure réelle."""
    
    def __init__(self):
        self.connection = None
        self.clubs = {}
        self.gymnases = {}
        self.creneaux = {}
        self.classements = {}
        self.equipes = {}
        self.divisions_virtuelles = {}
    
    def connect(self) -> bool:
        """Établit la connexion à la base de données."""
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            print(f"[OK] Connexion reussie a la base {DB_CONFIG['database']}")
            return True
        except mysql.connector.Error as err:
            print(f"[ERREUR] Erreur de connexion MySQL: {err}")
            return False
    
    def disconnect(self):
        """Ferme la connexion à la base de données."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("[INFO] Connexion MySQL fermee")
    
    def load_all_data(self) -> bool:
        """Charge toutes les données nécessaires depuis la BDD."""
        if not self.connect():
            return False
        
        try:
            print("[INFO] Chargement des donnees UFOLEP reelles...")
            
            # Charger dans l'ordre des dépendances
            self._load_clubs()
            self._load_gymnases()
            self._load_equipes()
            self._load_classements()
            self._load_creneaux()
            
            # Reconstruire les divisions virtuelles
            self._build_virtual_divisions()
            
            # Associer les données
            self._associate_data()
            
            print("[OK] Toutes les donnees chargees avec succes")
            return True
            
        except Exception as e:
            print(f"[ERREUR] Erreur lors du chargement: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.disconnect()
    
    def _load_clubs(self):
        """Charge les clubs depuis la BDD."""
        cursor = self.connection.cursor(dictionary=True)
        
        query = """
        SELECT  c.id, 
                c.nom,
                c.affiliation_number,
                c.email_responsable 
        FROM clubs c
        JOIN equipes e ON e.id_club = c.id
        JOIN classements cl ON cl.id_equipe = e.id_equipe
        WHERE cl.code_competition in ('m', 'f', 'mo')
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()

        for row in rows:
            club = ClubData(
                id=str(row['id']),
                nom=row['nom'],
                affiliation_number=row['affiliation_number'] or '',
                email_responsable=row['email_responsable'] or '',
                equipes=[]
            )
            self.clubs[club.id] = club
        
        cursor.close()
        print(f"[INFO] {len(self.clubs)} clubs charges")
    
    def _load_gymnases(self):
        """Charge les gymnases depuis la BDD."""
        cursor = self.connection.cursor(dictionary=True)
        
        query = """
        SELECT DISTINCT 
            g.id,
            g.nom,
            g.adresse,
            g.nb_terrain as nb_terrains
        FROM gymnase g
        JOIN ufolep_13volley.creneau c on g.id = c.id_gymnase
        JOIN ufolep_13volley.classements cl on c.id_equipe = cl.id_equipe
        WHERE cl.code_competition in ('m', 'f', 'mo')
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            gymnase = GymnaseData(
                id=str(row['id']),
                nom=row['nom'],
                adresse=row['adresse'] or '',
                nb_terrains=int(row['nb_terrains']) if row['nb_terrains'] else 1
            )
            self.gymnases[gymnase.id] = gymnase
        
        cursor.close()
        print(f"[INFO] {len(self.gymnases)} gymnases charges")
    
    def _load_equipes(self):
        """Charge les équipes depuis la BDD."""
        cursor = self.connection.cursor(dictionary=True)
        
        query = """
        SELECT DISTINCT
        e.id_equipe as id,
        e.nom_equipe as nom,
        e.id_club as club_id
        FROM equipes e
        JOIN ufolep_13volley.classements cl on e.id_equipe = cl.id_equipe
        WHERE cl.code_competition in ('m', 'f', 'mo')  
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            equipe = EquipeData(
                id=str(row['id']),
                nom=row['nom'],
                club_id=str(row['club_id']),
                classement=None,
                creneaux=[]
            )
            self.equipes[equipe.id] = equipe
        
        cursor.close()
        print(f"[INFO] {len(self.equipes)} equipes chargees")
    
    def _load_classements(self):
        """Charge les classements (liaison équipes-divisions) depuis la BDD."""
        cursor = self.connection.cursor(dictionary=True)
        
        query = """
        SELECT DISTINCT 
            id,
            code_competition,
            division,
            id_equipe
        FROM classements
        WHERE code_competition IN ('m', 'f', 'mo')
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            classement = ClassementData(
                id=str(row['id']),
                code_competition=row['code_competition'],
                division=int(row['division']),
                id_equipe=str(row['id_equipe'])
            )
            self.classements[classement.id] = classement
            
            # Associer le classement à l'équipe
            if classement.id_equipe in self.equipes:
                self.equipes[classement.id_equipe].classement = classement
        
        cursor.close()
        print(f"[INFO] {len(self.classements)} classements charges")
    
    def _load_creneaux(self):
        """Charge les créneaux depuis la BDD."""
        cursor = self.connection.cursor(dictionary=True)
        
        query = """
        SELECT DISTINCT
            c.id as id,
            c.id_equipe as equipe_id,
            c.id_gymnase as gymnase_id,
            c.jour as jour_semaine,
            c.heure as heure_debut
        FROM creneau c
        JOIN classements cl ON cl.id_equipe = c.id_equipe 
        WHERE cl.code_competition IN ('m', 'f', 'mo')
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            # Convertir l'heure si nécessaire
            heure_debut = row['heure_debut']
            if isinstance(heure_debut, str):
                # Essayer d'abord HH:MM:SS, puis HH:MM
                try:
                    heure_debut = datetime.strptime(heure_debut, '%H:%M:%S').time()
                except ValueError:
                    heure_debut = datetime.strptime(heure_debut, '%H:%M').time()
            elif isinstance(heure_debut, datetime):
                heure_debut = heure_debut.time()
            
            # Convertir le jour de la semaine (nom -> numéro)
            jour_raw = row['jour_semaine']
            if isinstance(jour_raw, str):
                # Mapping nom de jour -> numéro (1=Lundi, 7=Dimanche)
                jours_mapping = {
                    'Lundi': 1, 'Mardi': 2, 'Mercredi': 3, 'Jeudi': 4, 
                    'Vendredi': 5, 'Samedi': 6, 'Dimanche': 7
                }
                jour_semaine = jours_mapping.get(jour_raw, 1)  # Default à Lundi si inconnu
            else:
                jour_semaine = int(jour_raw)
            
            creneau = CreneauData(
                id=str(row['id']),
                equipe_id=str(row['equipe_id']),
                gymnase_id=str(row['gymnase_id']),
                jour_semaine=jour_semaine,
                heure_debut=heure_debut
            )
            self.creneaux[creneau.id] = creneau
        
        cursor.close()
        print(f"[INFO] {len(self.creneaux)} creneaux charges")
    
    def _build_virtual_divisions(self):
        """Reconstruit les divisions à partir des classements."""
        divisions_map = {}
        
        for classement in self.classements.values():
            # Créer une clé unique pour chaque division
            div_key = f"{classement.code_competition}_{classement.division}"
            
            if div_key not in divisions_map:
                divisions_map[div_key] = {
                    'code_competition': classement.code_competition,
                    'division': classement.division,
                    'equipes': []
                }
            
            divisions_map[div_key]['equipes'].append(classement.id_equipe)
        
        # Créer les objets DivisionVirtuelle
        for div_key, div_data in divisions_map.items():
            division = DivisionVirtuelle(
                id=div_key,
                nom=f"Division {div_data['code_competition']} {div_data['division']}",
                code_competition=div_data['code_competition'],
                division=div_data['division'],
                equipes=div_data['equipes']
            )
            self.divisions_virtuelles[div_key] = division
        
        print(f"[INFO] {len(self.divisions_virtuelles)} divisions virtuelles creees")
    
    def _associate_data(self):
        """Associe les données entre elles (relations) et filtre les équipes."""
        # Filtrer les équipes pour ne garder que celles avec classement 'm', 'f', 'mo'
        equipes_valides = {}
        for equipe in self.equipes.values():
            if (equipe.classement and 
                equipe.classement.code_competition in ['m', 'f', 'mo']):
                equipes_valides[equipe.id] = equipe
        
        # Remplacer la liste des équipes par les équipes filtrées
        self.equipes = equipes_valides
        
        # Associer créneaux aux équipes (seulement les équipes valides)
        for creneau in self.creneaux.values():
            if creneau.equipe_id in self.equipes:
                self.equipes[creneau.equipe_id].creneaux.append(creneau)
        
        # Associer équipes aux clubs (seulement les équipes valides)
        for club in self.clubs.values():
            club.equipes = []  # Réinitialiser
        
        for equipe in self.equipes.values():
            if equipe.club_id in self.clubs:
                self.clubs[equipe.club_id].equipes.append(equipe)
    
    def get_summary(self) -> Dict:
        """Retourne un résumé des données chargées."""
        # Compter les créneaux par gymnase
        creneaux_par_gymnase = {}
        for creneau in self.creneaux.values():
            gym_id = creneau.gymnase_id
            if gym_id not in creneaux_par_gymnase:
                creneaux_par_gymnase[gym_id] = 0
            creneaux_par_gymnase[gym_id] += 1
        
        # Compter les divisions par type
        divisions_by_type = {}
        for div in self.divisions_virtuelles.values():
            champ = div.code_competition
            if champ not in divisions_by_type:
                divisions_by_type[champ] = 0
            divisions_by_type[champ] += 1
        
        # Compter les équipes par division
        equipes_par_division = {}
        for div in self.divisions_virtuelles.values():
            equipes_par_division[div.nom] = len(div.equipes)
        
        return {
            'clubs': len(self.clubs),
            'gymnases': len(self.gymnases),
            'creneaux_total': len(self.creneaux),
            'creneaux_par_gymnase': creneaux_par_gymnase,
            'divisions': len(self.divisions_virtuelles),
            'divisions_par_type': divisions_by_type,
            'equipes': len(self.equipes),
            'equipes_par_division': equipes_par_division,
            'classements': len(self.classements)
        }
    
    def get_divisions_with_enough_teams(self, min_teams: int = 3) -> List[DivisionVirtuelle]:
        """Retourne les divisions ayant au moins min_teams équipes."""
        valid_divisions = []
        for division in self.divisions_virtuelles.values():
            if len(division.equipes) >= min_teams:
                valid_divisions.append(division)
        return valid_divisions


def test_connection():
    """Teste la connexion à la base de données."""
    loader = UfolepDatabaseLoader()
    if loader.connect():
        print("[OK] Test de connexion reussi")
        loader.disconnect()
        return True
    else:
        print("[ERREUR] Test de connexion echoue")
        return False


def test_data_loading():
    """Teste le chargement complet des données."""
    loader = UfolepDatabaseLoader()
    if loader.load_all_data():
        summary = loader.get_summary()
        print("\n[INFO] Resume des donnees chargees:")
        for key, value in summary.items():
            print(f"  - {key}: {value}")
        
        # Afficher les divisions valides
        valid_divisions = loader.get_divisions_with_enough_teams(3)
        print(f"\n[INFO] Divisions avec au moins 3 equipes: {len(valid_divisions)}")
        for div in valid_divisions:
            print(f"  - {div.nom}: {len(div.equipes)} équipes")
        
        return True
    else:
        return False


if __name__ == "__main__":
    print("Test de connexion MySQL...")
    if test_connection():
        print("\nTest de chargement des données...")
        test_data_loading()
