#!/usr/bin/env python3
"""
Générateur de calendrier UFOLEP Volleyball - Version MySQL Finale
Utilise les données réelles de la base MySQL avec filtre sur les compétitions 'm', 'f', 'mo'
- Contraintes UFOLEP complètes avec OR-Tools CP-SAT
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

# Configuration des jours fériés et vacances Zone B 2025
JOURS_FERIES_2025 = [
    date(2025, 1, 1),   # Jour de l'An
    date(2025, 4, 21),  # Lundi de Pâques
    date(2025, 5, 1),   # Fête du Travail
    date(2025, 5, 8),   # Victoire 1945
    date(2025, 5, 29),  # Ascension
    date(2025, 6, 9),   # Lundi de Pentecôte
    date(2025, 7, 14),  # Fête Nationale
    date(2025, 8, 15),  # Assomption
    date(2025, 11, 1),  # Toussaint
    date(2025, 11, 11), # Armistice
    date(2025, 12, 25), # Noël
]

# Vacances scolaires Zone B 2025-2026
VACANCES_ZONE_B_2025 = [
    # Vacances de la Toussaint 2025
    (date(2025, 10, 19), date(2025, 11, 3)),
    # Vacances de Noël 2025
    (date(2025, 12, 21), date(2026, 1, 5)),
    # Vacances d'hiver 2026
    (date(2026, 2, 8), date(2026, 2, 23)),
    # Vacances de printemps 2026
    (date(2026, 4, 5), date(2026, 4, 20)),
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
    
    def __init__(self):
        self.db_loader = UfolepDatabaseLoader()
        self.divisions: List[Division] = []
        self.teams: List[Team] = []
        self.time_slots: List[TimeSlot] = []
        self.matches: List[Match] = []
        
        # Période de championnat
        self.start_date = date(2025, 11, 3)
        self.end_date = date(2025, 12, 19)
        
        # Jours de la semaine autorisés (1=Lundi, 5=Vendredi)
        self.allowed_weekdays = [1, 2, 3, 4, 5]
        
    def load_data(self) -> bool:
        """Charge les données depuis MySQL."""
        print("[INFO] Chargement des données MySQL UFOLEP...")
        
        if not self.db_loader.load_all_data():
            print("[ERREUR] Impossible de charger les données MySQL")
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
                    
                    team = Team(
                        id=equipe_data.id,
                        nom=equipe_data.nom,
                        club_id=equipe_data.club_id,
                        division_id=f"{equipe_data.classement.code_competition}_{equipe_data.classement.division}",
                        code_competition=equipe_data.classement.code_competition,
                        time_slots=equipe_time_slots
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
        if date_obj in JOURS_FERIES_2025:
            return False
            
        # Vérifier vacances scolaires
        for debut_vacances, fin_vacances in VACANCES_ZONE_B_2025:
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
    
    def _add_match_assignment_constraints(self, model: cp_model.CpModel, matches_data: list) -> None:
        """Contrainte : Chaque match doit être programmé exactement une fois."""
        print("[INFO] Application contrainte : chaque match programmé exactement une fois...")
        
        matches_by_id = {}
        for match_data in matches_data:
            mid = match_data['match_id']
            if mid not in matches_by_id:
                matches_by_id[mid] = []
            matches_by_id[mid].append(match_data['var'])
        
        for match_id, vars_list in matches_by_id.items():
            model.Add(sum(vars_list) == 1)
        
        print(f"[INFO] {len(matches_by_id)} contraintes d'assignation de matchs ajoutées")
    
    def _add_team_date_constraints(self, model: cp_model.CpModel, matches_data: list) -> None:
        """Contrainte : Une équipe ne peut jouer qu'un match par date."""
        print("[INFO] Application contrainte : max 1 match par équipe par date...")
        
        team_date_vars = {}
        for match_data in matches_data:
            home_team = match_data['home_team']
            away_team = match_data['away_team']
            date_obj = match_data['date']
            var = match_data['var']
            
            # Équipe à domicile
            key = (home_team.id, date_obj)
            if key not in team_date_vars:
                team_date_vars[key] = []
            team_date_vars[key].append(var)
            
            # Équipe à l'extérieur
            key = (away_team.id, date_obj)
            if key not in team_date_vars:
                team_date_vars[key] = []
            team_date_vars[key].append(var)
        
        for (team_id, date_obj), vars_list in team_date_vars.items():
            model.Add(sum(vars_list) <= 1)
        
        print(f"[INFO] {len(team_date_vars)} contraintes équipe-date ajoutées")
    
    def _add_gymnasium_capacity_constraints(self, model: cp_model.CpModel, matches_data: list) -> None:
        """Contrainte : Capacité des gymnases respectée."""
        print("[INFO] Application contrainte : capacité gymnases...")
        
        gymnasium_date_vars = {}
        for match_data in matches_data:
            time_slot = match_data['time_slot']
            date_obj = match_data['date']
            var = match_data['var']
            
            # Grouper par gymnase + date (ignorer l'heure)
            key = (time_slot.gymnase_id, date_obj)
            if key not in gymnasium_date_vars:
                gymnasium_date_vars[key] = []
            gymnasium_date_vars[key].append(var)
        
        # Appliquer la contrainte : max nb_terrains matchs par gymnase par soirée
        constraints_added = 0
        for (gym_id, date_obj), vars_list in gymnasium_date_vars.items():
            gymnase = self.db_loader.gymnases.get(gym_id)
            max_terrains = gymnase.nb_terrains
            model.Add(sum(vars_list) <= max_terrains)
            constraints_added += 1
        
        print(f"[INFO] {constraints_added} contraintes de capacité gymnases ajoutées")
    
    def _add_weekly_match_limit_constraints(self, model: cp_model.CpModel, matches_data: list) -> dict:
        """Contrainte : Maximum 2 matchs par équipe par semaine.
        Retourne team_week_vars pour utilisation dans d'autres contraintes."""
        print("[INFO] Application contrainte : max 2 matchs par équipe par semaine...")
        
        team_week_vars = {}
        for match_data in matches_data:
            home_team = match_data['home_team']
            away_team = match_data['away_team']
            date_obj = match_data['date']
            var = match_data['var']
            
            # Calculer le numéro de semaine
            week_num = date_obj.isocalendar()[1]
            
            # Équipe à domicile
            key = (home_team.id, week_num)
            if key not in team_week_vars:
                team_week_vars[key] = []
            team_week_vars[key].append(var)
            
            # Équipe à l'extérieur
            key = (away_team.id, week_num)
            if key not in team_week_vars:
                team_week_vars[key] = []
            team_week_vars[key].append(var)
        
        for (team_id, week_num), vars_list in team_week_vars.items():
            model.Add(sum(vars_list) <= 2)
        
        print(f"[INFO] {len(team_week_vars)} contraintes hebdomadaires ajoutées")
        return team_week_vars
    
    def _add_weekly_home_constraints(self, model: cp_model.CpModel, matches_data: list, team_week_vars: dict) -> None:
        """Contrainte : Si une équipe joue 2 fois dans la semaine, elle doit recevoir au moins une fois."""
        print("[INFO] Application contrainte : 2 matchs/semaine -> au moins 1 domicile...")
        
        # Grouper les matchs par équipe/semaine en séparant domicile et extérieur
        team_week_home_vars = {}
        team_week_total_vars = {}
        
        for match_data in matches_data:
            home_team = match_data['home_team']
            away_team = match_data['away_team']
            date_obj = match_data['date']
            var = match_data['var']
            
            # Calculer le numéro de semaine
            week_num = date_obj.isocalendar()[1]
            
            # Équipe à domicile
            home_key = (home_team.id, week_num)
            if home_key not in team_week_home_vars:
                team_week_home_vars[home_key] = []
            if home_key not in team_week_total_vars:
                team_week_total_vars[home_key] = []
            team_week_home_vars[home_key].append(var)
            team_week_total_vars[home_key].append(var)
            
            # Équipe à l'extérieur (seulement dans total, pas dans home)
            away_key = (away_team.id, week_num)
            if away_key not in team_week_total_vars:
                team_week_total_vars[away_key] = []
            team_week_total_vars[away_key].append(var)
        
        # Appliquer la contrainte : si équipe joue 2 fois → au moins 1 domicile
        home_constraint_count = 0
        for (team_id, week_num), total_vars in team_week_total_vars.items():
            if len(total_vars) >= 2:  # Si l'équipe peut jouer 2 fois cette semaine
                home_key = (team_id, week_num)
                if home_key in team_week_home_vars:
                    home_vars = team_week_home_vars[home_key]
                    # Si l'équipe joue 2 fois (sum(total_vars) = 2), elle doit recevoir au moins 1 fois
                    # Contrainte: sum(total_vars) = 2 → sum(home_vars) ≥ 1
                    # Équivalent: sum(total_vars) ≤ 1 OU sum(home_vars) ≥ 1
                    # Implémentation: 2 - sum(total_vars) + sum(home_vars) ≥ 1
                    # Soit: sum(home_vars) ≥ sum(total_vars) - 1
                    model.Add(sum(home_vars) >= sum(total_vars) - 1)
                    home_constraint_count += 1
                else:
                    # CAS CRITIQUE : Équipe n'a que des matchs à l'extérieur cette semaine
                    # Si elle joue 2 fois, ce sera forcément 2 à l'extérieur = VIOLATION
                    # Contrainte: limiter à maximum 1 match cette semaine
                    model.Add(sum(total_vars) <= 1)
                    home_constraint_count += 1
                    print(f"[WARNING] Équipe {team_id} semaine {week_num}: que des matchs extérieur possibles, limitée à 1 match")
        
        print(f"[INFO] {home_constraint_count} contraintes 'au moins 1 domicile si 2 matchs/semaine' ajoutées")
    
    def _add_minimum_rest_constraints(self, model: cp_model.CpModel, matches_data: list) -> None:
        """Contrainte : Au moins 2 jours de repos entre 2 matchs d'une même équipe."""
        print("[INFO] Application contrainte : espacement minimum 2 jours entre matchs...")
        
        # Grouper les matchs par équipe et par date
        team_date_vars = {}
        for match_data in matches_data:
            home_team = match_data['home_team']
            away_team = match_data['away_team']
            date_obj = match_data['date']
            var = match_data['var']
            
            # Équipe à domicile
            key = (home_team.id, date_obj)
            if key not in team_date_vars:
                team_date_vars[key] = []
            team_date_vars[key].append(var)
            
            # Équipe à l'extérieur
            key = (away_team.id, date_obj)
            if key not in team_date_vars:
                team_date_vars[key] = []
            team_date_vars[key].append(var)
        
        # Appliquer la contrainte d'espacement pour chaque équipe
        team_dates = {}
        for (team_id, date_obj), vars_list in team_date_vars.items():
            if team_id not in team_dates:
                team_dates[team_id] = []
            team_dates[team_id].append((date_obj, vars_list))
        
        spacing_constraints_count = 0
        for team_id, date_vars_list in team_dates.items():
            # Trier les dates pour cette équipe
            date_vars_list.sort(key=lambda x: x[0])
            
            # Pour chaque paire de dates consécutives, vérifier l'espacement
            for i in range(len(date_vars_list)):
                for j in range(i + 1, len(date_vars_list)):
                    date1, vars1 = date_vars_list[i]
                    date2, vars2 = date_vars_list[j]
                    
                    # Calculer la différence en jours
                    days_diff = (date2 - date1).days
                    
                    # Si les dates sont trop proches (moins de 3 jours d'écart)
                    if days_diff < 3:
                        # Les deux matchs ne peuvent pas être sélectionnés en même temps
                        for var1 in vars1:
                            for var2 in vars2:
                                model.Add(var1 + var2 <= 1)
                                spacing_constraints_count += 1
        
        print(f"[INFO] {spacing_constraints_count} contraintes d'espacement ajoutées")
    
    def _add_home_percentage_constraints(self, model: cp_model.CpModel, matches_data: list) -> None:
        """Contrainte : Équipes avec créneaux de réception doivent jouer ≥30% de leurs matchs à domicile."""
        print("[INFO] Application contrainte : 30% domicile pour équipes avec réception...")
        
        # Identifier les équipes ayant des créneaux de réception (time_slots)
        teams_with_reception = set()
        for team in self.teams:
            if team.time_slots:  # Si l'équipe a des créneaux, elle peut recevoir
                teams_with_reception.add(team.id)
        
        print(f"[INFO] {len(teams_with_reception)} équipes avec créneaux de réception identifiées")
        
        # Compter les matchs par équipe et appliquer la contrainte 30%
        team_home_vars = {}
        
        for match_data in matches_data:
            home_team = match_data['home_team']
            var = match_data['var']
            
            # Compter les matchs à domicile
            if home_team.id not in team_home_vars:
                team_home_vars[home_team.id] = []
            team_home_vars[home_team.id].append(var)
        
        # Appliquer la contrainte 30% pour les équipes avec réception
        constraints_added = 0
        for team_id in teams_with_reception:
            if team_id in team_home_vars:
                # Calculer le nombre réel de matchs pour cette équipe
                # Une équipe joue contre toutes les autres de sa division
                team = next((t for t in self.teams if t.id == team_id), None)
                if team:
                    # Trouver la division de l'équipe
                    team_division = next((d for d in self.divisions if d.id == team.division_id), None)
                    if team_division:
                        total_matches = len(team_division.teams) - 1  # Contre toutes les autres équipes
                        home_vars = team_home_vars[team_id]
                        min_home_matches = math.ceil(total_matches * 0.3)  # 30% minimum, arrondi vers le haut
                        
                        # Contrainte: nombre de matchs à domicile ≥ 30% du total
                        model.Add(sum(home_vars) >= min_home_matches)
                        constraints_added += 1
                        
                        print(f"[CONTRAINTE] {team.nom}: >={min_home_matches}/{total_matches} matchs domicile (30%)")
        
        print(f"[INFO] {constraints_added} contraintes 30% domicile ajoutées")
    
    def _add_optimization_objective(self, model: cp_model.CpModel, team_week_vars: dict) -> None:
        """Fonction objectif : Minimiser le nombre d'équipes jouant 2 fois dans la même semaine."""
        print("[INFO] Application fonction objectif : minimiser équipes jouant 2 fois/semaine...")
        
        # Créer des variables binaires pour détecter les équipes jouant exactement 2 fois par semaine
        plays_2_vars = []
        teams_with_reception = {team.id for team in self.teams if team.time_slots}
        
        for (team_id, week_num), vars_list in team_week_vars.items():
            # Ne considérer que les équipes avec créneaux de réception pour l'optimisation
            if team_id in teams_with_reception and len(vars_list) >= 2:
                # Variable binaire : 1 si l'équipe joue exactement 2 fois cette semaine
                plays_2_var = model.NewBoolVar(f"plays_2_{team_id}_{week_num}")
                plays_2_vars.append(plays_2_var)
                
                # Contraintes logiques : plays_2_var = 1 ssi sum(vars_list) = 2
                # Méthode simple et correcte pour OR-Tools :
                
                # Contrainte 1: Si sum(vars_list) = 2, alors plays_2_var peut être 1
                # Contrainte 2: Si sum(vars_list) != 2, alors plays_2_var = 0
                
                # plays_2_var <= sum(vars_list) / 2 (mais sum max = 2, donc plays_2_var <= 1)
                # plays_2_var >= sum(vars_list) - 1 (si sum = 2, alors plays_2_var >= 1)
                # plays_2_var <= 3 - sum(vars_list) (si sum = 0 ou 1, alors plays_2_var <= 3-sum)
                
                model.Add(plays_2_var >= sum(vars_list) - 1)  # Force à 1 si sum = 2
                model.Add(plays_2_var <= sum(vars_list))      # Force à 0 si sum = 0
                model.Add(plays_2_var <= 3 - sum(vars_list)) # Force à 0 si sum = 1
        
        # Fonction objectif : minimiser le nombre d'équipes jouant 2 fois/semaine
        if plays_2_vars:
            model.Minimize(sum(plays_2_vars))
            print(f"[INFO] Fonction objectif configurée pour {len(plays_2_vars)} variables d'optimisation")
        else:
            print("[INFO] Aucune variable d'optimisation créée (pas d'équipes avec réception)")
    
    def generate_schedule(self) -> bool:
        """Génère le calendrier complet avec OR-Tools."""
        print("\n" + "="*60)
        print("GÉNÉRATION DU CALENDRIER UFOLEP MYSQL")
        print("="*60)
        
        # Calculer les besoins
        total_matches = self._calculate_matches_needed()
        valid_dates = self._generate_valid_dates()
        total_slots = len(self.time_slots) * len(valid_dates)
        
        print("\n[ANALYSE] Besoins vs Capacité:")
        print(f"  - Matchs à programmer: {total_matches}")
        print(f"  - Créneaux disponibles: {len(self.time_slots)}")
        print(f"  - Dates valides: {len(valid_dates)}")
        print(f"  - Slots totaux: {total_slots}")
        print(f"  - Ratio: {total_matches/total_slots:.2f} matchs/slot")
        
        if total_matches > total_slots:
            print(f"[ATTENTION] Pas assez de créneaux! Besoin: {total_matches}, Disponible: {total_slots}")

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
        
        print(f"[INFO] Variables créées: {len(matches_data)} possibilités pour {match_id} matchs")
        
        # Application des contraintes
        self._add_match_assignment_constraints(model, matches_data)
        self._add_team_date_constraints(model, matches_data)
        self._add_gymnasium_capacity_constraints(model, matches_data)
        team_week_vars = self._add_weekly_match_limit_constraints(model, matches_data)
        
        self._add_weekly_home_constraints(model, matches_data, team_week_vars)
        
        self._add_minimum_rest_constraints(model, matches_data)
        
        self._add_home_percentage_constraints(model, matches_data)
        
        self._add_optimization_objective(model, team_week_vars)
        
        print("[INFO] Résolution en cours avec optimisation...")
        
        # Résoudre
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 300.0  # 5 minutes max
        solver.parameters.log_search_progress = True
        
        status = solver.Solve(model)
        
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print(f"\n[SUCCÈS] Solution trouvée! Status: {solver.StatusName(status)}")
            
            # Extraire les matchs programmés
            self.matches = []
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
            
            print(f"[OK] {len(self.matches)} matchs programmés")
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
        print("CALENDRIER UFOLEP VOLLEYBALL - DONNÉES MYSQL RÉELLES")
        print("="*80)
        
        # Trier par date puis par heure
        sorted_matches = sorted(self.matches, key=lambda m: (m.date, m.time_slot.heure_debut))
        
        current_date = None
        matches_by_division = {}
        
        for match in sorted_matches:
            # Compter par division
            div_name = match.division.nom
            if div_name not in matches_by_division:
                matches_by_division[div_name] = 0
            matches_by_division[div_name] += 1
            
            # Affichage par date
            if current_date != match.date:
                current_date = match.date
                day_name = calendar.day_name[match.date.weekday()]
                print(f"\n{day_name} {match.date.strftime('%d/%m/%Y')}")
                print("-" * 50)
            
            # Trouver le gymnase
            gymnase = self.db_loader.gymnases.get(match.time_slot.gymnase_id)
            gym_name = gymnase.nom if gymnase else f"Gymnase {match.time_slot.gymnase_id}"
            
            print(f"  {match.time_slot.heure_debut.strftime('%H:%M')} - {gym_name}")
            print(f"    {match.equipe_domicile.nom} vs {match.equipe_exterieur.nom}")
            print(f"    Division: {match.division.nom}")
        
        # Statistiques
        print("\n" + "="*80)
        print("STATISTIQUES")
        print("="*80)
        print(f"Total matchs programmés: {len(self.matches)}")
        print(f"Période: {self.start_date.strftime('%d/%m/%Y')} - {self.end_date.strftime('%d/%m/%Y')}")
        
        print("\nRépartition par division:")
        for div_name, count in sorted(matches_by_division.items()):
            print(f"  {div_name}: {count} matchs")
        
        # Utilisation des créneaux (calcul correct)
        slots_used = set((m.time_slot.id, m.date) for m in self.matches)
        
        # Calculer les slots réellement disponibles (créneau × dates compatibles)
        valid_dates = self._generate_valid_dates()
        total_real_slots = 0
        
        for time_slot in self.time_slots:
            # Compter les dates où ce créneau est disponible
            compatible_dates = [d for d in valid_dates if d.weekday() + 1 == time_slot.jour_semaine]
            total_real_slots += len(compatible_dates) * time_slot.nb_terrains
        
        utilization = len(slots_used) / total_real_slots * 100 if total_real_slots > 0 else 0
        
        print("\nUtilisation des créneaux:")
        print(f"  Matchs programmés: {len(slots_used)}")
        print(f"  Slots réellement disponibles: {total_real_slots}")
        print("  (150 créneaux x ~4.7 dates compatibles x nb_terrains)")
        print(f"  Taux d'utilisation réel: {utilization:.1f}%")
        
        # Statistiques détaillées
        print("\nDétail par jour de la semaine:")
        for day_num in range(1, 6):  # Lundi à Vendredi
            day_name = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi'][day_num-1]
            day_slots = [ts for ts in self.time_slots if ts.jour_semaine == day_num]
            day_dates = [d for d in valid_dates if d.weekday() + 1 == day_num]
            day_matches = [m for m in self.matches if m.date.weekday() + 1 == day_num]
            
            total_day_capacity = sum(ts.nb_terrains for ts in day_slots) * len(day_dates)
            
            print(f"  {day_name}: {len(day_matches)} matchs / {total_day_capacity} slots disponibles "
                  f"({len(day_matches)/total_day_capacity*100:.1f}%)" if total_day_capacity > 0 else f"  {day_name}: 0 slots")
    
    def validate_gymnasium_capacity(self) -> bool:
        """Valide que la contrainte de capacité des gymnases est respectée à 100%."""
        print("\n" + "="*80)
        print("VALIDATION DES CONTRAINTES GYMNASES")
        print("="*80)
        
        violations = []
        gymnasium_usage = {}
        
        # Analyser l'utilisation par gymnase et date
        for match in self.matches:
            gym_id = match.time_slot.gymnase_id
            date_key = match.date
            
            key = (gym_id, date_key)
            if key not in gymnasium_usage:
                gymnasium_usage[key] = []
            gymnasium_usage[key].append(match)
        
        # Vérifier les violations
        for (gym_id, date_obj), matches_list in gymnasium_usage.items():
            # Trouver le gymnase et sa capacité
            gymnase = self.db_loader.gymnases.get(gym_id)
            if not gymnase:
                violations.append(f"Gymnase {gym_id} introuvable pour {date_obj}")
                continue
                
            max_capacity = gymnase.nb_terrains
            actual_usage = len(matches_list)
            
            if actual_usage > max_capacity:
                violations.append({
                    'gymnase': gymnase.nom,
                    'date': date_obj,
                    'capacity': max_capacity,
                    'usage': actual_usage,
                    'matches': matches_list
                })
        
        # Rapport de validation
        if violations:
            print(f"[ERROR] VIOLATIONS DETECTEES: {len(violations)} problemes")
            print("\nDétail des violations:")
            
            for i, violation in enumerate(violations, 1):
                if isinstance(violation, dict):
                    print(f"\n{i}. {violation['gymnase']} - {violation['date'].strftime('%d/%m/%Y')}")
                    print(f"   Capacité: {violation['capacity']} terrains")
                    print(f"   Utilisé: {violation['usage']} matchs")
                    print(f"   DÉPASSEMENT: +{violation['usage'] - violation['capacity']} matchs")
                    print("   Matchs concernés:")
                    for match in violation['matches']:
                        print(f"     - {match.time_slot.heure_debut.strftime('%H:%M')} : "
                              f"{match.equipe_domicile.nom} vs {match.equipe_exterieur.nom}")
                else:
                    print(f"{i}. {violation}")
            
            return False
        else:
            print("[OK] TOUTES LES CONTRAINTES RESPECTEES")
            print("Aucune violation de capacité détectée.")
            
            # Statistiques d'utilisation par gymnase
            print("\nUtilisation des gymnases:")
            gymnasium_stats = {}
            
            for (gym_id, date_obj), matches_list in gymnasium_usage.items():
                if gym_id not in gymnasium_stats:
                    gymnase = self.db_loader.gymnases.get(gym_id)
                    gymnasium_stats[gym_id] = {
                        'nom': gymnase.nom if gymnase else f"Gymnase {gym_id}",
                        'capacity': gymnase.nb_terrains if gymnase else 1,
                        'total_matches': 0,
                        'dates_used': 0,
                        'max_usage_per_date': 0
                    }
                
                gymnasium_stats[gym_id]['total_matches'] += len(matches_list)
                gymnasium_stats[gym_id]['dates_used'] += 1
                gymnasium_stats[gym_id]['max_usage_per_date'] = max(
                    gymnasium_stats[gym_id]['max_usage_per_date'], 
                    len(matches_list)
                )
            
            # Afficher les gymnases les plus utilisés
            sorted_gyms = sorted(gymnasium_stats.items(), 
                               key=lambda x: x[1]['total_matches'], reverse=True)[:10]
            
            print("\nTop 10 gymnases les plus utilisés:")
            for gym_id, stats in sorted_gyms:
                utilization = (stats['max_usage_per_date'] / stats['capacity']) * 100
                print(f"  {stats['nom']}: {stats['total_matches']} matchs, "
                      f"max {stats['max_usage_per_date']}/{stats['capacity']} terrains "
                      f"({utilization:.1f}% pic d'utilisation)")
            
            return True
    
    def validate_30_percent_home_rule(self):
        """Valide la règle des 30% minimum de matchs à domicile pour équipes avec réception"""
        print("\n" + "="*80)
        print("VALIDATION RÈGLE 30% DOMICILE (ÉQUIPES AVEC RÉCEPTION)")
        print("="*80)
        
        # Identifier les équipes avec créneaux de réception
        teams_with_reception = set()
        for team in self.teams:
            if team.time_slots:
                teams_with_reception.add(team.id)
        
        # Compter les matchs domicile/extérieur par équipe
        team_stats = {}
        for team in self.teams:
            team_stats[team.id] = {
                'team': team,
                'home': 0,
                'away': 0,
                'total': 0,
                'has_reception': team.id in teams_with_reception
            }
        
        for match in self.matches:
            home_team_id = match.equipe_domicile.id
            away_team_id = match.equipe_exterieur.id
            
            if home_team_id in team_stats:
                team_stats[home_team_id]['home'] += 1
                team_stats[home_team_id]['total'] += 1
            
            if away_team_id in team_stats:
                team_stats[away_team_id]['away'] += 1
                team_stats[away_team_id]['total'] += 1
        
        # Analyser le respect de la règle 30%
        compliant_teams = 0
        violation_teams = 0
        no_reception_teams = 0
        
        print("\nDétail par équipe:")
        print("Equipe | Domicile | Total | % Dom. | Min 30% | Reception | Statut")
        print("-" * 75)
        
        for team_id, stats in team_stats.items():
            if stats['total'] == 0:
                continue
            
            home = stats['home']
            total = stats['total']
            home_percentage = (home / total) * 100 if total > 0 else 0
            min_required = math.ceil(total * 0.3)  # 30% minimum, arrondi vers le haut
            has_reception = stats['has_reception']
            
            if not has_reception:
                status = "N/A (pas reception)"
                no_reception_teams += 1
            elif home >= min_required:
                status = "OK CONFORME"
                compliant_teams += 1
            else:
                status = "X VIOLATION"
                violation_teams += 1
            
            team_name = stats['team'].nom[:20]
            reception_str = "OUI" if has_reception else "NON"
            print(f"{team_name:<20} | {home:^8} | {total:^5} | {home_percentage:^6.1f} | {min_required:^7} | {reception_str:^9} | {status}")
        
        # Statistiques globales
        total_with_reception = compliant_teams + violation_teams
        print("\n" + "-" * 75)
        print("STATISTIQUES GLOBALES:")
        print(f"  Equipes avec creneaux de reception: {total_with_reception}")
        print(f"  Equipes conformes (>=30% domicile): {compliant_teams}/{total_with_reception} ({compliant_teams/total_with_reception*100:.1f}%)" if total_with_reception > 0 else "  Aucune equipe avec reception")
        print(f"  Equipes en violation (<30% domicile): {violation_teams}/{total_with_reception} ({violation_teams/total_with_reception*100:.1f}%)" if total_with_reception > 0 else "")
        print(f"  Equipes sans reception: {no_reception_teams}")
        
        # Resultat final
        if violation_teams == 0:
            print("\n[OK SUCCES] REGLE 30% DOMICILE RESPECTEE")
            print("Toutes les equipes avec reception jouent au moins 30% de leurs matchs a domicile.")
        else:
            print(f"\n[X ECHEC] {violation_teams} VIOLATIONS DE LA REGLE 30% DOMICILE")
            print("Certaines equipes avec reception ne jouent pas assez de matchs a domicile.")
        
        return violation_teams == 0

    def validate_minimum_rest_days(self):
        """Valide la règle d'espacement minimum de 2 jours entre 2 matchs d'une même équipe"""
        print("\n" + "="*80)
        print("VALIDATION RÈGLE ESPACEMENT MINIMUM 2 JOURS ENTRE MATCHS")
        print("="*80)
        
        # Grouper les matchs par équipe
        team_matches = {}
        for match in self.matches:
            home_team_id = match.equipe_domicile.id
            away_team_id = match.equipe_exterieur.id
            date_obj = match.date
            
            # Ajouter pour l'équipe à domicile
            if home_team_id not in team_matches:
                team_matches[home_team_id] = []
            team_matches[home_team_id].append((date_obj, match.equipe_domicile.nom))
            
            # Ajouter pour l'équipe à l'extérieur
            if away_team_id not in team_matches:
                team_matches[away_team_id] = []
            team_matches[away_team_id].append((date_obj, match.equipe_exterieur.nom))
        
        # Analyser l'espacement pour chaque équipe
        violation_count = 0
        violation_teams = []
        
        print("\nAnalyse par equipe:")
        print("Equipe | Violations | Detail des violations")
        print("-" * 70)
        
        for team_id, matches_list in team_matches.items():
            if len(matches_list) <= 1:
                continue  # Pas de problème avec 1 seul match
            
            # Trier les matchs par date
            matches_list.sort(key=lambda x: x[0])
            team_name = matches_list[0][1]
            
            team_violations = []
            
            # Vérifier l'espacement entre matchs consécutifs
            for i in range(len(matches_list) - 1):
                date1 = matches_list[i][0]
                date2 = matches_list[i + 1][0]
                days_diff = (date2 - date1).days
                
                if days_diff < 3:  # Moins de 3 jours d'écart = violation
                    violation_text = f"{date1.strftime('%d/%m')} -> {date2.strftime('%d/%m')} ({days_diff}j)"
                    team_violations.append(violation_text)
            
            if team_violations:
                violation_count += len(team_violations)
                violation_teams.append(team_name)
                violations_str = "; ".join(team_violations)
                print(f"{team_name[:20]:<20} | {len(team_violations):^10} | {violations_str}")
            else:
                print(f"{team_name[:20]:<20} | {0:^10} | OK - Espacement respecte")
        
        # Statistiques globales
        total_teams = len(team_matches)
        compliant_teams = total_teams - len(violation_teams)
        
        print("\n" + "-" * 70)
        print("STATISTIQUES GLOBALES:")
        print(f"  Equipes analysees: {total_teams}")
        print(f"  Equipes conformes (espacement >=2 jours): {compliant_teams}/{total_teams} ({compliant_teams/total_teams*100:.1f}%)" if total_teams > 0 else "  Aucune equipe")
        print(f"  Equipes en violation (<2 jours repos): {len(violation_teams)}/{total_teams} ({len(violation_teams)/total_teams*100:.1f}%)" if total_teams > 0 else "")
        print(f"  Total violations detectees: {violation_count}")
        
        # Resultat final
        if violation_count == 0:
            print("\n[OK SUCCES] REGLE ESPACEMENT 2 JOURS RESPECTEE")
            print("Toutes les equipes ont au moins 2 jours de repos entre leurs matchs.")
        else:
            print(f"\n[X ECHEC] {violation_count} VIOLATIONS DE LA REGLE ESPACEMENT")
            print("Certaines equipes n'ont pas assez de repos entre leurs matchs.")
            print("Equipes concernees:", ", ".join(violation_teams))
        
        return violation_count == 0

    def validate_weekly_home_constraint(self):
        """Valide la règle: si une équipe joue 2 fois dans la semaine, elle doit recevoir au moins une fois"""
        print("\n" + "="*80)
        print("VALIDATION REGLE: 2 MATCHS/SEMAINE -> AU MOINS 1 DOMICILE")
        print("="*80)
        
        # Grouper les matchs par équipe et par semaine
        team_week_matches = {}
        for match in self.matches:
            home_team_id = match.equipe_domicile.id
            away_team_id = match.equipe_exterieur.id
            date_obj = match.date
            week_num = date_obj.isocalendar()[1]
            
            # Équipe à domicile
            home_key = (home_team_id, week_num)
            if home_key not in team_week_matches:
                team_week_matches[home_key] = {'home': 0, 'away': 0, 'total': 0, 'team_name': match.equipe_domicile.nom}
            team_week_matches[home_key]['home'] += 1
            team_week_matches[home_key]['total'] += 1
            
            # Équipe à l'extérieur
            away_key = (away_team_id, week_num)
            if away_key not in team_week_matches:
                team_week_matches[away_key] = {'home': 0, 'away': 0, 'total': 0, 'team_name': match.equipe_exterieur.nom}
            team_week_matches[away_key]['away'] += 1
            team_week_matches[away_key]['total'] += 1
        
        # Analyser les violations
        violation_count = 0
        violation_details = []
        
        print("\nAnalyse par équipe/semaine:")
        print("Équipe | Semaine | Total | Domicile | Extérieur | Statut")
        print("-" * 75)
        
        for (team_id, week_num), stats in team_week_matches.items():
            team_name = stats['team_name']
            total = stats['total']
            home = stats['home']
            away = stats['away']
            
            if total == 2:  # Équipe joue 2 fois cette semaine
                if home == 0:  # Aucun match domicile = violation
                    status = "X VIOLATION (2 extérieur)"
                    violation_count += 1
                    violation_details.append(f"{team_name} (semaine {week_num})")
                else:
                    status = "OK CONFORME"
                
                print(f"{team_name[:20]:<20} | {week_num:^7} | {total:^5} | {home:^8} | {away:^9} | {status}")
        
        # Statistiques globales
        total_weeks_2_matches = sum(1 for stats in team_week_matches.values() if stats['total'] == 2)
        compliant_weeks = total_weeks_2_matches - violation_count
        
        print("\n" + "-" * 75)
        print("STATISTIQUES GLOBALES:")
        print(f"  Equipes jouant 2 fois/semaine: {total_weeks_2_matches}")
        print(f"  Semaines conformes (>=1 domicile): {compliant_weeks}/{total_weeks_2_matches} ({compliant_weeks/total_weeks_2_matches*100:.1f}%)" if total_weeks_2_matches > 0 else "  Aucune equipe ne joue 2 fois/semaine")
        print(f"  Semaines en violation (2 exterieur): {violation_count}/{total_weeks_2_matches} ({violation_count/total_weeks_2_matches*100:.1f}%)" if total_weeks_2_matches > 0 else "")
        print(f"  Total violations detectees: {violation_count}")
        
        # Résultat final
        if violation_count == 0:
            print("\n[OK SUCCES] REGLE 2 MATCHS/SEMAINE -> 1 DOMICILE RESPECTEE")
            print("Aucune equipe n'a 2 deplacements dans la meme semaine.")
        else:
            print(f"\n[X ECHEC] {violation_count} VIOLATIONS DE LA REGLE")
            print("Certaines equipes ont 2 deplacements dans la meme semaine.")
            print("Equipes concernees:", ", ".join(violation_details))
        
        return violation_count == 0

    def validate_teams_playing_twice_per_week(self):
        """Valide l'optimisation : mesure le nombre d'équipes jouant 2 fois dans la même semaine"""
        print("\n" + "="*80)
        print("VALIDATION OPTIMISATION : ÉQUIPES JOUANT 2 FOIS/SEMAINE")
        print("="*80)
        
        # Grouper les matchs par équipe et par semaine
        team_week_matches = {}
        for match in self.matches:
            home_team_id = match.equipe_domicile.id
            away_team_id = match.equipe_exterieur.id
            date_obj = match.date
            week_num = date_obj.isocalendar()[1]
            
            # Équipe à domicile
            home_key = (home_team_id, week_num)
            if home_key not in team_week_matches:
                team_week_matches[home_key] = {'count': 0, 'team_name': match.equipe_domicile.nom}
            team_week_matches[home_key]['count'] += 1
            
            # Équipe à l'extérieur
            away_key = (away_team_id, week_num)
            if away_key not in team_week_matches:
                team_week_matches[away_key] = {'count': 0, 'team_name': match.equipe_exterieur.nom}
            team_week_matches[away_key]['count'] += 1
        
        # Analyser les résultats
        teams_playing_twice = []
        teams_playing_once = []
        
        for (team_id, week_num), stats in team_week_matches.items():
            if stats['count'] == 2:
                teams_playing_twice.append((stats['team_name'], week_num))
            elif stats['count'] == 1:
                teams_playing_once.append((stats['team_name'], week_num))
        
        # Statistiques globales
        total_team_weeks = len(team_week_matches)
        teams_twice_count = len(teams_playing_twice)
        teams_once_count = len(teams_playing_once)
        
        print("\nRÉSULTATS DE L'OPTIMISATION:")
        print(f"  Total équipes-semaines analysées: {total_team_weeks}")
        print(f"  Équipes jouant 1 fois/semaine: {teams_once_count} ({teams_once_count/total_team_weeks*100:.1f}%)" if total_team_weeks > 0 else "")
        print(f"  Équipes jouant 2 fois/semaine: {teams_twice_count} ({teams_twice_count/total_team_weeks*100:.1f}%)" if total_team_weeks > 0 else "")
        
        if teams_playing_twice:
            print("\nDÉTAIL DES ÉQUIPES JOUANT 2 FOIS/SEMAINE:")
            teams_twice_sorted = sorted(teams_playing_twice, key=lambda x: (x[1], x[0]))
            current_week = None
            for team_name, week_num in teams_twice_sorted:
                if current_week != week_num:
                    current_week = week_num
                    print(f"\n  Semaine {week_num}:")
                print(f"    - {team_name}")
        
        # Évaluation du résultat
        if teams_twice_count == 0:
            print("\n[🎉 EXCELLENCE] OPTIMISATION PARFAITE ATTEINTE!")
            print("Aucune équipe ne joue 2 fois dans la même semaine.")
            print("Confort maximal pour toutes les équipes.")
        elif teams_twice_count <= total_team_weeks * 0.1:  # Moins de 10%
            print("\n[✅ TRÈS BON] OPTIMISATION RÉUSSIE!")
            print(f"Seulement {teams_twice_count} cas sur {total_team_weeks} ({teams_twice_count/total_team_weeks*100:.1f}%)")
            print("Résultat excellent avec la période étendue.")
        elif teams_twice_count <= total_team_weeks * 0.3:  # Moins de 30%
            print("\n[✅ BON] OPTIMISATION EFFICACE")
            print(f"{teams_twice_count} cas sur {total_team_weeks} ({teams_twice_count/total_team_weeks*100:.1f}%)")
            print("Amélioration significative par rapport à une génération sans optimisation.")
        else:
            print("\n[⚠️ MOYEN] OPTIMISATION PARTIELLE")
            print(f"{teams_twice_count} cas sur {total_team_weeks} ({teams_twice_count/total_team_weeks*100:.1f}%)")
            print("Considérer d'étendre encore la période ou assouplir d'autres contraintes.")
        
        return teams_twice_count

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
    
    def filter_teams_by_valid_clubs(self, valid_club_ids: set) -> None:
        """Filtre les équipes pour ne garder que celles des clubs conformes."""
        original_count = len(self.teams)
        original_divisions = len(self.divisions)
        
        # Filtrer les équipes
        self.teams = [team for team in self.teams if team.club_id in valid_club_ids]
        
        # Reconstruire les divisions avec les équipes filtrées
        teams_by_division = {}
        for team in self.teams:
            div_key = team.division_id
            if div_key not in teams_by_division:
                teams_by_division[div_key] = []
            teams_by_division[div_key].append(team)
        
        # Recréer les divisions avec les équipes filtrées
        filtered_divisions = []
        for division in self.divisions:
            if division.id in teams_by_division:
                teams_in_division = teams_by_division[division.id]
                
                # Ne garder que les divisions avec au moins 3 équipes
                if len(teams_in_division) >= 3:
                    division.teams = teams_in_division
                    filtered_divisions.append(division)
                else:
                    print(f"[INFO] Division {division.nom} supprimée: seulement {len(teams_in_division)} équipes restantes")
        
        self.divisions = filtered_divisions
        
        # Filtrer les créneaux pour ne garder que ceux des équipes valides
        valid_team_ids = {team.id for team in self.teams}
        self.time_slots = [ts for ts in self.time_slots if ts.equipe_id in valid_team_ids]
        
        # Rapport du filtrage
        teams_removed = original_count - len(self.teams)
        divisions_removed = original_divisions - len(self.divisions)
        
        print("\n[INFO] RESULTAT DU FILTRAGE:")
        print(f"   - Équipes conservées: {len(self.teams)} (supprimées: {teams_removed})")
        print(f"   - Divisions conservées: {len(self.divisions)} (supprimées: {divisions_removed})")
        print(f"   - Créneaux conservés: {len(self.time_slots)}")
    
    def filter_teams_with_reception_slots(self) -> None:
        """Filtre les équipes pour ne garder que celles ayant des créneaux de réception."""
        original_count = len(self.teams)
        original_divisions = len(self.divisions)
        
        # Identifier les équipes avec créneaux de réception
        teams_with_reception = []
        teams_without_reception = []
        
        for team in self.teams:
            if team.time_slots:  # Si l'équipe a des créneaux, elle peut recevoir
                teams_with_reception.append(team)
            else:
                teams_without_reception.append(team)
        
        print("\n[INFO] ANALYSE DES ÉQUIPES:")
        print(f"   - Équipes avec créneaux de réception: {len(teams_with_reception)}")
        print(f"   - Équipes sans créneaux de réception: {len(teams_without_reception)}")
        
        if teams_without_reception:
            print("\n[INFO] ÉQUIPES SANS CRÉNEAUX (EXCLUES):")
            for team in teams_without_reception:
                print(f"   - {team.nom} (Division {team.division_id})")
        
        # Filtrer les équipes pour ne garder que celles avec réception
        self.teams = teams_with_reception
        
        # Reconstruire les divisions avec les équipes filtrées
        teams_by_division = {}
        for team in self.teams:
            div_key = team.division_id
            if div_key not in teams_by_division:
                teams_by_division[div_key] = []
            teams_by_division[div_key].append(team)
        
        # Recréer les divisions avec les équipes filtrées
        filtered_divisions = []
        for division in self.divisions:
            if division.id in teams_by_division:
                teams_in_division = teams_by_division[division.id]
                
                # Ne garder que les divisions avec au moins 3 équipes
                if len(teams_in_division) >= 3:
                    division.teams = teams_in_division
                    filtered_divisions.append(division)
                else:
                    print(f"[INFO] Division {division.nom} supprimée: seulement {len(teams_in_division)} équipes avec réception")
        
        self.divisions = filtered_divisions
        
        # Filtrer les créneaux pour ne garder que ceux des équipes valides
        valid_team_ids = {team.id for team in self.teams}
        self.time_slots = [ts for ts in self.time_slots if ts.equipe_id in valid_team_ids]
        
        # Rapport du filtrage
        teams_removed = original_count - len(self.teams)
        divisions_removed = original_divisions - len(self.divisions)
        
        print("\n[INFO] RESULTAT DU FILTRAGE CRÉNEAUX DE RÉCEPTION:")
        print(f"   - Équipes conservées: {len(self.teams)} (supprimées: {teams_removed})")
        print(f"   - Divisions conservées: {len(self.divisions)} (supprimées: {divisions_removed})")
        print(f"   - Créneaux conservés: {len(self.time_slots)}")
    
    def generate_match_code(self, match: Match, match_index: int) -> str:
        """Génère un code unique pour le match."""
        # Format: COMP_DIV_YYYYMMDD_INDEX (ex: M_1_20251103_001)
        date_str = match.date.strftime('%Y%m%d')
        return f"{match.division.code_competition.upper()}_{match.division.division_num}_{date_str}_{match_index:03d}"
    
    def clear_existing_matches(self) -> bool:
        """Supprime uniquement les matchs NOT_CONFIRMED des championnats m/f/mo."""
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor()
            
            # Supprimer uniquement les matchs NOT_CONFIRMED des compétitions filtrées
            query = f"""
            DELETE FROM {TABLE_NAMES['matchs']} 
            WHERE {COLUMN_MAPPING['matches']['code_competition']} IN ('m', 'f', 'mo')
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
                f.write("-- Suppression uniquement des matchs NOT_CONFIRMED\n")
                f.write(f"DELETE FROM {TABLE_NAMES['matchs']} \n")
                f.write(f"WHERE {COLUMN_MAPPING['matches']['code_competition']} IN ('m', 'f', 'mo')\n")
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
                
                # Statistiques finales
                f.write("-- Statistiques\n")
                f.write(f"-- Total matchs insérés: {len(self.matches)}\n")
                
                divisions_count = {}
                for match in self.matches:
                    div_key = f"{match.division.code_competition}{match.division.division_num}"
                    divisions_count[div_key] = divisions_count.get(div_key, 0) + 1
                
                for div, count in sorted(divisions_count.items()):
                    f.write(f"-- Division {div}: {count} matchs\n")
            
            print(f"[SUCCÈS] Fichier SQL généré: {filename}")
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

def main():
    """Fonction principale."""
    print("GÉNÉRATEUR DE CALENDRIER UFOLEP - VERSION MYSQL FINALE")
    print("="*60)
    
    scheduler = UfolepMySQLScheduler()
    
    # Charger les données
    if not scheduler.load_data():
        return
    
    # Filtrer les équipes sans créneaux de réception
    print("\n[INFO] FILTRAGE DES ÉQUIPES SANS CRÉNEAUX DE RÉCEPTION...")
    scheduler.filter_teams_with_reception_slots()
    
    if len(scheduler.teams) == 0:
        print("\n[ERROR] ERREUR: Aucune équipe avec créneaux de réception!")
        print("Impossible de générer un calendrier sans équipes pouvant recevoir.")
        return
    
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
        
        # Validation critique des contraintes gymnases
        if not scheduler.validate_gymnasium_capacity():
            print("\n[ERROR] ERREUR CRITIQUE: Des violations de contraintes ont ete detectees!")
            print("Le calendrier ne peut pas être sauvegardé en l'état.")
            print("Veuillez corriger les problèmes avant de continuer.")
            return
        
        # Validation de la règle 30% domicile pour équipes avec réception
        scheduler.validate_30_percent_home_rule()
        
        # Validation de la règle espacement minimum 2 jours entre matchs
        scheduler.validate_minimum_rest_days()
        
        # Validation de la règle "2 matchs/semaine → au moins 1 domicile"
        scheduler.validate_weekly_home_constraint()
        
        # Validation de l'optimisation : équipes jouant 2 fois/semaine
        scheduler.validate_teams_playing_twice_per_week()
        
        # Demander le mode de sauvegarde
        print("\n" + "="*60)
        print("OPTIONS DE SAUVEGARDE:")
        print("1. Sauvegarde directe en base MySQL (connexion directe requise)")
        print("2. Génération fichier SQL pour phpMyAdmin (recommandé pour OVH)")
        print("3. Ne pas sauvegarder maintenant")
        
        try:
            save_choice = input("Votre choix (1/2/3): ").strip()
        except EOFError:
            print("Pas d'entrée interactive disponible. Génération du fichier SQL par défaut...")
            save_choice = "2"
        
        if save_choice == "1":
            # Sauvegarde directe
            if scheduler.save_schedule_to_database():
                print("\n🎉 CALENDRIER SAUVEGARDÉ AVEC SUCCÈS!")
                print(f"Les {len(scheduler.matches)} matchs ont été insérés dans votre base MySQL.")
                print("Status: Prêt pour validation UFOLEP.")
            else:
                print("\n❌ ERREUR lors de la sauvegarde directe.")
                print("Génération du fichier SQL en alternative...")
                scheduler.generate_sql_file()
                
        elif save_choice == "2":
            # Génération fichier SQL
            if scheduler.generate_sql_file():
                print("\n📄 FICHIER SQL GÉNÉRÉ AVEC SUCCÈS!")
                print("Vous pouvez maintenant l'utiliser dans phpMyAdmin.")
            else:
                print("\n❌ ERREUR lors de la génération du fichier SQL.")
                
        else:
            print("\n📋 Calendrier généré mais non sauvegardé.")
            print("Vous pouvez relancer le programme pour sauvegarder plus tard.")
    else:
        print("[ERREUR] Échec de la génération du calendrier")

if __name__ == "__main__":
    main()
