#!/usr/bin/env python3
"""
Script de génération des huitièmes de finale pour les coupes UFOLEP.

Génère les matchs des huitièmes de finale à partir du tirage au sort
stocké dans la table registry, puis utilise UfolepMySQLScheduler pour
la planification des dates et gymnases.

Usage:
    python generate_huitiemes_v2.py cf    # Huitièmes coupe Isoardi (parent: c)
    python generate_huitiemes_v2.py kf    # Huitièmes coupe KH (parent: kh)
    python generate_huitiemes_v2.py cf kf # Les deux coupes (planification conjointe)
"""

import os
import re
import sys
from dataclasses import dataclass
from datetime import date, time, datetime, timedelta
from typing import List, Dict, Optional

import mysql.connector

from db_config import DB_CONFIG, TABLE_NAMES, COLUMN_MAPPING
from ufolep_mysql_final import UfolepMySQLScheduler, PredefinedMatch, Division, Team


# Mapping compétition finale -> compétition parente
PARENT_COMPETITION = {
    'cf': 'c',   # Coupe finale Isoardi <- Coupe Isoardi
    'kf': 'kh',  # Coupe finale KH <- Coupe KH
}


@dataclass
class TeamData:
    """Données d'une équipe."""
    id: int
    nom: str
    club_id: int


@dataclass
class MatchHuitieme:
    """Match de huitième de finale."""
    match_num: int
    code_competition: str
    home_team: Optional[TeamData]
    away_team: Optional[TeamData]
    team1_label: str
    team2_label: str


class HuitiemesDrawLoader:
    """Charge le tirage au sort des huitièmes depuis la BDD."""
    
    def __init__(self, code_finals: str):
        self.code_finals = code_finals
        self.code_parent = PARENT_COMPETITION.get(code_finals)
        self.connection = None
        self.matches: List[MatchHuitieme] = []
    
    def load(self, connection) -> List[MatchHuitieme]:
        """Charge les matchs du tirage au sort."""
        self.connection = connection
        
        # Récupérer le tirage brut
        raw_draw = self._get_finals_draw_raw()
        if not raw_draw:
            print(f"[ERREUR] Aucun tirage trouvé pour {self.code_finals}")
            return []
        
        # Récupérer les classements
        rankings = self._get_pool_rankings()
        if not rankings:
            print(f"[ERREUR] Aucun classement trouvé pour {self.code_parent}")
            return []
        
        # Récupérer le tirage de réception
        host_draw = self._get_host_draw()
        
        # Résoudre chaque match
        self.matches = []
        for match_num, match_data in raw_draw.items():
            team1_label = match_data.get('team1', '')
            team2_label = match_data.get('team2', '')
            
            team1 = self._resolve_position(team1_label, rankings)
            team2 = self._resolve_position(team2_label, rankings)
            
            # Déterminer qui reçoit selon le tirage
            host_team_num = host_draw.get(match_num, 1)
            if host_team_num == 1:
                home_team, away_team = team1, team2
            else:
                home_team, away_team = team2, team1
            
            match = MatchHuitieme(
                match_num=match_num,
                code_competition=self.code_finals,
                home_team=home_team,
                away_team=away_team,
                team1_label=team1_label,
                team2_label=team2_label
            )
            self.matches.append(match)
        
        print(f"[OK] {len(self.matches)} matchs de huitièmes chargés pour {self.code_finals}")
        return self.matches
    
    def _get_finals_draw_raw(self) -> Dict[int, Dict[str, str]]:
        """Récupère le tirage au sort brut depuis la table registry."""
        cursor = self.connection.cursor(dictionary=True)
        
        pattern = f"finals_draw.{self.code_finals}.1_8.%"
        query = "SELECT registry_key, registry_value FROM registry WHERE registry_key LIKE %s"
        cursor.execute(query, (pattern,))
        entries = cursor.fetchall()
        cursor.close()
        
        matches = {}
        for entry in entries:
            key = entry['registry_key']
            value = entry['registry_value']
            parts = key.split('.')
            if len(parts) != 5:
                continue
            match_num = int(parts[3])
            side = parts[4]
            if match_num not in matches:
                matches[match_num] = {}
            matches[match_num][side] = value
        
        print(f"[OK] Tirage récupéré: {len(matches)} matchs pour {self.code_finals}")
        return dict(sorted(matches.items()))
    
    def _get_pool_rankings(self) -> Dict[str, List[Dict]]:
        """Récupère le classement des poules (requête get_rank_for_cup.sql)."""
        cursor = self.connection.cursor(dictionary=True)
        
        query = """
        SELECT @r := @r + 1 AS rang, z.*
        FROM (SELECT e.id_equipe, e.nom_equipe, e.id_club, c.code_competition, c.division,
                     (SELECT rv.rang FROM ranks_view rv 
                      WHERE rv.code_competition = c.code_competition 
                        AND rv.division = c.division 
                        AND rv.id_equipe = e.id_equipe) AS rang_poule,
                     (SUM(IF(e.id_equipe = m.id_equipe_dom AND m.score_equipe_dom = 3, 3, 0)) +
                      SUM(IF(e.id_equipe = m.id_equipe_ext AND m.score_equipe_ext = 3, 3, 0)) +
                      SUM(IF(e.id_equipe = m.id_equipe_dom AND m.score_equipe_ext = 3 AND m.forfait_dom = 0, 1, 0)) +
                      SUM(IF(e.id_equipe = m.id_equipe_ext AND m.score_equipe_dom = 3 AND m.forfait_ext = 0, 1, 0))
                      - c.penalite) / NULLIF((SUM(IF(e.id_equipe = m.id_equipe_dom, 1, 0)) +
                                              SUM(IF(e.id_equipe = m.id_equipe_ext, 1, 0))), 0) AS points_ponderes,
                     (SUM(IF(e.id_equipe = m.id_equipe_dom, m.score_equipe_dom, m.score_equipe_ext)) -
                      SUM(IF(e.id_equipe = m.id_equipe_dom, m.score_equipe_ext, m.score_equipe_dom))) / 
                      NULLIF((SUM(IF(e.id_equipe = m.id_equipe_dom, 1, 0)) +
                              SUM(IF(e.id_equipe = m.id_equipe_ext, 1, 0))), 0) AS diff_sets_ponderes,
                     (SUM(IF(m.id_equipe_dom = e.id_equipe, m.set_1_dom + m.set_2_dom + m.set_3_dom + m.set_4_dom + m.set_5_dom,
                             m.set_1_ext + m.set_2_ext + m.set_3_ext + m.set_4_ext + m.set_5_ext)) - 
                      SUM(IF(m.id_equipe_dom = e.id_equipe, m.set_1_ext + m.set_2_ext + m.set_3_ext + m.set_4_ext + m.set_5_ext,
                             m.set_1_dom + m.set_2_dom + m.set_3_dom + m.set_4_dom + m.set_5_dom))) /
                      NULLIF((SUM(IF(e.id_equipe = m.id_equipe_dom, 1, 0)) +
                              SUM(IF(e.id_equipe = m.id_equipe_ext, 1, 0))), 0) AS diff_points_ponderes
              FROM classements c
              JOIN equipes e ON e.id_equipe = c.id_equipe
              LEFT JOIN matchs_view m ON m.code_competition = c.code_competition
                  AND m.division = c.division
                  AND (m.id_equipe_dom = e.id_equipe OR m.id_equipe_ext = e.id_equipe)
                  AND m.match_status != 'ARCHIVED'
              WHERE c.code_competition = %s
              GROUP BY e.id_equipe, e.nom_equipe, e.id_club, c.code_competition, c.division, c.penalite, c.report_count, c.rank_start
              ORDER BY points_ponderes DESC, diff_sets_ponderes DESC, diff_points_ponderes DESC, c.rank_start) z,
             (SELECT @r := 0) y
        """
        
        cursor.execute(query, (self.code_parent,))
        results = cursor.fetchall()
        cursor.close()
        
        rankings_by_pool = {}
        for row in results:
            division = str(row['division'])
            if division not in rankings_by_pool:
                rankings_by_pool[division] = []
            row['points_ponderes'] = float(row['points_ponderes'] or 0)
            row['diff_sets_ponderes'] = float(row['diff_sets_ponderes'] or 0)
            row['diff_points_ponderes'] = float(row['diff_points_ponderes'] or 0)
            rankings_by_pool[division].append(row)
        
        for division in rankings_by_pool:
            rankings_by_pool[division].sort(key=lambda t: t.get('rang_poule') or 999)
        
        print(f"[OK] Classements récupérés: {len(rankings_by_pool)} poules pour {self.code_parent}")
        return rankings_by_pool
    
    def _get_host_draw(self) -> Dict[int, int]:
        """Récupère le tirage de réception."""
        cursor = self.connection.cursor(dictionary=True)
        
        pattern = f"finals_host_draw.{self.code_finals}.1_8.%"
        query = "SELECT registry_key, registry_value FROM registry WHERE registry_key LIKE %s"
        cursor.execute(query, (pattern,))
        entries = cursor.fetchall()
        cursor.close()
        
        host_draw = {}
        for entry in entries:
            parts = entry['registry_key'].split('.')
            if len(parts) == 4:
                host_draw[int(parts[3])] = int(entry['registry_value'])
        
        return host_draw
    
    def _resolve_position(self, position_label: str, rankings_by_pool: Dict[str, List[Dict]]) -> Optional[TeamData]:
        """Résout une position vers une équipe réelle."""
        if not position_label:
            return None
        
        # Pattern "1er poule X"
        match = re.match(r'^1er poule (\d+)$', position_label)
        if match:
            pool = match.group(1)
            if pool in rankings_by_pool and len(rankings_by_pool[pool]) >= 1:
                team = rankings_by_pool[pool][0]
                return TeamData(id=team['id_equipe'], nom=team['nom_equipe'], club_id=team['id_club'])
            return None
        
        # Pattern "2e poule X"
        match = re.match(r'^2e poule (\d+)$', position_label)
        if match:
            pool = match.group(1)
            if pool in rankings_by_pool and len(rankings_by_pool[pool]) >= 2:
                team = rankings_by_pool[pool][1]
                return TeamData(id=team['id_equipe'], nom=team['nom_equipe'], club_id=team['id_club'])
            return None
        
        # Pattern "meilleur 2e X/Y"
        match = re.match(r'^meilleur 2e (\d+)/(\d+)$', position_label)
        if match:
            nth = int(match.group(1))
            seconds = [teams[1] for teams in rankings_by_pool.values() if len(teams) >= 2]
            seconds.sort(key=lambda t: (-t.get('points_ponderes', 0), -t.get('diff_sets_ponderes', 0), -t.get('diff_points_ponderes', 0)))
            if nth <= len(seconds):
                team = seconds[nth - 1]
                return TeamData(id=team['id_equipe'], nom=team['nom_equipe'], club_id=team['id_club'])
            return None
        
        print(f"[ATTENTION] Position non reconnue: {position_label}")
        return None


def main(competition_codes: List[str]):
    """Point d'entrée principal."""
    # Configurer le logging
    script_dir = os.path.dirname(os.path.abspath(__file__))
    codes_suffix = "_".join(competition_codes)
    log_filename = os.path.join(script_dir, f"generation_huitiemes_{codes_suffix}.log")
    
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
    
    print(f"GÉNÉRATEUR DE HUITIÈMES DE FINALE UFOLEP")
    print(f"Compétitions: {competition_codes}")
    print(f"Fichier log: {log_filename}")
    print("=" * 60)
    
    try:
        # Connexion à la BDD
        connection = mysql.connector.connect(**DB_CONFIG)
        print(f"[OK] Connexion réussie à la base {DB_CONFIG['database']}")
        
        # Charger les tirages pour toutes les compétitions
        all_matches: List[MatchHuitieme] = []
        for code in competition_codes:
            if code not in PARENT_COMPETITION:
                print(f"[ERREUR] Code compétition invalide: {code}")
                continue
            loader = HuitiemesDrawLoader(code)
            matches = loader.load(connection)
            all_matches.extend(matches)
        
        if not all_matches:
            print("[ERREUR] Aucun match à planifier")
            connection.close()
            return
        
        # Créer les matchs prédéfinis pour le scheduler
        # On crée une division fictive pour les huitièmes
        divisions_by_code = {}
        predefined_matches = []
        
        for match in all_matches:
            if not match.home_team or not match.away_team:
                print(f"[ATTENTION] Match incomplet: {match.team1_label} vs {match.team2_label}")
                continue
            
            # Créer une division fictive si nécessaire
            if match.code_competition not in divisions_by_code:
                divisions_by_code[match.code_competition] = Division(
                    id=f"{match.code_competition}_1_8",
                    nom=f"Huitièmes {match.code_competition.upper()}",
                    code_competition=match.code_competition,
                    division_num=1,
                    teams=[]
                )
            
            predef = PredefinedMatch(
                match_id=f"{match.code_competition}_{match.match_num}",
                home_team_id=str(match.home_team.id),
                away_team_id=str(match.away_team.id),
                division=divisions_by_code[match.code_competition]
            )
            predefined_matches.append(predef)
        
        print(f"\n[INFO] {len(predefined_matches)} matchs prédéfinis à planifier")
        
        # Utiliser le scheduler avec les matchs prédéfinis
        # On doit charger les équipes des compétitions parentes (c, kh) car les équipes
        # des huitièmes sont inscrites dans ces compétitions
        parent_codes = list(set(PARENT_COMPETITION[code] for code in competition_codes if code in PARENT_COMPETITION))
        scheduler = UfolepMySQLScheduler(parent_codes, predefined_matches=predefined_matches)
        
        if not scheduler.load_data():
            print("[ERREUR] Impossible de charger les données")
            connection.close()
            return
        
        # IMPORTANT: Forcer les dates des compétitions finales (cf, kf), pas des parentes (c, kh)
        # Les huitièmes se jouent sur les 2 premières semaines de juin
        cursor = connection.cursor(dictionary=True)
        start_date = None
        end_date = None
        for code in competition_codes:
            cursor.execute("SELECT start_date, limit_register_date FROM competitions WHERE code_competition = %s", (code,))
            result = cursor.fetchone()
            if result and result['start_date']:
                comp_start = result['start_date']
                # Utiliser limit_register_date si défini, sinon 2 semaines pour les huitièmes
                comp_end = result.get('limit_register_date') or (comp_start + timedelta(weeks=2))
                if start_date is None or comp_start < start_date:
                    start_date = comp_start
                if end_date is None or comp_end > end_date:
                    end_date = comp_end
        cursor.close()
        
        if start_date and end_date:
            scheduler.start_date = start_date
            scheduler.end_date = end_date
            print(f"[OK] Dates forcées pour les finales: {start_date} au {end_date}")
        
        if not scheduler.generate_schedule():
            print("[ERREUR] Impossible de générer le calendrier")
            connection.close()
            return
        
        # Afficher le résumé et générer les fichiers SQL
        scheduler.print_schedule()
        
        # Générer un fichier SQL par compétition (filtré)
        for code in competition_codes:
            filename = os.path.join(script_dir, f"insert_huitiemes_{code}.sql")
            scheduler.generate_sql_file(filename, filter_competition=code)
        
        connection.close()
        print("[INFO] Connexion MySQL fermée")
        
    finally:
        sys.stdout = tee.terminal
        tee.close()
        print(f"\n[INFO] Log sauvegardé dans: {log_filename}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        codes = sys.argv[1:]
    else:
        print("Usage: python generate_huitiemes_v2.py <code_competition> [code_competition2 ...]")
        print("  Codes valides: cf (coupe Isoardi), kf (coupe KH)")
        print("\nExemples:")
        print("  python generate_huitiemes_v2.py cf")
        print("  python generate_huitiemes_v2.py kf")
        print("  python generate_huitiemes_v2.py cf kf")
        sys.exit(1)
    
    main(codes)
