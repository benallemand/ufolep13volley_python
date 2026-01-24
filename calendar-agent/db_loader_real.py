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
    lat: float = None
    lng: float = None


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
    code_competition: str
    division: str  # Peut contenir des lettres comme '7a'
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
    id: str  # ex: "M_1", "F_2a", "MIXTE_3b"
    nom: str  # ex: "Division Masculine 1A"
    code_competition: str  # M, F, MIXTE
    division: str  # Peut contenir des lettres comme '7a', '7b', etc.
    equipes: List[str]  # IDs des équipes


@dataclass
class CompetitionDates:
    """Dates d'une compétition."""
    code_competition: str
    start_date: 'date'
    end_date: 'date'


class UfolepDatabaseLoader:
    """Chargeur de données UFOLEP depuis MySQL adapté à la structure réelle."""
    
    def __init__(self, competition_codes: List[str] = None):
        """Initialise le loader.
        
        Args:
            competition_codes: Liste des codes de compétition à charger (ex: ['m', 'f', 'mo', 'c'])
                              Par défaut: ['m', 'f', 'mo']
        """
        self.connection = None
        self.competition_codes = competition_codes or ['m', 'f', 'mo']
        self.clubs = {}
        self.gymnases = {}
        self.creneaux = {}
        self.classements = {}
        self.equipes = {}
        self.divisions_virtuelles = {}
        self.competition_dates = {}
        self.historique_deplacements = {}  # {(equipe1_id, equipe2_id): {'equipe1_dom': n, 'equipe2_dom': n}}
        self.equipes_joueurs = {}  # {equipe_id: set(joueur_ids)}
        self.equipes_effectif_commun = []  # Liste de tuples (equipe1_id, equipe2_id, nb_joueurs_communs, ratio)
    
    def _get_competition_filter(self) -> str:
        """Retourne la clause SQL pour filtrer par code_competition."""
        codes_str = ", ".join(f"'{c}'" for c in self.competition_codes)
        return f"({codes_str})"
    
    def _parse_gps(self, gps_str: str) -> tuple:
        """Parse une chaîne GPS 'lat,lng' en tuple (lat, lng)."""
        if not gps_str:
            return None, None
        try:
            parts = gps_str.split(',')
            if len(parts) == 2:
                return float(parts[0].strip()), float(parts[1].strip())
        except (ValueError, AttributeError):
            pass
        return None, None
    
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
            self._load_competition_dates()
            
            # Reconstruire les divisions virtuelles
            self._build_virtual_divisions()
            
            # Associer les données
            self._associate_data()
            
            # Charger l'historique des déplacements
            self._load_historique_deplacements()
            
            # Charger les effectifs d'équipes et calculer les chevauchements
            self._load_equipes_joueurs()
            self._calculate_effectif_commun()
            
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
        
        comp_filter = self._get_competition_filter()
        query = f"""
        SELECT  c.id, 
                c.nom,
                c.affiliation_number,
                c.email_responsable 
        FROM clubs c
        JOIN equipes e ON e.id_club = c.id
        JOIN classements cl ON cl.id_equipe = e.id_equipe
        WHERE cl.code_competition in {comp_filter}
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
        """Charge les gymnases depuis la BDD.
        
        Pour 'kh': charge aussi depuis register (inscriptions kh)
        Pour 'c' et autres: charge depuis creneau
        """
        cursor = self.connection.cursor(dictionary=True)
        
        # Charger gymnases depuis table creneau (pour 'm', 'f', 'mo', 'c')
        classic_codes = [c for c in self.competition_codes if c != 'kh']
        if classic_codes:
            comp_filter = "('" + "', '".join(classic_codes) + "')"
            query = f"""
            SELECT DISTINCT 
                g.id,
                g.nom,
                g.adresse,
                g.nb_terrain as nb_terrains,
                g.gps
            FROM gymnase g
            JOIN ufolep_13volley.creneau c on g.id = c.id_gymnase
            JOIN ufolep_13volley.classements cl on c.id_equipe = cl.id_equipe
            WHERE cl.code_competition in {comp_filter}
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                lat, lng = self._parse_gps(row.get('gps'))
                gymnase = GymnaseData(
                    id=str(row['id']),
                    nom=row['nom'],
                    adresse=row['adresse'] or '',
                    nb_terrains=int(row['nb_terrains']) if row['nb_terrains'] else 1,
                    lat=lat,
                    lng=lng
                )
                self.gymnases[gymnase.id] = gymnase
        
        # Charger gymnases depuis table register (pour 'kh')
        if 'kh' in self.competition_codes:
            query_kh = """
            SELECT DISTINCT 
                g.id,
                g.nom,
                g.adresse,
                g.nb_terrain as nb_terrains,
                g.gps
            FROM gymnase g
            WHERE g.id IN (
                SELECT DISTINCT r.id_court_1 FROM register r WHERE r.id_competition = 18 AND r.id_court_1 IS NOT NULL
                UNION
                SELECT DISTINCT r.id_court_2 FROM register r WHERE r.id_competition = 18 AND r.id_court_2 IS NOT NULL
            )
            """
            cursor.execute(query_kh)
            rows_kh = cursor.fetchall()
            
            for row in rows_kh:
                if str(row['id']) not in self.gymnases:
                    lat, lng = self._parse_gps(row.get('gps'))
                    gymnase = GymnaseData(
                        id=str(row['id']),
                        nom=row['nom'],
                        adresse=row['adresse'] or '',
                        nb_terrains=int(row['nb_terrains']) if row['nb_terrains'] else 1,
                        lat=lat,
                        lng=lng
                    )
                    self.gymnases[gymnase.id] = gymnase
        
        cursor.close()
        print(f"[INFO] {len(self.gymnases)} gymnases charges")
    
    def _load_equipes(self):
        """Charge les équipes depuis la BDD."""
        cursor = self.connection.cursor(dictionary=True)
        
        comp_filter = self._get_competition_filter()
        query = f"""
        SELECT DISTINCT
        e.id_equipe as id,
        e.nom_equipe as nom,
        e.id_club as club_id
        FROM equipes e
        JOIN ufolep_13volley.classements cl on e.id_equipe = cl.id_equipe
        WHERE cl.code_competition in {comp_filter}  
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
        
        comp_filter = self._get_competition_filter()
        query = f"""
        SELECT DISTINCT 
            id,
            code_competition,
            division,
            id_equipe
        FROM classements
        WHERE code_competition IN {comp_filter}
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            classement = ClassementData(
                id=str(row['id']),
                code_competition=row['code_competition'],
                division=str(row['division']),  # Conversion en chaîne au lieu de int
                id_equipe=str(row['id_equipe'])
            )
            self.classements[classement.id] = classement
            
            # Associer le classement à l'équipe
            # Prioriser les divisions non-exclues (6, 7) sur les divisions exclues (7d, 7o)
            DIVISIONS_EXCLUES = ['7d', '7o']
            if classement.id_equipe in self.equipes:
                existing = self.equipes[classement.id_equipe].classement
                if existing is None:
                    self.equipes[classement.id_equipe].classement = classement
                elif existing.division in DIVISIONS_EXCLUES and classement.division not in DIVISIONS_EXCLUES:
                    # Remplacer un classement exclu par un non-exclu
                    self.equipes[classement.id_equipe].classement = classement
                # Sinon garder l'existant (ne pas écraser un non-exclu par un exclu)
        
        cursor.close()
        print(f"[INFO] {len(self.classements)} classements charges")
    
    def _load_creneaux(self):
        """Charge les créneaux depuis la BDD.
        
        Logique spéciale par compétition:
        - 'kh': créneaux depuis table 'register' (inscriptions kh)
        - 'c': créneaux des équipes 'm' avec is_cup_registered=1 (depuis table 'creneau')
        - 'm', 'f', 'mo': créneaux depuis table 'creneau'
        """
        cursor = self.connection.cursor(dictionary=True)
        creneau_id = 0
        
        # Mapping jour de la semaine (nom -> numéro)
        jours_mapping = {
            'Lundi': 1, 'Mardi': 2, 'Mercredi': 3, 'Jeudi': 4, 
            'Vendredi': 5, 'Samedi': 6, 'Dimanche': 7
        }
        
        # Charger créneaux pour 'kh' depuis table register
        if 'kh' in self.competition_codes:
            print("[INFO] Chargement créneaux 'kh' depuis table register...")
            query_kh = """
            SELECT 
                r.new_team_name,
                e.id_equipe as equipe_id,
                r.id_court_1 as gymnase_id_1,
                r.day_court_1 as jour_1,
                r.hour_court_1 as heure_1,
                r.id_court_2 as gymnase_id_2,
                r.day_court_2 as jour_2,
                r.hour_court_2 as heure_2
            FROM register r
            JOIN equipes e ON e.nom_equipe = r.new_team_name
            WHERE r.id_competition = 18
            """
            cursor.execute(query_kh)
            rows_kh = cursor.fetchall()
            
            # Heure par défaut si non spécifiée
            from datetime import time as dt_time
            heure_defaut = dt_time(20, 0)  # 20:00 par défaut
            
            for row in rows_kh:
                equipe_id = str(row['equipe_id'])
                
                # Créneau 1 (prioritaire)
                if row['gymnase_id_1'] and row['jour_1']:
                    heure_1 = self._parse_heure(row['heure_1']) or heure_defaut
                    jour_1 = jours_mapping.get(row['jour_1'], 1)
                    creneau_id += 1
                    creneau = CreneauData(
                        id=f"reg_kh_{creneau_id}",
                        equipe_id=equipe_id,
                        gymnase_id=str(row['gymnase_id_1']),
                        jour_semaine=jour_1,
                        heure_debut=heure_1
                    )
                    self.creneaux[creneau.id] = creneau
                
                # Créneau 2 (secondaire)
                if row['gymnase_id_2'] and row['jour_2']:
                    heure_2 = self._parse_heure(row['heure_2']) or heure_defaut
                    jour_2 = jours_mapping.get(row['jour_2'], 1)
                    creneau_id += 1
                    creneau = CreneauData(
                        id=f"reg_kh_{creneau_id}",
                        equipe_id=equipe_id,
                        gymnase_id=str(row['gymnase_id_2']),
                        jour_semaine=jour_2,
                        heure_debut=heure_2
                    )
                    self.creneaux[creneau.id] = creneau
            
            print(f"[INFO] {len([c for c in self.creneaux if c.startswith('reg_kh')])} créneaux 'kh' chargés depuis register")
        
        # Charger créneaux pour 'c' depuis table creneau (équipes 'm' avec is_cup_registered=1)
        if 'c' in self.competition_codes:
            print("[INFO] Chargement créneaux 'c' depuis équipes 'm' inscrites à la coupe...")
            query_c = """
            SELECT DISTINCT
                c.id as id,
                c.id_equipe as equipe_id,
                c.id_gymnase as gymnase_id,
                c.jour as jour_semaine,
                c.heure as heure_debut
            FROM creneau c
            JOIN classements cl ON cl.id_equipe = c.id_equipe 
            JOIN equipes e ON e.id_equipe = c.id_equipe
            WHERE cl.code_competition = 'm'
            AND e.is_cup_registered = 1
            """
            cursor.execute(query_c)
            rows_c = cursor.fetchall()
            
            for row in rows_c:
                heure_debut = self._parse_heure(row['heure_debut'])
                jour_raw = row['jour_semaine']
                if isinstance(jour_raw, str):
                    jour_semaine = jours_mapping.get(jour_raw, 1)
                else:
                    jour_semaine = int(jour_raw) if jour_raw else 1
                
                if heure_debut:
                    creneau = CreneauData(
                        id=f"cup_c_{row['id']}",
                        equipe_id=str(row['equipe_id']),
                        gymnase_id=str(row['gymnase_id']),
                        jour_semaine=jour_semaine,
                        heure_debut=heure_debut
                    )
                    self.creneaux[creneau.id] = creneau
            
            print(f"[INFO] {len([c for c in self.creneaux if c.startswith('cup_c')])} créneaux 'c' chargés")
        
        # Charger créneaux pour 'm', 'f', 'mo' depuis table creneau (méthode classique)
        classic_codes = [c for c in self.competition_codes if c in ('m', 'f', 'mo')]
        if classic_codes:
            comp_filter = "('" + "', '".join(classic_codes) + "')"
            print(f"[INFO] Chargement créneaux classiques pour {classic_codes}...")
            query_classic = f"""
            SELECT DISTINCT
                c.id as id,
                c.id_equipe as equipe_id,
                c.id_gymnase as gymnase_id,
                c.jour as jour_semaine,
                c.heure as heure_debut
            FROM creneau c
            JOIN classements cl ON cl.id_equipe = c.id_equipe 
            WHERE cl.code_competition IN {comp_filter}
            """
            cursor.execute(query_classic)
            rows_classic = cursor.fetchall()
            
            for row in rows_classic:
                heure_debut = self._parse_heure(row['heure_debut'])
                jour_raw = row['jour_semaine']
                if isinstance(jour_raw, str):
                    jour_semaine = jours_mapping.get(jour_raw, 1)
                else:
                    jour_semaine = int(jour_raw) if jour_raw else 1
                
                if heure_debut:
                    creneau = CreneauData(
                        id=str(row['id']),
                        equipe_id=str(row['equipe_id']),
                        gymnase_id=str(row['gymnase_id']),
                        jour_semaine=jour_semaine,
                        heure_debut=heure_debut
                    )
                    self.creneaux[creneau.id] = creneau
        
        cursor.close()
        print(f"[INFO] {len(self.creneaux)} creneaux charges au total")
    
    def _parse_heure(self, heure_raw):
        """Parse une heure depuis différents formats."""
        if heure_raw is None:
            return None
        if isinstance(heure_raw, str):
            if not heure_raw:
                return None
            # Essayer différents formats
            for fmt in ('%H:%M:%S', '%H:%M', '%H:%M:%S.%f'):
                try:
                    return datetime.strptime(heure_raw, fmt).time()
                except ValueError:
                    continue
            return None
        elif isinstance(heure_raw, datetime):
            return heure_raw.time()
        elif hasattr(heure_raw, 'hour'):  # C'est déjà un time
            return heure_raw
        return None
    
    def _load_competition_dates(self):
        """Charge les dates de début et fin pour chaque compétition."""
        cursor = self.connection.cursor(dictionary=True)
        
        comp_filter = self._get_competition_filter()
        query = f"""
        SELECT 
            c.code_competition,
            c.start_date,
            dl.date_limite as end_date
        FROM competitions c
        LEFT JOIN dates_limite dl ON dl.code_competition = c.code_competition
        WHERE c.code_competition IN {comp_filter}
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            # Convertir les dates si elles sont des chaînes
            start_date = row['start_date']
            end_date = row['end_date']
            
            if isinstance(start_date, str):
                # Essayer différents formats
                for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
                    try:
                        start_date = datetime.strptime(start_date, fmt).date()
                        break
                    except ValueError:
                        continue
            
            if isinstance(end_date, str):
                # Essayer différents formats
                for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
                    try:
                        end_date = datetime.strptime(end_date, fmt).date()
                        break
                    except ValueError:
                        continue
            
            comp_dates = CompetitionDates(
                code_competition=row['code_competition'],
                start_date=start_date,
                end_date=end_date
            )
            self.competition_dates[comp_dates.code_competition] = comp_dates
        
        cursor.close()
        print(f"[INFO] {len(self.competition_dates)} dates de competition chargees")
    
    def _build_virtual_divisions(self):
        """Reconstruit les divisions à partir des classements."""
        # Divisions à exclure (playoff/playdown de la demi-saison précédente)
        DIVISIONS_EXCLUES = ['7d', '7o']
        
        divisions_map = {}
        
        for classement in self.classements.values():
            # Ignorer les divisions de playoff/playdown
            if classement.division in DIVISIONS_EXCLUES:
                continue
            
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
        # Filtrer les équipes pour ne garder que celles avec classement correspondant
        equipes_valides = {}
        for equipe in self.equipes.values():
            if (equipe.classement and 
                equipe.classement.code_competition in self.competition_codes):
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
    
    def _load_historique_deplacements(self):
        """Charge l'historique des matchs passés pour calculer le déséquilibre dom/ext par paire."""
        cursor = self.connection.cursor(dictionary=True)
        
        # Charger tous les matchs CONFIRMED de la saison en cours
        query = """
        SELECT 
            m.id_equipe_dom,
            m.id_equipe_ext,
            COUNT(*) as nb_matchs
        FROM matches m
        WHERE m.match_status IN ('CONFIRMED', 'ARCHIVED')
        AND m.date_reception >= '2025-09-01'
        GROUP BY m.id_equipe_dom, m.id_equipe_ext
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Construire l'historique par paire d'équipes
        for row in rows:
            dom_id = str(row['id_equipe_dom'])
            ext_id = str(row['id_equipe_ext'])
            nb = row['nb_matchs']
            
            # Normaliser la paire (ordre alphabétique des IDs)
            pair = tuple(sorted([dom_id, ext_id]))
            
            if pair not in self.historique_deplacements:
                self.historique_deplacements[pair] = {pair[0]: 0, pair[1]: 0}
            
            # L'équipe dom_id a reçu (donc ext_id s'est déplacé)
            self.historique_deplacements[pair][dom_id] += nb
        
        # Compter les paires avec déséquilibre
        desequilibres = sum(1 for p, h in self.historique_deplacements.items() 
                          if abs(h[p[0]] - h[p[1]]) >= 2)
        
        cursor.close()
        print(f"[INFO] Historique: {len(self.historique_deplacements)} paires, {desequilibres} avec déséquilibre")
    
    def _load_equipes_joueurs(self):
        """Charge les joueurs par équipe avec leur sexe depuis la table joueur_equipe."""
        cursor = self.connection.cursor(dictionary=True)
        
        # Charger les joueurs avec leur sexe et le code compétition de l'équipe
        comp_filter = self._get_competition_filter()
        query = f"""
        SELECT je.id_equipe, je.id_joueur, j.sexe, cl.code_competition
        FROM joueur_equipe je
        JOIN equipes e ON e.id_equipe = je.id_equipe
        JOIN classements cl ON cl.id_equipe = e.id_equipe
        JOIN joueurs j ON j.id = je.id_joueur
        WHERE cl.code_competition IN {comp_filter}
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Stocker les joueurs par équipe avec leur sexe
        self.equipes_joueurs_details = {}  # {equipe_id: {'joueurs': set(), 'hommes': set(), 'femmes': set(), 'code_comp': str}}
        
        for row in rows:
            equipe_id = str(row['id_equipe'])
            joueur_id = str(row['id_joueur'])
            sexe = row['sexe']  # 'H' ou 'F'
            code_comp = row['code_competition']
            
            if equipe_id not in self.equipes_joueurs_details:
                self.equipes_joueurs_details[equipe_id] = {
                    'joueurs': set(),
                    'hommes': set(),
                    'femmes': set(),
                    'code_comp': code_comp
                }
            
            self.equipes_joueurs_details[equipe_id]['joueurs'].add(joueur_id)
            if sexe == 'H':
                self.equipes_joueurs_details[equipe_id]['hommes'].add(joueur_id)
            elif sexe == 'F':
                self.equipes_joueurs_details[equipe_id]['femmes'].add(joueur_id)
            
            # Compatibilité avec l'ancien format
            if equipe_id not in self.equipes_joueurs:
                self.equipes_joueurs[equipe_id] = set()
            self.equipes_joueurs[equipe_id].add(joueur_id)
        
        # Stats
        equipes_avec_effectif = sum(1 for e, d in self.equipes_joueurs_details.items() if len(d['joueurs']) > 0)
        cursor.close()
        print(f"[INFO] Effectifs: {equipes_avec_effectif} equipes avec joueurs renseignes")
    
    def _is_effectif_complet(self, equipe_id: str) -> bool:
        """Vérifie si une équipe a un effectif complet selon les règles de sa compétition.
        
        - KH: minimum 2 filles + 2 garçons
        - C/M: minimum 6 personnes
        """
        if equipe_id not in self.equipes_joueurs_details:
            return False
        
        details = self.equipes_joueurs_details[equipe_id]
        code_comp = details['code_comp'].lower()
        nb_hommes = len(details['hommes'])
        nb_femmes = len(details['femmes'])
        nb_total = len(details['joueurs'])
        
        if code_comp == 'kh':
            # KH: minimum 2 filles ET 2 garçons
            return nb_hommes >= 2 and nb_femmes >= 2
        else:
            # C, M et autres: minimum 6 personnes
            return nb_total >= 6
    
    def _calculate_effectif_commun(self, seuil_ratio: float = 0.5):
        """Calcule les paires d'équipes ayant un effectif commun significatif.
        
        Args:
            seuil_ratio: Ratio minimum de joueurs communs (par rapport à la plus petite équipe)
                        0.5 = au moins 50% de l'effectif de la plus petite équipe en commun
        
        Note: Seules les équipes avec effectif complet sont prises en compte.
              - KH: minimum 2 filles + 2 garçons
              - C/M: minimum 6 personnes
        """
        self.equipes_effectif_commun = []
        
        # Ne considérer que les équipes avec effectif complet
        equipes_valides = {}
        equipes_exclues = 0
        
        for equipe_id, joueurs in self.equipes_joueurs.items():
            if self._is_effectif_complet(equipe_id):
                equipes_valides[equipe_id] = joueurs
            else:
                equipes_exclues += 1
        
        if equipes_exclues > 0:
            print(f"[INFO] Effectif commun: {equipes_exclues} equipes exclues (effectif incomplet)")
        
        equipes_ids = list(equipes_valides.keys())
        
        for i in range(len(equipes_ids)):
            for j in range(i + 1, len(equipes_ids)):
                e1, e2 = equipes_ids[i], equipes_ids[j]
                joueurs_e1 = equipes_valides[e1]
                joueurs_e2 = equipes_valides[e2]
                
                # Calculer l'intersection
                joueurs_communs = joueurs_e1 & joueurs_e2
                nb_communs = len(joueurs_communs)
                
                if nb_communs > 0:
                    # Ratio par rapport à la plus petite équipe
                    min_effectif = min(len(joueurs_e1), len(joueurs_e2))
                    ratio = nb_communs / min_effectif
                    
                    if ratio >= seuil_ratio:
                        self.equipes_effectif_commun.append((e1, e2, nb_communs, ratio))
        
        if self.equipes_effectif_commun:
            print(f"[INFO] Effectif commun: {len(self.equipes_effectif_commun)} paires avec >={int(seuil_ratio*100)}% joueurs communs")
    
    def get_equipes_avec_effectif_commun(self) -> list:
        """Retourne la liste des paires d'équipes avec effectif commun significatif."""
        return self.equipes_effectif_commun
    
    def get_equipe_qui_doit_recevoir(self, equipe1_id: str, equipe2_id: str) -> str:
        """Retourne l'ID de l'équipe qui devrait recevoir pour équilibrer l'historique.
        
        Retourne l'équipe qui s'est le plus déplacée (donc qui devrait recevoir maintenant).
        Retourne None si pas d'historique ou si équilibré.
        """
        pair = tuple(sorted([equipe1_id, equipe2_id]))
        
        if pair not in self.historique_deplacements:
            return None
        
        hist = self.historique_deplacements[pair]
        receptions_e1 = hist.get(equipe1_id, 0)
        receptions_e2 = hist.get(equipe2_id, 0)
        
        # Celui qui a le moins reçu devrait recevoir maintenant
        if receptions_e1 < receptions_e2:
            return equipe1_id
        elif receptions_e2 < receptions_e1:
            return equipe2_id
        
        return None  # Équilibré


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
