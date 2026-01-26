#!/usr/bin/env python3
"""
Générateur de calendrier UFOLEP Volleyball - Version MySQL Finale
Utilise les données réelles de la base MySQL avec filtre paramétrable sur les compétitions.
- Contraintes UFOLEP complètes avec OR-Tools CP-SAT
- Support multi-compétitions: championnats ('m', 'f', 'mo'), coupes ('c'), etc.

Exemples d'utilisation:
    # Championnats (par défaut)
    scheduler = UfolepMySQLScheduler(['m', 'f', 'mo'])
    
    # Coupes uniquement
    scheduler = UfolepMySQLScheduler(['c'])
    
    # Une seule compétition
    scheduler = UfolepMySQLScheduler(['m'])
"""

import calendar
import math
from dataclasses import dataclass
from datetime import datetime, date, timedelta, time
from typing import List

import mysql.connector
from ortools.sat.python import cp_model

from db_config import DB_CONFIG, TABLE_NAMES, COLUMN_MAPPING
from db_loader_real import UfolepDatabaseLoader

# Jours fériés année scolaire 2025-2026
# Coupes: 19 janvier - 13 février 2026
# Championnats: 2 mars - 22 mai 2026
JOURS_FERIES = [
    # 2025
    date(2025, 11, 1),   # Toussaint
    date(2025, 11, 11),  # Armistice
    date(2025, 12, 25),  # Noël
    # 2026
    date(2026, 1, 1),    # Jour de l'An
    date(2026, 4, 6),    # Lundi de Pâques
    date(2026, 5, 1),    # Fête du Travail
    date(2026, 5, 8),    # Victoire 1945
    date(2026, 5, 14),   # Ascension
    date(2026, 5, 25),   # Lundi de Pentecôte
]

# Vacances scolaires Zone B année scolaire 2025-2026
VACANCES_ZONE_B = [
    # Vacances de la Toussaint 2025
    (date(2025, 10, 18), date(2025, 11, 3)),
    # Vacances de Noël 2025-2026
    (date(2025, 12, 20), date(2026, 1, 5)),
    # Vacances d'hiver 2026
    (date(2026, 2, 14), date(2026, 3, 2)),
    # Vacances de printemps 2026 (Zone B)
    (date(2026, 4, 11), date(2026, 4, 27)),
]

@dataclass
class TimeSlot:
    """Créneau horaire pour un match."""
    id: str
    equipe_id: str
    gymnase_id: str
    jour_semaine: int  # 1=Lundi, 7=Dimanche
    heure_debut: time
    club_id: str
    nb_terrains: int = 1

@dataclass
class Team:
    """Équipe avec ses informations complètes."""
    id: str
    nom: str
    club_id: str
    division_id: str
    code_competition: str
    time_slots: List[TimeSlot]
    lat: float = None
    lng: float = None

def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calcule la distance en km entre deux points GPS (formule Haversine)."""
    if None in (lat1, lng1, lat2, lng2):
        return 0
    R = 6371  # Rayon de la Terre en km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))

@dataclass
class Division:
    """Division avec ses équipes."""
    id: str
    nom: str
    code_competition: str
    division_num: int
    teams: List[Team]

@dataclass
class Match:
    """Match programmé."""
    id: str
    equipe_domicile: Team
    equipe_exterieur: Team
    date: date
    time_slot: TimeSlot
    division: Division

class UfolepMySQLScheduler:
    """Générateur de calendrier UFOLEP utilisant les données MySQL réelles."""
    
    def __init__(self, competition_codes: List[str] = None):
        """Initialise le scheduler.
        
        Args:
            competition_codes: Liste des codes de compétition à traiter (ex: ['m'], ['c'], ['m', 'f', 'mo'])
                              Par défaut: ['m', 'f', 'mo']
        """
        self.competition_codes = competition_codes or ['m', 'f', 'mo']
        self.db_loader = UfolepDatabaseLoader(self.competition_codes)
        self.divisions: List[Division] = []
        self.teams: List[Team] = []
        self.time_slots: List[TimeSlot] = []
        self.matches: List[Match] = []
        
        # Période de championnat (sera chargée depuis la BDD)
        self.start_date = None
        self.end_date = None
        
        # Jours de la semaine autorisés (1=Lundi, 5=Vendredi)
        self.allowed_weekdays = [1, 2, 3, 4, 5]
        
    def load_data(self) -> bool:
        """Charge les données depuis MySQL."""
        print(f"[INFO] Chargement des données MySQL UFOLEP pour {self.competition_codes}...")
        
        if not self.db_loader.load_all_data():
            print("[ERREUR] Impossible de charger les données MySQL")
            return False
        
        # Charger les dates de la première compétition depuis la BDD
        # (toutes les compétitions d'un même ensemble ont les mêmes dates)
        main_code = self.competition_codes[0]
        if main_code in self.db_loader.competition_dates:
            comp_dates = self.db_loader.competition_dates[main_code]
            self.start_date = comp_dates.start_date
            self.end_date = comp_dates.end_date
            print(f"[OK] Période compétition: {self.start_date} au {self.end_date}")
        else:
            print(f"[ERREUR] Dates non trouvées pour la compétition '{main_code}'")
            return False
            
        print(f"[OK] Données chargées: {len(self.db_loader.equipes)} équipes, "
              f"{len(self.db_loader.divisions_virtuelles)} divisions, "
              f"{len(self.db_loader.creneaux)} créneaux")
        
        return self._convert_data()
    
    def _convert_data(self) -> bool:
        """Convertit les données MySQL vers les structures du scheduler."""
        try:
            # Convertir les créneaux
            for creneau_data in self.db_loader.creneaux.values():
                equipe_data = self.db_loader.equipes.get(creneau_data.equipe_id)
                gymnase_data = self.db_loader.gymnases.get(creneau_data.gymnase_id)
                
                if equipe_data and gymnase_data:
                    club_data = self.db_loader.clubs.get(equipe_data.club_id)
                    
                    time_slot = TimeSlot(
                        id=creneau_data.id,
                        equipe_id=creneau_data.equipe_id,
                        gymnase_id=creneau_data.gymnase_id,
                        jour_semaine=creneau_data.jour_semaine,
                        heure_debut=creneau_data.heure_debut,
                        club_id=club_data.id,
                        nb_terrains=gymnase_data.nb_terrains
                    )
                    self.time_slots.append(time_slot)
            
            # Convertir les équipes
            teams_by_division = {}
            for equipe_data in self.db_loader.equipes.values():
                if equipe_data.classement:
                    # Récupérer les créneaux de cette équipe
                    equipe_time_slots = [ts for ts in self.time_slots if ts.equipe_id == equipe_data.id]
                    
                    # Récupérer les coordonnées GPS du gymnase principal (premier créneau)
                    lat, lng = None, None
                    if equipe_time_slots:
                        gym = self.db_loader.gymnases.get(equipe_time_slots[0].gymnase_id)
                        if gym:
                            lat, lng = gym.lat, gym.lng
                    
                    team = Team(
                        id=equipe_data.id,
                        nom=equipe_data.nom,
                        club_id=equipe_data.club_id,
                        division_id=f"{equipe_data.classement.code_competition}_{equipe_data.classement.division}",
                        code_competition=equipe_data.classement.code_competition,
                        time_slots=equipe_time_slots,
                        lat=lat,
                        lng=lng
                    )
                    self.teams.append(team)
                    
                    # Grouper par division
                    div_key = team.division_id
                    if div_key not in teams_by_division:
                        teams_by_division[div_key] = []
                    teams_by_division[div_key].append(team)
            
            # Créer les divisions
            for div_data in self.db_loader.divisions_virtuelles.values():
                div_key = f"{div_data.code_competition}_{div_data.division}"
                if div_key in teams_by_division:
                    teams_in_division = teams_by_division[div_key]
                    # Ignorer les divisions avec plus de 8 équipes
                    if len(teams_in_division) > 8:
                        raise ValueError(f"Division {div_data.nom} a plus de 8 équipes, c'est interdit")
                    division = Division(
                        id=div_key,
                        nom=div_data.nom,
                        code_competition=div_data.code_competition,
                        division_num=div_data.division,
                        teams=teams_in_division
                    )
                    self.divisions.append(division)
            # Compter les équipes dans les divisions retenues
            teams_in_selected_divisions = sum(len(div.teams) for div in self.divisions)
            print(f"[OK] Conversion terminée: {len(self.divisions)} divisions, "
                  f"{teams_in_selected_divisions} équipes programmées, {len(self.time_slots)} créneaux")
            return True
            
        except Exception as e:
            print(f"[ERREUR] Erreur lors de la conversion des données: {e}")
            return False
    
    def _is_valid_date(self, date_obj: date) -> bool:
        """Vérifie si une date est valide (pas férié, pas vacances, bon jour semaine)."""
        # Vérifier jour de la semaine (1=Lundi, 7=Dimanche)
        if date_obj.weekday() + 1 not in self.allowed_weekdays:
            return False
            
        # Vérifier jours fériés
        if date_obj in JOURS_FERIES:
            return False
            
        # Vérifier vacances scolaires
        for debut_vacances, fin_vacances in VACANCES_ZONE_B:
            if debut_vacances <= date_obj <= fin_vacances:
                return False
                
        return True
    
    def _generate_valid_dates(self) -> List[date]:
        """Génère la liste des dates valides pour la période."""
        valid_dates = []
        current_date = self.start_date
        
        while current_date <= self.end_date:
            if self._is_valid_date(current_date):
                valid_dates.append(current_date)
            current_date += timedelta(days=1)
            
        return valid_dates
    
    def _calculate_matches_needed(self) -> int:
        """Calcule le nombre total de matchs nécessaires."""
        total_matches = 0
        for division in self.divisions:
            n_teams = len(division.teams)
            if n_teams >= 3:
                # Championnat aller uniquement
                matches_in_division = n_teams * (n_teams - 1) // 2
                total_matches += matches_in_division
                print(f"[INFO] {division.nom}: {n_teams} équipes = {matches_in_division} matchs")
        
        return total_matches
    
    def _add_match_assignment_constraints_flexible(self, model: cp_model.CpModel, matches_data: list, total_matches: int) -> None:
        """Contrainte flexible : Chaque match programmé 0 ou 1 fois, maximiser les matchs programmés."""
        matches_by_id = {}
        for match_data in matches_data:
            mid = match_data['match_id']
            if mid not in matches_by_id:
                matches_by_id[mid] = []
            matches_by_id[mid].append(match_data['var'])
        
        for match_id, vars_list in matches_by_id.items():
            model.Add(sum(vars_list) <= 1)
        
        all_vars = [var for vars_list in matches_by_id.values() for var in vars_list]
        model.Maximize(sum(all_vars))
    
    def _add_team_date_constraints(self, model: cp_model.CpModel, matches_data: list) -> None:
        """Contrainte : Une équipe ne peut jouer qu'un match par date."""
        team_date_vars = {}
        for match_data in matches_data:
            home_team = match_data['home_team']
            away_team = match_data['away_team']
            date_obj = match_data['date']
            var = match_data['var']
            
            for team_id in [home_team.id, away_team.id]:
                key = (team_id, date_obj)
                if key not in team_date_vars:
                    team_date_vars[key] = []
                team_date_vars[key].append(var)
        
        for vars_list in team_date_vars.values():
            model.Add(sum(vars_list) <= 1)
    
    def _add_gymnasium_capacity_constraints(self, model: cp_model.CpModel, matches_data: list) -> None:
        """Contrainte : Capacité des gymnases respectée."""
        gymnasium_date_vars = {}
        for match_data in matches_data:
            key = (match_data['time_slot'].gymnase_id, match_data['date'])
            if key not in gymnasium_date_vars:
                gymnasium_date_vars[key] = []
            gymnasium_date_vars[key].append(match_data['var'])
        
        for (gym_id, _), vars_list in gymnasium_date_vars.items():
            gymnase = self.db_loader.gymnases.get(gym_id)
            model.Add(sum(vars_list) <= gymnase.nb_terrains)
    
    def _add_weekly_match_limit_constraints(self, model: cp_model.CpModel, matches_data: list) -> dict:
        """Contrainte : Maximum 1 match par équipe par semaine."""
        team_week_vars = {}
        for match_data in matches_data:
            week_num = match_data['date'].isocalendar()[1]
            var = match_data['var']
            
            for team in [match_data['home_team'], match_data['away_team']]:
                key = (team.id, week_num)
                if key not in team_week_vars:
                    team_week_vars[key] = []
                team_week_vars[key].append(var)
        
        for vars_list in team_week_vars.values():
            model.Add(sum(vars_list) <= 1)
        return team_week_vars
    
    def _add_home_balance_constraints(self, model: cp_model.CpModel, matches_data: list) -> None:
        """Contrainte : Équipes avec créneaux doivent avoir max 1 match d'écart dom/ext."""
        teams_with_reception = {team.id for team in self.teams if team.time_slots}
        
        team_home_vars = {}
        team_away_vars = {}
        
        for match_data in matches_data:
            home_id = match_data['home_team'].id
            away_id = match_data['away_team'].id
            var = match_data['var']
            
            team_home_vars.setdefault(home_id, []).append(var)
            team_away_vars.setdefault(away_id, []).append(var)
        
        for team_id in teams_with_reception:
            home_vars = team_home_vars.get(team_id, [])
            away_vars = team_away_vars.get(team_id, [])
            if home_vars and away_vars:
                model.Add(sum(home_vars) >= sum(away_vars) - 1)
    
    def _add_history_based_home_constraints(self, model: cp_model.CpModel, matches_data: list) -> None:
        """Contrainte : Alternance domicile/extérieur basée sur l'historique pour TOUTES les paires.
        
        Pour chaque paire d'équipes:
        - Si A a reçu B la dernière fois, alors B doit recevoir A (si B a un créneau)
        - Sinon: pas de contrainte spécifique sur qui reçoit
        """
        teams_by_id = {t.id: t for t in self.teams}
        teams_with_reception = {team.id for team in self.teams if team.time_slots}
        
        # Collecter toutes les paires d'équipes de toutes les divisions
        all_pairs = []
        for division in self.divisions:
            teams = division.teams
            for i in range(len(teams)):
                for j in range(i + 1, len(teams)):
                    t1, t2 = teams[i], teams[j]
                    all_pairs.append((t1, t2, division))
        
        if not all_pairs:
            return
        
        # Grouper les variables par paire d'équipes et par qui reçoit
        pair_home_vars = {}
        
        for match_data in matches_data:
            home_id = match_data['home_team'].id
            away_id = match_data['away_team'].id
            var = match_data['var']
            
            pair = tuple(sorted([home_id, away_id]))
            if pair not in pair_home_vars:
                pair_home_vars[pair] = {pair[0]: [], pair[1]: []}
            
            pair_home_vars[pair][home_id].append(var)
        
        # Appliquer les contraintes
        forced_receptions = 0
        skipped_no_slot = 0
        
        for t1, t2, division in all_pairs:
            pair = tuple(sorted([t1.id, t2.id]))
            if pair not in pair_home_vars:
                continue
                
            vars_t1_home = pair_home_vars[pair].get(t1.id, [])
            vars_t2_home = pair_home_vars[pair].get(t2.id, [])
            
            if not vars_t1_home and not vars_t2_home:
                continue
            
            # Vérifier l'historique pour cette paire
            equipe_qui_doit_recevoir = self.db_loader.get_equipe_qui_doit_recevoir(t1.id, t2.id)
            
            if equipe_qui_doit_recevoir:
                # Forcer la réception vers l'équipe désignée par l'historique
                # MAIS seulement si l'équipe a des dates valides pour recevoir (vars non vide)
                if equipe_qui_doit_recevoir == t1.id:
                    if vars_t1_home and t1.id in teams_with_reception:
                        # Ne pas forcer sum==1 car ça force le match à être programmé
                        # Juste interdire que t2 reçoive si t1 peut recevoir
                        if vars_t2_home:
                            model.Add(sum(vars_t2_home) == 0)
                        forced_receptions += 1
                    else:
                        skipped_no_slot += 1
                elif equipe_qui_doit_recevoir == t2.id:
                    if vars_t2_home and t2.id in teams_with_reception:
                        # Ne pas forcer sum==1 car ça force le match à être programmé
                        # Juste interdire que t1 reçoive si t2 peut recevoir
                        if vars_t1_home:
                            model.Add(sum(vars_t1_home) == 0)
                        forced_receptions += 1
                    else:
                        skipped_no_slot += 1
        
        print(f"[INFO] Alternance historique: {forced_receptions} réceptions forcées, {skipped_no_slot} ignorées (pas de créneau/date)")
    
    def _add_shared_roster_constraints(self, model: cp_model.CpModel, matches_data: list) -> None:
        """Contrainte optionnelle : Éviter que 2 équipes avec effectif commun jouent le même soir.
        
        Si 2 équipes partagent ≥50% de leur effectif, elles ne doivent pas jouer le même jour.
        """
        # Récupérer les paires d'équipes avec effectif commun
        paires_effectif_commun = self.db_loader.get_equipes_avec_effectif_commun()
        
        if not paires_effectif_commun:
            return
        
        # Grouper les matchs par équipe et par date
        team_date_vars = {}  # {(team_id, date): [vars]}
        
        for match_data in matches_data:
            home_id = match_data['home_team'].id
            away_id = match_data['away_team'].id
            date_obj = match_data['date']
            var = match_data['var']
            
            # Les deux équipes sont occupées par ce match
            for team_id in [home_id, away_id]:
                key = (team_id, date_obj)
                if key not in team_date_vars:
                    team_date_vars[key] = []
                team_date_vars[key].append(var)
        
        # Appliquer les contraintes pour chaque paire avec effectif commun
        constraints_added = 0
        
        for e1_id, e2_id, nb_communs, ratio in paires_effectif_commun:
            # Pour chaque date, si e1 joue alors e2 ne doit pas jouer
            dates_with_both = set()
            
            for (team_id, date_obj), vars_list in team_date_vars.items():
                if team_id == e1_id:
                    dates_with_both.add(date_obj)
            
            for date_obj in dates_with_both:
                vars_e1 = team_date_vars.get((e1_id, date_obj), [])
                vars_e2 = team_date_vars.get((e2_id, date_obj), [])
                
                if vars_e1 and vars_e2:
                    # Au plus une des deux équipes peut jouer ce jour
                    model.Add(sum(vars_e1) + sum(vars_e2) <= 1)
                    constraints_added += 1
        
        if constraints_added > 0:
            # Récupérer les noms pour le log
            teams_by_id = {t.id: t for t in self.teams}
            print(f"[INFO] Effectif commun: {len(paires_effectif_commun)} paires, {constraints_added} contraintes jour ajoutées")
            for e1_id, e2_id, nb_communs, ratio in paires_effectif_commun[:5]:  # Afficher max 5
                e1_nom = teams_by_id.get(e1_id, type('', (), {'nom': e1_id})()).nom
                e2_nom = teams_by_id.get(e2_id, type('', (), {'nom': e2_id})()).nom
                print(f"       - {e1_nom} / {e2_nom}: {nb_communs} joueurs ({int(ratio*100)}%)")
            if len(paires_effectif_commun) > 5:
                print(f"       ... et {len(paires_effectif_commun) - 5} autres paires")
        
    def generate_schedule(self) -> bool:
        """Génère le calendrier complet avec OR-Tools."""
        total_matches = self._calculate_matches_needed()
        valid_dates = self._generate_valid_dates()

        # Initialiser le modèle OR-Tools
        model = cp_model.CpModel()
        
        # Variables de décision
        match_vars = {}
        matches_data = []
        
        # Créer toutes les combinaisons possibles
        match_id = 0
        for division in self.divisions:
            teams = division.teams
            n_teams = len(teams)
            if n_teams < 3:
                continue
            # Générer tous les matchs de la division (aller uniquement)
            for i in range(n_teams):
                for j in range(i + 1, n_teams):
                    team_home = teams[i]
                    team_away = teams[j]
                    # Créer les variables pour chaque date et créneau possible
                    for date_obj in valid_dates:
                        # Match à domicile : créneaux de l'équipe à domicile
                        for time_slot in team_home.time_slots:
                            if date_obj.weekday() + 1 == time_slot.jour_semaine:
                                # Vérifier que le gymnase est disponible à cette date
                                if not self.db_loader.is_gymnase_available(time_slot.gymnase_id, date_obj):
                                    continue
                                var_name = f"match_{match_id}_home_{date_obj}_{time_slot.id}"
                                match_var = model.NewBoolVar(var_name)
                                match_vars[var_name] = match_var
                                
                                matches_data.append({
                                    'var': match_var,
                                    'match_id': match_id,
                                    'home_team': team_home,
                                    'away_team': team_away,
                                    'date': date_obj,
                                    'time_slot': time_slot,
                                    'division': division
                                })
                        
                        # Match à l'extérieur : créneaux de l'équipe à l'extérieur
                        for time_slot in team_away.time_slots:
                            if date_obj.weekday() + 1 == time_slot.jour_semaine:
                                # Vérifier que le gymnase est disponible à cette date
                                if not self.db_loader.is_gymnase_available(time_slot.gymnase_id, date_obj):
                                    continue
                                var_name = f"match_{match_id}_away_{date_obj}_{time_slot.id}"
                                match_var = model.NewBoolVar(var_name)
                                match_vars[var_name] = match_var
                                
                                matches_data.append({
                                    'var': match_var,
                                    'match_id': match_id,
                                    'home_team': team_away,  # Inversion !
                                    'away_team': team_home,  # Inversion !
                                    'date': date_obj,
                                    'time_slot': time_slot,
                                    'division': division
                                })
                    
                    match_id += 1
        
        # Stocker les infos des matchs pour gérer les non-programmables
        self._all_matches_info = []
        for division in self.divisions:
            teams = division.teams
            n_teams = len(teams)
            if n_teams < 3:
                continue
            for i in range(n_teams):
                for j in range(i + 1, n_teams):
                    self._all_matches_info.append({
                        'team1': teams[i],
                        'team2': teams[j],
                        'division': division
                    })
        
        # Application des contraintes SIMPLIFIÉES
        # 1. Chaque match programmé exactement une fois (si possible)
        self._add_match_assignment_constraints_flexible(model, matches_data, match_id)
        
        # 2. Max 1 match par équipe par date
        self._add_team_date_constraints(model, matches_data)
        
        # 3. Capacité gymnases
        self._add_gymnasium_capacity_constraints(model, matches_data)
        
        # 4. Max 1 match par équipe par semaine
        self._add_weekly_match_limit_constraints(model, matches_data)
        
        # 5. Équilibre dom/ext pour équipes avec créneaux
        self._add_home_balance_constraints(model, matches_data)
        
        # 6. Alternance dom/ext basée sur l'historique (TOUTES les paires)
        self._add_history_based_home_constraints(model, matches_data)
        
        # 7. Éviter que 2 équipes avec effectif commun jouent le même soir
        self._add_shared_roster_constraints(model, matches_data)
        
        # Résoudre
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 300.0
        solver.parameters.log_search_progress = False
        
        status = solver.Solve(model)
        
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            
            # Extraire les matchs programmés
            self.matches = []
            programmed_pairs = set()  # Pour identifier les matchs programmés
            
            for match_data in matches_data:
                if solver.Value(match_data['var']) == 1:
                    match = Match(
                        id=f"match_{len(self.matches)}",
                        equipe_domicile=match_data['home_team'],
                        equipe_exterieur=match_data['away_team'],
                        date=match_data['date'],
                        time_slot=match_data['time_slot'],
                        division=match_data['division']
                    )
                    self.matches.append(match)
                    # Enregistrer la paire d'équipes programmée
                    pair = tuple(sorted([match_data['home_team'].id, match_data['away_team'].id]))
                    programmed_pairs.add((pair, match_data['division'].id))
            
            # Créer les matchs non programmés (sans date)
            self.unscheduled_matches = []
            for match_info in self._all_matches_info:
                pair = tuple(sorted([match_info['team1'].id, match_info['team2'].id]))
                key = (pair, match_info['division'].id)
                if key not in programmed_pairs:
                    # Match non programmé - créer sans date
                    # Déterminer qui reçoit (équipe avec créneaux prioritaire)
                    if match_info['team1'].time_slots:
                        home_team, away_team = match_info['team1'], match_info['team2']
                    elif match_info['team2'].time_slots:
                        home_team, away_team = match_info['team2'], match_info['team1']
                    else:
                        home_team, away_team = match_info['team1'], match_info['team2']
                    
                    match = Match(
                        id=f"unscheduled_{len(self.unscheduled_matches)}",
                        equipe_domicile=home_team,
                        equipe_exterieur=away_team,
                        date=None,  # Pas de date
                        time_slot=None,  # Pas de créneau
                        division=match_info['division']
                    )
                    self.unscheduled_matches.append(match)
            
            print(f"[OK] {len(self.matches)} matchs programmés")
            if self.unscheduled_matches:
                print(f"[ATTENTION] {len(self.unscheduled_matches)} matchs non programmés (sans date)")
            return True
            
        else:
            print(f"\n[ÉCHEC] Impossible de trouver une solution. Status: {solver.StatusName(status)}")
            return False
    
    def print_schedule(self):
        """Affiche le calendrier généré."""
        if not self.matches:
            print("[INFO] Aucun match programmé")
            return
        
        print("\n" + "="*80)
        print("CALENDRIER")
        print("="*80)
        
        sorted_matches = sorted(self.matches, key=lambda m: (m.date, m.time_slot.heure_debut))
        current_date = None
        
        for match in sorted_matches:
            if current_date != match.date:
                current_date = match.date
                day_name = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][match.date.weekday()]
                print(f"\n{day_name} {match.date.strftime('%d/%m/%Y')}")
                print("-" * 50)
            
            print(f"  {match.time_slot.heure_debut.strftime('%H:%M')} | {match.division.nom}")
            print(f"    {match.equipe_domicile.nom} vs {match.equipe_exterieur.nom}")
        
        self._print_statistics()
    
    def _print_statistics(self):
        """Affiche les statistiques: par division et par équipe."""
        # Stats par division
        matches_by_division = {}
        for match in self.matches:
            div_name = match.division.nom
            matches_by_division[div_name] = matches_by_division.get(div_name, 0) + 1
        
        print("\n" + "="*80)
        print("MATCHS PAR DIVISION")
        print("="*80)
        for div_name, count in sorted(matches_by_division.items()):
            print(f"  {div_name}: {count} matchs")
        print(f"\nTotal: {len(self.matches)} matchs programmés")
        
        # Stats par équipe (dom/ext)
        team_stats = {}
        for match in self.matches:
            home_name = match.equipe_domicile.nom
            away_name = match.equipe_exterieur.nom
            
            if home_name not in team_stats:
                team_stats[home_name] = {'dom': 0, 'ext': 0}
            if away_name not in team_stats:
                team_stats[away_name] = {'dom': 0, 'ext': 0}
            
            team_stats[home_name]['dom'] += 1
            team_stats[away_name]['ext'] += 1
        
        print("\n" + "="*80)
        print("RÉCEPTIONS / DÉPLACEMENTS PAR ÉQUIPE")
        print("="*80)
        print(f"{'Équipe':<30} | {'Dom':>3} | {'Ext':>3} | {'Total':>5}")
        print("-" * 50)
        for team_name, stats in sorted(team_stats.items()):
            total = stats['dom'] + stats['ext']
            print(f"{team_name:<30} | {stats['dom']:>3} | {stats['ext']:>3} | {total:>5}")
    
    def validate_gymnasium_capacity(self) -> bool:
        """Valide que la contrainte de capacité des gymnases est respectée."""
        gymnasium_usage = {}
        for match in self.matches:
            key = (match.time_slot.gymnase_id, match.date)
            gymnasium_usage.setdefault(key, []).append(match)
        
        violations = 0
        for (gym_id, _), matches_list in gymnasium_usage.items():
            gymnase = self.db_loader.gymnases.get(gym_id)
            if gymnase and len(matches_list) > gymnase.nb_terrains:
                violations += 1
        
        if violations:
            print(f"\n[ERREUR] {violations} violations de capacité gymnase")
        return violations == 0
    
    def validate_home_balance(self):
        """Valide l'équilibre dom/ext (max 1 écart)."""
        teams_with_reception = {team.id for team in self.teams if team.time_slots}
        
        team_stats = {}
        for match in self.matches:
            for team_id, is_home in [(match.equipe_domicile.id, True), (match.equipe_exterieur.id, False)]:
                team_stats.setdefault(team_id, {'home': 0, 'away': 0})
                team_stats[team_id]['home' if is_home else 'away'] += 1
        
        violations = sum(1 for tid in teams_with_reception if tid in team_stats 
                        and team_stats[tid]['home'] < team_stats[tid]['away'] - 1)
        
        if violations:
            print(f"\n[ATTENTION] {violations} équipes avec déséquilibre dom/ext")

    def validate_club_capacity(self) -> tuple[bool, set]:
        """Valide que chaque club respecte la règle: nb_équipes <= 2 x nb_terrains_semaine.
        Retourne (all_valid, valid_club_ids)"""
        print("\n" + "="*80)
        print("VALIDATION DES CONTRAINTES CLUBS (DONNÉES D'ENTRÉE)")
        print("="*80)
        
        violations = []
        club_stats = {}
        valid_club_ids = set()
        
        # Analyser chaque club
        for club_data in self.db_loader.clubs.values():
            club_id = club_data.id
            club_name = club_data.nom
            
            # Compter les équipes du club (dans les divisions retenues)
            club_teams = [team for team in self.teams if team.club_id == club_id]
            nb_equipes = len(club_teams)
            
            # Calculer la capacité théorique du club
            # nb_terrains_semaine = somme(nb_terrains x nb_créneaux_semaine) pour tous les gymnases du club
            club_gymnases = {}
            total_terrains_semaine = 0
            
            for team in club_teams:
                for time_slot in team.time_slots:
                    gym_id = time_slot.gymnase_id
                    if gym_id not in club_gymnases:
                        gymnase = self.db_loader.gymnases.get(gym_id)
                        if gymnase:
                            club_gymnases[gym_id] = {
                                'nom': gymnase.nom,
                                'nb_terrains': gymnase.nb_terrains,
                                'creneaux_semaine': set()
                            }
                    
                    if gym_id in club_gymnases:
                        # Compter les créneaux uniques par semaine (jour + heure)
                        creneau_key = (time_slot.jour_semaine, time_slot.heure_debut)
                        club_gymnases[gym_id]['creneaux_semaine'].add(creneau_key)
            
            # Calculer la capacité totale
            for gym_id, gym_info in club_gymnases.items():
                nb_creneaux_semaine = len(gym_info['creneaux_semaine'])
                terrains_semaine = gym_info['nb_terrains'] * nb_creneaux_semaine
                total_terrains_semaine += terrains_semaine
            
            # Capacité maximale selon la règle UFOLEP
            max_equipes_autorisees = 2 * total_terrains_semaine
            
            club_stats[club_id] = {
                'nom': club_name,
                'nb_equipes': nb_equipes,
                'terrains_semaine': total_terrains_semaine,
                'max_autorise': max_equipes_autorisees,
                'gymnases': club_gymnases,
                'teams': club_teams
            }
            
            # Vérifier la violation
            if nb_equipes > max_equipes_autorisees:
                violations.append(club_stats[club_id])
            else:
                valid_club_ids.add(club_id)
        
        # Rapport de validation
        if violations:
            print(f"[WARNING] VIOLATIONS DETECTEES: {len(violations)} clubs en surcharge")
            print(f"[OK] CLUBS CONFORMES: {len(valid_club_ids)} clubs respectent les contraintes")
            print("\nDétail des violations:")
            
            for i, club_info in enumerate(violations, 1):
                print(f"\n{i}. Club: {club_info['nom']} (IGNORÉ)")
                print(f"   Équipes inscrites: {club_info['nb_equipes']}")
                print(f"   Capacité autorisée: {club_info['max_autorise']} équipes")
                print(f"   DÉPASSEMENT: +{club_info['nb_equipes'] - club_info['max_autorise']} équipes")
                print(f"   Terrains x créneaux/semaine: {club_info['terrains_semaine']}")
                
                print("   Gymnases utilisés:")
                for gym_id, gym_info in club_info['gymnases'].items():
                    nb_creneaux = len(gym_info['creneaux_semaine'])
                    capacite_gym = gym_info['nb_terrains'] * nb_creneaux
                    print(f"     - {gym_info['nom']}: {gym_info['nb_terrains']} terrains x {nb_creneaux} créneaux = {capacite_gym}")
                
                print("   Équipes IGNORÉES:")
                for team in club_info['teams']:
                    print(f"     - {team.nom} (Division {team.division_id})")
            
            print("\n[INFO] STRATEGIE: Generation du calendrier avec les clubs conformes uniquement.")
            print(f"   - Clubs inclus: {len(valid_club_ids)}")
            print(f"   - Clubs ignorés: {len(violations)}")
            
            return False, valid_club_ids
        else:
            print("[OK] TOUTES LES CONTRAINTES CLUBS RESPECTEES")
            print("Aucune surcharge détectée.")
            
            # Statistiques des clubs
            print("\nStatistiques des clubs:")
            sorted_clubs = sorted(club_stats.items(), 
                                key=lambda x: x[1]['nb_equipes'], reverse=True)
            
            print("\nTop clubs par nombre d'équipes:")
            for club_id, stats in sorted_clubs[:10]:
                if stats['nb_equipes'] > 0:
                    utilization = (stats['nb_equipes'] / stats['max_autorise']) * 100 if stats['max_autorise'] > 0 else 0
                    print(f"  {stats['nom']}: {stats['nb_equipes']}/{stats['max_autorise']} équipes "
                          f"({utilization:.1f}% de la capacité)")
            
            return True, valid_club_ids
    
    def generate_match_code(self, match: Match, match_index: int) -> str:
        """Génère un code unique pour le match."""
        # Format: COMP_DIV_YYYYMMDD_INDEX (ex: M_1_20251103_001)
        date_str = match.date.strftime('%Y%m%d')
        return f"{match.division.code_competition.upper()}_{match.division.division_num}_{date_str}_{match_index:03d}"
    
    def clear_existing_matches(self) -> bool:
        """Supprime uniquement les matchs NOT_CONFIRMED des compétitions sélectionnées."""
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor()
            
            # Construire le filtre dynamique
            codes_str = ", ".join(f"'{c}'" for c in self.competition_codes)
            
            # Supprimer uniquement les matchs NOT_CONFIRMED des compétitions filtrées
            query = f"""
            DELETE FROM {TABLE_NAMES['matchs']} 
            WHERE {COLUMN_MAPPING['matches']['code_competition']} IN ({codes_str})
            AND {COLUMN_MAPPING['matches']['match_status']} = 'NOT_CONFIRMED'
            """
            
            cursor.execute(query)
            deleted_count = cursor.rowcount
            
            connection.commit()
            cursor.close()
            connection.close()
            
            print(f"[INFO] {deleted_count} matchs existants supprimés de la base de données")
            return True
            
        except mysql.connector.Error as e:
            print(f"[ERREUR] Impossible de supprimer les matchs existants: {e}")
            return False
    
    def save_matches_to_database(self) -> bool:
        """Sauvegarde tous les matchs générés dans la base de données."""
        if not self.matches:
            print("[INFO] Aucun match à sauvegarder")
            return True
            
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor()
            
            # Préparer la requête d'insertion
            insert_query = f"""
            INSERT INTO {TABLE_NAMES['matchs']} (
                {COLUMN_MAPPING['matches']['code_match']},
                {COLUMN_MAPPING['matches']['code_competition']},
                {COLUMN_MAPPING['matches']['division']},
                {COLUMN_MAPPING['matches']['id_equipe_dom']},
                {COLUMN_MAPPING['matches']['id_equipe_ext']},
                {COLUMN_MAPPING['matches']['date_reception']},
                {COLUMN_MAPPING['matches']['match_status']},
                {COLUMN_MAPPING['matches']['id_gymnasium']}
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Préparer les données à insérer
            matches_data = []
            for i, match in enumerate(self.matches, 1):
                match_code = self.generate_match_code(match, i)
                
                # Utiliser seulement la date (pas l'heure)
                
                match_row = (
                    match_code,                           # code_match
                    match.division.code_competition,      # code_competition
                    match.division.division_num,          # division
                    match.equipe_domicile.id,            # id_equipe_dom
                    match.equipe_exterieur.id,           # id_equipe_ext
                    match.date,                           # date_reception (date seulement)
                    'NOT_CONFIRMED',                      # match_status
                    match.time_slot.gymnase_id           # id_gymnasium
                )
                matches_data.append(match_row)
            
            # Insérer tous les matchs
            cursor.executemany(insert_query, matches_data)
            
            connection.commit()
            inserted_count = cursor.rowcount
            
            cursor.close()
            connection.close()
            
            print(f"[SUCCÈS] {inserted_count} matchs sauvegardés dans la base de données")
            return True
            
        except mysql.connector.Error as e:
            print(f"[ERREUR] Impossible de sauvegarder les matchs: {e}")
            return False
    
    def save_schedule_to_database(self) -> bool:
        """Sauvegarde complète: supprime les anciens matchs et insère les nouveaux."""
        print("\n" + "="*60)
        print("SAUVEGARDE DU CALENDRIER EN BASE DE DONNÉES")
        print("="*60)
        
        # Étape 1: Supprimer les matchs existants
        if not self.clear_existing_matches():
            return False
        
        # Étape 2: Insérer les nouveaux matchs
        if not self.save_matches_to_database():
            return False
        
        print("[SUCCÈS] Calendrier sauvegardé avec succès dans la base MySQL!")
        return True
    
    def generate_sql_file(self, filename: str = "insert_matches.sql") -> bool:
        """Génère un fichier SQL pour insérer les matchs via phpMyAdmin.
        Utilise exactement la même logique que save_matches_to_database()."""
        if not self.matches:
            print("[ERREUR] Aucun match à exporter")
            return False
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # En-tête du fichier
                f.write("-- Fichier SQL généré automatiquement par le générateur UFOLEP\n")
                f.write(f"-- Date de génération: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- Nombre de matchs: {len(self.matches)}\n")
                f.write("-- À exécuter dans phpMyAdmin\n\n")
                
                # Suppression des matchs existants (même logique que clear_existing_matches)
                codes_str = ", ".join(f"'{c}'" for c in self.competition_codes)
                f.write("-- Suppression uniquement des matchs NOT_CONFIRMED\n")
                f.write(f"DELETE FROM {TABLE_NAMES['matchs']} \n")
                f.write(f"WHERE {COLUMN_MAPPING['matches']['code_competition']} IN ({codes_str})\n")
                f.write(f"AND {COLUMN_MAPPING['matches']['match_status']} = 'NOT_CONFIRMED';\n\n")
                
                # Insertion des nouveaux matchs (même structure que save_matches_to_database)
                f.write("-- Insertion des nouveaux matchs\n")
                f.write(f"INSERT INTO {TABLE_NAMES['matchs']} (\n")
                f.write(f"    {COLUMN_MAPPING['matches']['code_match']},\n")
                f.write(f"    {COLUMN_MAPPING['matches']['code_competition']},\n")
                f.write(f"    {COLUMN_MAPPING['matches']['division']},\n")
                f.write(f"    {COLUMN_MAPPING['matches']['id_equipe_dom']},\n")
                f.write(f"    {COLUMN_MAPPING['matches']['id_equipe_ext']},\n")
                f.write(f"    {COLUMN_MAPPING['matches']['date_reception']},\n")
                f.write(f"    {COLUMN_MAPPING['matches']['match_status']},\n")
                f.write(f"    {COLUMN_MAPPING['matches']['id_gymnasium']}\n")
                f.write(") VALUES\n")
                
                # Préparer les données exactement comme dans save_matches_to_database
                match_values = []
                for i, match in enumerate(self.matches, 1):
                    # Utiliser la même méthode de génération de code
                    match_code = self.generate_match_code(match, i)
                    
                    # Utiliser seulement la date (pas l'heure)
                    date_str = match.date.strftime('%Y-%m-%d')
                    
                    # Créer la ligne de valeurs avec les mêmes données
                    values = f"('{match_code}', '{match.division.code_competition}', '{match.division.division_num}', '{match.equipe_domicile.id}', '{match.equipe_exterieur.id}', '{date_str}', 'NOT_CONFIRMED', '{match.time_slot.gymnase_id}')"
                    match_values.append(values)
                
                # Écrire toutes les valeurs
                f.write(',\n'.join(match_values))
                f.write(';\n\n')
                
                # Ajouter les matchs non programmés (sans date)
                if hasattr(self, 'unscheduled_matches') and self.unscheduled_matches:
                    f.write("\n-- Insertion des matchs non programmés (sans date)\n")
                    f.write(f"INSERT INTO {TABLE_NAMES['matchs']} (\n")
                    f.write(f"    {COLUMN_MAPPING['matches']['code_match']},\n")
                    f.write(f"    {COLUMN_MAPPING['matches']['code_competition']},\n")
                    f.write(f"    {COLUMN_MAPPING['matches']['division']},\n")
                    f.write(f"    {COLUMN_MAPPING['matches']['id_equipe_dom']},\n")
                    f.write(f"    {COLUMN_MAPPING['matches']['id_equipe_ext']},\n")
                    f.write(f"    {COLUMN_MAPPING['matches']['date_reception']},\n")
                    f.write(f"    {COLUMN_MAPPING['matches']['match_status']},\n")
                    f.write(f"    {COLUMN_MAPPING['matches']['id_gymnasium']}\n")
                    f.write(") VALUES\n")
                    
                    unscheduled_values = []
                    for i, match in enumerate(self.unscheduled_matches, len(self.matches) + 1):
                        match_code = f"{match.division.code_competition.upper()}_{match.division.division_num}_{i:03d}_UNSCHEDULED"
                        # NULL pour date et gymnase
                        values = f"('{match_code}', '{match.division.code_competition}', '{match.division.division_num}', '{match.equipe_domicile.id}', '{match.equipe_exterieur.id}', NULL, 'NOT_CONFIRMED', NULL)"
                        unscheduled_values.append(values)
                    
                    f.write(',\n'.join(unscheduled_values))
                    f.write(';\n\n')
                
                # Statistiques finales
                f.write("-- Statistiques\n")
                total_matches = len(self.matches) + (len(self.unscheduled_matches) if hasattr(self, 'unscheduled_matches') else 0)
                f.write(f"-- Total matchs: {total_matches}\n")
                f.write(f"-- Matchs programmés: {len(self.matches)}\n")
                if hasattr(self, 'unscheduled_matches') and self.unscheduled_matches:
                    f.write(f"-- Matchs non programmés: {len(self.unscheduled_matches)}\n")
                
                divisions_count = {}
                for match in self.matches:
                    div_key = f"{match.division.code_competition}{match.division.division_num}"
                    divisions_count[div_key] = divisions_count.get(div_key, 0) + 1
                
                for div, count in sorted(divisions_count.items()):
                    f.write(f"-- Division {div}: {count} matchs\n")
            
            print(f"[SUCCES] Fichier SQL genere: {filename}")
            print(f"[INFO] Ce fichier utilise exactement la même logique que la sauvegarde directe")
            print(f"[INFO] Vous pouvez maintenant:")
            print(f"[INFO] 1. Ouvrir phpMyAdmin")
            print(f"[INFO] 2. Sélectionner votre base de données")
            print(f"[INFO] 3. Aller dans l'onglet 'SQL'")
            print(f"[INFO] 4. Copier-coller le contenu de {filename}")
            print(f"[INFO] 5. Exécuter la requête")
            return True
            
        except Exception as e:
            print(f"[ERREUR] Impossible de générer le fichier SQL: {e}")
            return False

def main(competition_codes: List[str] = None):
    """Fonction principale.
    
    Args:
        competition_codes: Liste des codes de compétition (ex: ['c', 'kh'], ['m', 'f', 'mo'])
                          Par défaut: ['m', 'f', 'mo']
    """
    import sys
    import os
    from io import StringIO
    
    codes = competition_codes or ['m', 'f', 'mo']
    
    # Configurer le logging dans un fichier
    script_dir = os.path.dirname(os.path.abspath(__file__))
    codes_suffix = "_".join(codes)
    log_filename = os.path.join(script_dir, f"generation_{codes_suffix}.log")
    
    # Classe pour dupliquer la sortie vers fichier et console
    class TeeOutput:
        def __init__(self, filename):
            self.terminal = sys.stdout
            self.log = open(filename, 'w', encoding='utf-8')
        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)
        def flush(self):
            self.terminal.flush()
            self.log.flush()
        def close(self):
            self.log.close()
    
    tee = TeeOutput(log_filename)
    sys.stdout = tee
    
    print("GÉNÉRATEUR DE CALENDRIER UFOLEP - VERSION MYSQL FINALE")
    print(f"Compétitions: {codes}")
    print(f"Fichier log: {log_filename}")
    print("="*60)
    
    scheduler = UfolepMySQLScheduler(codes)
    
    # Charger les données
    if not scheduler.load_data():
        return
    
    # Afficher les équipes sans créneaux de réception (info seulement, pas de filtrage)
    teams_with_reception = [t for t in scheduler.teams if t.time_slots]
    teams_without_reception = [t for t in scheduler.teams if not t.time_slots]
    
    print(f"\n[INFO] ANALYSE DES CRÉNEAUX:")
    print(f"   - Équipes avec créneaux de réception: {len(teams_with_reception)}")
    print(f"   - Équipes sans créneaux (joueront toujours à l'extérieur): {len(teams_without_reception)}")
    
    if teams_without_reception:
        print("\n[INFO] ÉQUIPES SANS CRÉNEAUX:")
        for team in teams_without_reception:
            print(f"   - {team.nom} (Division {team.division_id})")
    
    # # Validation des données d'entrée (contraintes clubs)
    # all_clubs_valid, valid_club_ids = scheduler.validate_club_capacity()
    #
    # if not all_clubs_valid:
    #     print("\n[WARNING] CLUBS NON-CONFORMES DETECTES: Filtrage en cours...")
    #     scheduler.filter_teams_by_valid_clubs(valid_club_ids)
    #
    #     if len(scheduler.teams) == 0:
    #         print("\n[ERROR] ERREUR: Aucune equipe restante apres filtrage!")
    #         print("Tous les clubs ont des violations. Impossible de générer un calendrier.")
    #         return
    #
    #     print(f"\n[OK] FILTRAGE TERMINE: Generation avec {len(scheduler.teams)} equipes conformes.")
    
    # Générer le calendrier
    if scheduler.generate_schedule():
        scheduler.print_schedule()
        
        # Validation des contraintes gymnases
        scheduler.validate_gymnasium_capacity()
        
        # Validation de l'équilibre dom/ext
        scheduler.validate_home_balance()
        
        # Génération automatique du fichier SQL
        print("\n" + "="*60)
        print("GÉNÉRATION DU FICHIER SQL...")
        
        # Nom de fichier basé sur les compétitions (dans le même dossier que le script)
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        codes_suffix = "_".join(codes)
        filename = os.path.join(script_dir, f"insert_matches_{codes_suffix}.sql")
        
        if scheduler.generate_sql_file(filename):
            print("\n[OK] FICHIER SQL GENERE AVEC SUCCES!")
            print(f"Fichier: {filename}")
            if hasattr(scheduler, 'unscheduled_matches') and scheduler.unscheduled_matches:
                print(f"[ATTENTION] {len(scheduler.unscheduled_matches)} matchs non programmes inclus (sans date)")
            print("Vous pouvez maintenant l'utiliser dans phpMyAdmin.")
        else:
            print("\n[ERREUR] Impossible de generer le fichier SQL.")
    else:
        print("[ERREUR] Échec de la génération du calendrier")
    
    # Fermer le fichier de log
    sys.stdout = tee.terminal
    tee.close()
    print(f"\n[INFO] Log sauvegardé dans: {log_filename}")

if __name__ == "__main__":
    main()
