#!/usr/bin/env python3
"""
Script de génération incrémentale du calendrier pour une nouvelle équipe.

Génère uniquement les matchs d'une nouvelle équipe ajoutée à une division existante,
en respectant tous les matchs CONFIRMED existants (toutes compétitions confondues).

Contraintes respectées:
- Matchs CONFIRMED existants (dates bloquées pour les adversaires + gymnases occupés)
- Capacité des gymnases
- Max 1 match par équipe par semaine
- Max 1 match par équipe par date
- Indisponibilités gymnases (blacklist)
- Effectifs communs entre équipes

Usage:
    python generate_calendar_new_team.py
"""

import sys
import os
from datetime import datetime, date, timedelta, time as dt_time
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass

import mysql.connector
from ortools.sat.python import cp_model

from db_config import DB_CONFIG, TABLE_NAMES, COLUMN_MAPPING
from db_loader_real import UfolepDatabaseLoader

# Import des structures et constantes depuis le module principal
from ufolep_mysql_final import (
    TimeSlot, Team, Division, Match,
    JOURS_FERIES, VACANCES_ZONE_B,
    UfolepMySQLScheduler,
)


@dataclass
class ConfirmedMatch:
    """Match confirmé existant en BDD."""
    id_match: int
    code_competition: str
    division: str
    id_equipe_dom: str
    id_equipe_ext: str
    date_reception: date
    id_gymnasium: str


def load_all_confirmed_matches() -> List[ConfirmedMatch]:
    """Charge TOUS les matchs CONFIRMED/ARCHIVED de toutes les compétitions depuis la BDD."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        query = f"""
        SELECT 
            {COLUMN_MAPPING['matches']['id_match']},
            {COLUMN_MAPPING['matches']['code_competition']},
            {COLUMN_MAPPING['matches']['division']},
            {COLUMN_MAPPING['matches']['id_equipe_dom']},
            {COLUMN_MAPPING['matches']['id_equipe_ext']},
            {COLUMN_MAPPING['matches']['date_reception']},
            {COLUMN_MAPPING['matches']['id_gymnasium']}
        FROM {TABLE_NAMES['matchs']}
        WHERE {COLUMN_MAPPING['matches']['match_status']} IN ('CONFIRMED', 'ARCHIVED')
        AND {COLUMN_MAPPING['matches']['date_reception']} IS NOT NULL
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        matches = []
        for row in rows:
            date_val = row['date_reception']
            if isinstance(date_val, datetime):
                date_val = date_val.date()
            
            matches.append(ConfirmedMatch(
                id_match=row['id_match'],
                code_competition=row['code_competition'],
                division=str(row['division']),
                id_equipe_dom=str(row['id_equipe_dom']),
                id_equipe_ext=str(row['id_equipe_ext']),
                date_reception=date_val,
                id_gymnasium=str(row['id_gymnasium']) if row['id_gymnasium'] else None
            ))
        
        cursor.close()
        connection.close()
        
        print(f"[OK] {len(matches)} matchs confirmés chargés (toutes compétitions)")
        return matches
        
    except mysql.connector.Error as e:
        print(f"[ERREUR] Impossible de charger les matchs confirmés: {e}")
        return []


def build_constraints_from_confirmed(confirmed_matches: List[ConfirmedMatch]):
    """Construit les structures de contraintes à partir des matchs confirmés.
    
    Returns:
        team_blocked_dates: {team_id: set(dates)} - dates où chaque équipe joue déjà
        team_blocked_weeks: {team_id: set(week_nums)} - semaines où chaque équipe joue déjà
        gym_date_usage: {(gym_id, date): count} - nb de matchs par gymnase/date
    """
    team_blocked_dates: Dict[str, Set[date]] = {}
    team_blocked_weeks: Dict[str, Set[int]] = {}
    gym_date_usage: Dict[Tuple[str, date], int] = {}
    
    for m in confirmed_matches:
        # Bloquer la date pour les deux équipes
        for team_id in [m.id_equipe_dom, m.id_equipe_ext]:
            if team_id not in team_blocked_dates:
                team_blocked_dates[team_id] = set()
            team_blocked_dates[team_id].add(m.date_reception)
            
            if team_id not in team_blocked_weeks:
                team_blocked_weeks[team_id] = set()
            week_num = m.date_reception.isocalendar()[1]
            team_blocked_weeks[team_id].add(week_num)
        
        # Comptabiliser l'usage du gymnase
        if m.id_gymnasium:
            key = (m.id_gymnasium, m.date_reception)
            gym_date_usage[key] = gym_date_usage.get(key, 0) + 1
    
    return team_blocked_dates, team_blocked_weeks, gym_date_usage


def find_new_team(scheduler: UfolepMySQLScheduler, division_id: str, 
                  confirmed_matches: List[ConfirmedMatch]) -> Team:
    """Identifie la nouvelle équipe = celle qui n'a aucun match confirmé dans la division."""
    # Trouver la division cible
    target_division = None
    for div in scheduler.divisions:
        if div.id == division_id:
            target_division = div
            break
    
    if not target_division:
        print(f"[ERREUR] Division '{division_id}' non trouvée")
        print(f"[INFO] Divisions disponibles: {[d.id for d in scheduler.divisions]}")
        return None
    
    # Collecter les IDs d'équipes qui ont des matchs confirmés dans cette division
    teams_with_matches = set()
    for m in confirmed_matches:
        if m.code_competition == target_division.code_competition and m.division == str(target_division.division_num):
            teams_with_matches.add(m.id_equipe_dom)
            teams_with_matches.add(m.id_equipe_ext)
    
    # La nouvelle équipe est celle sans match confirmé
    new_teams = [t for t in target_division.teams if t.id not in teams_with_matches]
    
    if len(new_teams) == 0:
        print(f"[ERREUR] Toutes les équipes de {target_division.nom} ont déjà des matchs confirmés")
        return None
    elif len(new_teams) > 1:
        print(f"[ATTENTION] Plusieurs équipes sans matchs trouvées:")
        for t in new_teams:
            print(f"  - {t.nom} (ID: {t.id})")
        print(f"[INFO] Sélection de la première: {new_teams[0].nom}")
    
    return new_teams[0]


def generate_new_team_matches(scheduler: UfolepMySQLScheduler, 
                               new_team: Team, 
                               division: Division,
                               confirmed_matches: List[ConfirmedMatch]) -> List[Match]:
    """Génère les matchs de la nouvelle équipe avec OR-Tools."""
    
    team_blocked_dates, team_blocked_weeks, gym_date_usage = \
        build_constraints_from_confirmed(confirmed_matches)
    
    # Générer les dates valides
    valid_dates = scheduler._generate_valid_dates()
    print(f"[INFO] {len(valid_dates)} dates valides dans la période")
    
    # Identifier les adversaires (toutes les autres équipes de la division)
    opponents = [t for t in division.teams if t.id != new_team.id]
    print(f"[INFO] {len(opponents)} adversaires à planifier:")
    for opp in opponents:
        blocked = len(team_blocked_dates.get(opp.id, set()))
        print(f"  - {opp.nom} ({blocked} dates déjà bloquées)")
    
    # Créer le modèle OR-Tools
    model = cp_model.CpModel()
    matches_data = []
    match_id = 0
    
    for opponent in opponents:
        both_teams = [new_team, opponent]
        
        for date_obj in valid_dates:
            # Vérifier si l'une des deux équipes joue déjà ce jour
            new_team_blocked = date_obj in team_blocked_dates.get(new_team.id, set())
            opponent_blocked = date_obj in team_blocked_dates.get(opponent.id, set())
            
            if new_team_blocked or opponent_blocked:
                continue
            
            # Vérifier si l'une des deux équipes joue déjà cette semaine
            week_num = date_obj.isocalendar()[1]
            new_team_week_blocked = week_num in team_blocked_weeks.get(new_team.id, set())
            opponent_week_blocked = week_num in team_blocked_weeks.get(opponent.id, set())
            
            if new_team_week_blocked or opponent_week_blocked:
                continue
            
            # Essayer chaque créneau des deux équipes (match chez l'une ou l'autre)
            for home_team, away_team in [(new_team, opponent), (opponent, new_team)]:
                for time_slot in home_team.time_slots:
                    if date_obj.weekday() + 1 != time_slot.jour_semaine:
                        continue
                    
                    # Vérifier blacklist gymnase
                    if not scheduler.db_loader.is_gymnase_available(time_slot.gymnase_id, date_obj):
                        continue
                    
                    # Vérifier capacité gymnase restante (après matchs confirmés)
                    gym_key = (time_slot.gymnase_id, date_obj)
                    current_usage = gym_date_usage.get(gym_key, 0)
                    gymnase = scheduler.db_loader.gymnases.get(time_slot.gymnase_id)
                    if gymnase and current_usage >= gymnase.nb_terrains:
                        continue
                    
                    var_name = f"match_{match_id}_{home_team.id}_vs_{away_team.id}_{date_obj}_{time_slot.id}"
                    match_var = model.NewBoolVar(var_name)
                    
                    matches_data.append({
                        'var': match_var,
                        'match_id': match_id,
                        'home_team': home_team,
                        'away_team': away_team,
                        'date': date_obj,
                        'time_slot': time_slot,
                        'division': division
                    })
        
        match_id += 1
    
    if not matches_data:
        print("[ERREUR] Aucune combinaison possible trouvée")
        return []
    
    print(f"[INFO] {len(matches_data)} combinaisons possibles pour {match_id} matchs")
    
    # CONTRAINTE 1: Chaque match (paire d'équipes) programmé exactement 0 ou 1 fois, maximiser
    matches_by_id = {}
    for md in matches_data:
        mid = md['match_id']
        if mid not in matches_by_id:
            matches_by_id[mid] = []
        matches_by_id[mid].append(md['var'])
    
    for mid, vars_list in matches_by_id.items():
        model.Add(sum(vars_list) <= 1)
    
    # Maximiser le nombre de matchs programmés
    all_vars = [md['var'] for md in matches_data]
    model.Maximize(sum(all_vars))
    
    # CONTRAINTE 2: Max 1 match par équipe par date (parmi les nouveaux matchs)
    team_date_vars: Dict[Tuple[str, date], list] = {}
    for md in matches_data:
        for team in [md['home_team'], md['away_team']]:
            key = (team.id, md['date'])
            if key not in team_date_vars:
                team_date_vars[key] = []
            team_date_vars[key].append(md['var'])
    
    for vars_list in team_date_vars.values():
        model.Add(sum(vars_list) <= 1)
    
    # CONTRAINTE 3: Max 1 match par équipe par semaine (parmi les nouveaux matchs)
    team_week_vars: Dict[Tuple[str, int], list] = {}
    for md in matches_data:
        week_num = md['date'].isocalendar()[1]
        for team in [md['home_team'], md['away_team']]:
            key = (team.id, week_num)
            if key not in team_week_vars:
                team_week_vars[key] = []
            team_week_vars[key].append(md['var'])
    
    for vars_list in team_week_vars.values():
        model.Add(sum(vars_list) <= 1)
    
    # CONTRAINTE 4: Capacité gymnases (entre nouveaux matchs sur le même gymnase/date)
    gym_date_vars: Dict[Tuple[str, date], list] = {}
    for md in matches_data:
        key = (md['time_slot'].gymnase_id, md['date'])
        if key not in gym_date_vars:
            gym_date_vars[key] = []
        gym_date_vars[key].append(md['var'])
    
    for (gym_id, date_obj), vars_list in gym_date_vars.items():
        gymnase = scheduler.db_loader.gymnases.get(gym_id)
        if gymnase:
            existing_usage = gym_date_usage.get((gym_id, date_obj), 0)
            remaining_capacity = gymnase.nb_terrains - existing_usage
            if remaining_capacity > 0:
                model.Add(sum(vars_list) <= remaining_capacity)
            else:
                # Pas de capacité restante (ne devrait pas arriver vu le filtrage)
                model.Add(sum(vars_list) == 0)
    
    # CONTRAINTE 5: Effectifs communs - éviter que 2 équipes avec joueurs partagés jouent le même jour
    paires_effectif_commun = scheduler.db_loader.get_equipes_avec_effectif_commun()
    if paires_effectif_commun:
        # Dates bloquées par les matchs confirmés + nouveaux matchs
        all_team_date_vars = {}
        for md in matches_data:
            for team in [md['home_team'], md['away_team']]:
                key = (team.id, md['date'])
                if key not in all_team_date_vars:
                    all_team_date_vars[key] = []
                all_team_date_vars[key].append(md['var'])
        
        constraints_added = 0
        for e1_id, e2_id, nb_communs, ratio in paires_effectif_commun:
            # Vérifier si la nouvelle équipe ou ses adversaires sont impliqués
            if new_team.id not in (e1_id, e2_id):
                # Pas directement la nouvelle équipe, mais vérifier si un adversaire est impliqué
                pass
            
            for md in matches_data:
                match_date = md['date']
                # Si e1 a un match confirmé ce jour et e2 est impliquée dans un nouveau match
                if e1_id in team_blocked_dates.get(e1_id, set()) and match_date in team_blocked_dates.get(e1_id, set()):
                    vars_e2 = all_team_date_vars.get((e2_id, match_date), [])
                    if vars_e2:
                        model.Add(sum(vars_e2) == 0)
                        constraints_added += 1
                
                if e2_id in team_blocked_dates.get(e2_id, set()) and match_date in team_blocked_dates.get(e2_id, set()):
                    vars_e1 = all_team_date_vars.get((e1_id, match_date), [])
                    if vars_e1:
                        model.Add(sum(vars_e1) == 0)
                        constraints_added += 1
        
        if constraints_added > 0:
            print(f"[INFO] {constraints_added} contraintes effectif commun ajoutées")
    
    # CONTRAINTE 6: Alternance dom/ext basée sur l'historique
    teams_with_reception = {t.id for t in scheduler.teams if t.time_slots}
    pair_home_vars = {}
    
    for md in matches_data:
        home_id = md['home_team'].id
        away_id = md['away_team'].id
        pair = tuple(sorted([home_id, away_id]))
        if pair not in pair_home_vars:
            pair_home_vars[pair] = {pair[0]: [], pair[1]: []}
        pair_home_vars[pair][home_id].append(md['var'])
    
    forced = 0
    for opponent in opponents:
        pair = tuple(sorted([new_team.id, opponent.id]))
        if pair not in pair_home_vars:
            continue
        
        equipe_qui_doit_recevoir = scheduler.db_loader.get_equipe_qui_doit_recevoir(new_team.id, opponent.id)
        if equipe_qui_doit_recevoir:
            other_id = new_team.id if equipe_qui_doit_recevoir != new_team.id else opponent.id
            vars_other_home = pair_home_vars[pair].get(other_id, [])
            if vars_other_home and other_id in teams_with_reception:
                # Interdire que l'autre équipe reçoive
                model.Add(sum(vars_other_home) == 0)
                forced += 1
    
    if forced > 0:
        print(f"[INFO] {forced} réceptions forcées par l'historique")
    
    # CONTRAINTE 7: Équilibre dom/ext pour la nouvelle équipe
    # Avec N matchs, viser au moins (N-1)//2 matchs à domicile
    new_team_home_vars = [md['var'] for md in matches_data if md['home_team'].id == new_team.id]
    new_team_away_vars = [md['var'] for md in matches_data if md['away_team'].id == new_team.id]
    if new_team_home_vars:
        n_opponents = len(opponents)
        min_home = (n_opponents - 1) // 2  # 6 matchs -> min 2 dom
        model.Add(sum(new_team_home_vars) >= min_home)
        print(f"[INFO] Équilibre dom/ext: minimum {min_home} matchs à domicile imposé")
    
    # Résoudre
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60.0
    solver.parameters.log_search_progress = False
    
    print("\n[INFO] Résolution en cours...")
    status = solver.Solve(model)
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        result_matches = []
        for md in matches_data:
            if solver.Value(md['var']) == 1:
                match = Match(
                    id=f"new_match_{len(result_matches)}",
                    equipe_domicile=md['home_team'],
                    equipe_exterieur=md['away_team'],
                    date=md['date'],
                    time_slot=md['time_slot'],
                    division=md['division']
                )
                result_matches.append(match)
        
        # Identifier les matchs non programmés
        programmed_opponents = {
            m.equipe_exterieur.id if m.equipe_domicile.id == new_team.id else m.equipe_domicile.id
            for m in result_matches
        }
        unprogrammed = [opp for opp in opponents if opp.id not in programmed_opponents]
        
        print(f"\n[OK] {len(result_matches)}/{len(opponents)} matchs programmés")
        if unprogrammed:
            print(f"[ATTENTION] {len(unprogrammed)} matchs non programmés:")
            for opp in unprogrammed:
                print(f"  - vs {opp.nom}")
        
        return result_matches
    else:
        print(f"[ÉCHEC] Pas de solution trouvée. Status: {solver.StatusName(status)}")
        return []


def generate_sql_file(matches: List[Match], division: Division, filename: str) -> bool:
    """Génère un fichier SQL pour insérer uniquement les nouveaux matchs."""
    if not matches:
        print("[ERREUR] Aucun match à exporter")
        return False
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("-- Fichier SQL généré automatiquement - NOUVELLE EQUIPE\n")
            f.write(f"-- Date de génération: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-- Division: {division.nom}\n")
            f.write(f"-- Nombre de matchs: {len(matches)}\n")
            f.write("-- Supprime d'abord les éventuels matchs NOT_CONFIRMED de la nouvelle équipe\n")
            f.write("-- puis insère les nouveaux matchs\n\n")
            
            # Collecter les IDs d'équipe impliqués (la nouvelle équipe)
            new_team_ids = set()
            for match in matches:
                new_team_ids.add(match.equipe_domicile.id)
                new_team_ids.add(match.equipe_exterieur.id)
            # Garder uniquement l'ID qui apparaît dans tous les matchs (la nouvelle équipe)
            # = intersection des {dom, ext} de chaque match
            for match in matches:
                new_team_ids &= {match.equipe_domicile.id, match.equipe_exterieur.id}
            
            for team_id in new_team_ids:
                f.write(f"DELETE FROM {TABLE_NAMES['matchs']}\n")
                f.write(f"WHERE ({COLUMN_MAPPING['matches']['id_equipe_dom']} = '{team_id}' OR {COLUMN_MAPPING['matches']['id_equipe_ext']} = '{team_id}')\n")
                f.write(f"AND {COLUMN_MAPPING['matches']['match_status']} = 'NOT_CONFIRMED';\n\n")
            
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
            
            match_values = []
            for i, match in enumerate(matches, 1):
                date_str = match.date.strftime('%Y-%m-%d')
                match_code = f"{match.division.code_competition.upper()}_{match.division.division_num}_{date_str.replace('-', '')}_{i:03d}"
                values = (
                    f"('{match_code}', '{match.division.code_competition}', "
                    f"'{match.division.division_num}', '{match.equipe_domicile.id}', "
                    f"'{match.equipe_exterieur.id}', '{date_str}', "
                    f"'NOT_CONFIRMED', '{match.time_slot.gymnase_id}')"
                )
                match_values.append(values)
            
            f.write(',\n'.join(match_values))
            f.write(';\n')
        
        print(f"[OK] Fichier SQL généré: {filename}")
        return True
        
    except Exception as e:
        print(f"[ERREUR] Impossible de générer le fichier SQL: {e}")
        return False


def main():
    """Fonction principale."""
    # Configuration
    COMPETITION_CODE = 'f'  # Féminin
    DIVISION_NUM = '5'      # Division 5
    DIVISION_ID = f"{COMPETITION_CODE}_{DIVISION_NUM}"
    
    # Logging
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_filename = os.path.join(script_dir, "generation_new_team.log")
    
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
    
    print("=" * 60)
    print("GÉNÉRATION INCRÉMENTALE - NOUVELLE ÉQUIPE")
    print(f"Compétition: {COMPETITION_CODE} | Division: {DIVISION_NUM}")
    print("=" * 60)
    
    # Étape 1: Charger les données de la compétition féminine
    print("\n--- ÉTAPE 1: Chargement des données ---")
    scheduler = UfolepMySQLScheduler([COMPETITION_CODE])
    if not scheduler.load_data():
        sys.stdout = tee.terminal
        tee.close()
        return
    
    # Étape 2: Charger TOUS les matchs confirmés (toutes compétitions)
    print("\n--- ÉTAPE 2: Chargement des matchs confirmés (TOUTES compétitions) ---")
    confirmed_matches = load_all_confirmed_matches()
    if not confirmed_matches:
        print("[ATTENTION] Aucun match confirmé trouvé, on continue sans contraintes existantes")
    
    # Stats par compétition
    comp_stats = {}
    for m in confirmed_matches:
        comp_stats[m.code_competition] = comp_stats.get(m.code_competition, 0) + 1
    for comp, count in sorted(comp_stats.items()):
        print(f"  - {comp}: {count} matchs confirmés")
    
    # Étape 3: Identifier la nouvelle équipe
    print(f"\n--- ÉTAPE 3: Identification de la nouvelle équipe dans {DIVISION_ID} ---")
    new_team = find_new_team(scheduler, DIVISION_ID, confirmed_matches)
    if not new_team:
        sys.stdout = tee.terminal
        tee.close()
        return
    
    print(f"[OK] Nouvelle équipe identifiée: {new_team.nom} (ID: {new_team.id})")
    print(f"     Créneaux: {len(new_team.time_slots)}")
    for ts in new_team.time_slots:
        jours = ['', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        gym = scheduler.db_loader.gymnases.get(ts.gymnase_id)
        gym_nom = gym.nom if gym else ts.gymnase_id
        print(f"       - {jours[ts.jour_semaine]} {ts.heure_debut} @ {gym_nom}")
    
    # Trouver la division
    target_division = next(d for d in scheduler.divisions if d.id == DIVISION_ID)
    
    # Étape 4: Générer les matchs
    print(f"\n--- ÉTAPE 4: Génération des matchs ---")
    new_matches = generate_new_team_matches(scheduler, new_team, target_division, confirmed_matches)
    
    if not new_matches:
        print("[ERREUR] Aucun match généré")
        sys.stdout = tee.terminal
        tee.close()
        return
    
    # Afficher le calendrier
    print("\n" + "=" * 60)
    print("CALENDRIER DE LA NOUVELLE ÉQUIPE")
    print("=" * 60)
    
    sorted_matches = sorted(new_matches, key=lambda m: m.date)
    for match in sorted_matches:
        day_name = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][match.date.weekday()]
        gym = scheduler.db_loader.gymnases.get(match.time_slot.gymnase_id)
        gym_nom = gym.nom if gym else match.time_slot.gymnase_id
        
        if match.equipe_domicile.id == new_team.id:
            role = "DOM"
        else:
            role = "EXT"
        
        print(f"  {day_name} {match.date.strftime('%d/%m/%Y')} {match.time_slot.heure_debut.strftime('%H:%M')} "
              f"| {match.equipe_domicile.nom} vs {match.equipe_exterieur.nom} [{role}] @ {gym_nom}")
    
    # Stats dom/ext
    home_count = sum(1 for m in new_matches if m.equipe_domicile.id == new_team.id)
    away_count = len(new_matches) - home_count
    print(f"\n  Domicile: {home_count} | Extérieur: {away_count}")
    
    # Étape 5: Générer le fichier SQL
    print(f"\n--- ÉTAPE 5: Génération du fichier SQL ---")
    sql_filename = os.path.join(script_dir, f"insert_matches_new_team_{COMPETITION_CODE}_{DIVISION_NUM}.sql")
    generate_sql_file(new_matches, target_division, sql_filename)
    
    # Fermer le log
    sys.stdout = tee.terminal
    tee.close()
    print(f"\n[INFO] Log sauvegardé dans: {log_filename}")


if __name__ == "__main__":
    main()
