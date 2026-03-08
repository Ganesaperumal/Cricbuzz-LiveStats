import sqlite3
import glob
import json
import re
import os
import random
from datetime import datetime

conn = sqlite3.connect('utils/cricBuzz.db')
cursor = conn.cursor()


# ═══════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════

def capacity_to_int(capacity_str):
    """Extract digits only — handles '42000 (approx)', '132,000', etc."""
    if not capacity_str:
        return None
    try:
        digits = "".join(re.findall(r"\d", str(capacity_str)))
        return int(digits) if digits else None
    except (ValueError, TypeError):
        return None


def balls_to_overs(balls):
    """Convert integer balls to overs notation (e.g. 25 → 4.1)"""
    if balls is None:
        return None
    try:
        balls = int(balls)
        return int(balls / 6) + (balls % 6) / 10
    except (ValueError, TypeError):
        return None


def ts_to_date(ts):
    """Convert millisecond timestamp to YYYY-MM-DD string"""
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(int(ts) / 1000).strftime('%Y-%m-%d')
    except (ValueError, TypeError, OSError):
        return None


def normalize_match_format(fmt):
    """Normalize matchFormat strings to standard values"""
    if not fmt:
        return None
    fmt = str(fmt).strip().lower()
    mapping = {
        't20i': 'T20',
        't 20': 'T20',
        't20':  'T20',
        'odi':  'ODI',
        'test': 'TEST',
        'ipl':  'IPL',
    }
    return mapping.get(fmt, fmt.upper())


def scorecard_match_id(data):
    """Extract matchId from scorecard appindex weburl"""
    try:
        return data.get('appindex', {}).get('weburl', '').split('/')[-2].split('.')[0]
    except (IndexError, AttributeError):
        return None


def parse_winner(status, team1name, team1id, team2name, team2id):
    """
    Parse winningTeamId, winningType, winningMargin from status string.
    Covers all known status formats.
    """
    winningTeamId = winningType = winningMargin = None

    if not status:
        return winningTeamId, winningType, winningMargin

    s = status.strip()

    # Pattern 1: innings win
    m = re.search(r'^(.+?)\s+won\s+by\s+an\s+innings\s+and\s+(\d+)\s+runs', s, re.IGNORECASE)
    if m:
        winnerName = m.group(1).strip().lower()
        winningMargin = int(m.group(2))
        winningType = 'innings'
        if team1name and winnerName == str(team1name).strip().lower():
            winningTeamId = team1id
        elif team2name and winnerName == str(team2name).strip().lower():
            winningTeamId = team2id
        return winningTeamId, winningType, winningMargin

    # Pattern 2: runs or wkts win
    m = re.search(r'^(.+?)\s+won\s+by\s+(\d+)\s+(runs?|wkts?)', s, re.IGNORECASE)
    if m:
        winnerName = m.group(1).strip().lower()
        winningMargin = int(m.group(2))
        winningType = 'runs' if 'run' in m.group(3).lower() else 'wkts'
        if team1name and winnerName == str(team1name).strip().lower():
            winningTeamId = team1id
        elif team2name and winnerName == str(team2name).strip().lower():
            winningTeamId = team2id
        return winningTeamId, winningType, winningMargin

    # Pattern 3: won by (no margin)
    m = re.search(r'^(.+?)\s+won\s+by', s, re.IGNORECASE)
    if m:
        winnerName = m.group(1).strip().lower()
        if team1name and winnerName == str(team1name).strip().lower():
            winningTeamId = team1id
        elif team2name and winnerName == str(team2name).strip().lower():
            winningTeamId = team2id
        return winningTeamId, None, None

    # Pattern 4: tied
    if re.match(r'match tied', s, re.IGNORECASE):
        return None, 'tied', None

    # Pattern 5: abandoned
    if re.match(r'match abandoned', s, re.IGNORECASE):
        return None, 'abandoned', None

    # Pattern 6: drawn
    if re.match(r'match drawn', s, re.IGNORECASE):
        return None, 'drawn', None

    # Pattern 7: no result
    if re.match(r'no result', s, re.IGNORECASE):
        return None, 'no result', None

    # Pattern 8: cancelled
    if re.match(r'match cancelled', s, re.IGNORECASE):
        return None, 'cancelled', None

    # Pattern 9: in-progress / scheduled / anything else
    return None, None, None


# ═══════════════════════════════════════════════════════════
# TABLE 1 — teams
# ═══════════════════════════════════════════════════════════

def teams():
    cursor.execute("DROP TABLE IF EXISTS teams")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            teamId    INTEGER PRIMARY KEY,
            teamName  TEXT,
            teamSName TEXT,
            teamType  TEXT
        )
    """)

    rows = []
    
    for jsonfile in glob.glob('utils/json/2_teams/*.json'):
        teamType = jsonfile.split('_')[-1].split('.')[0]
        with open(jsonfile, 'r') as f:
            data = json.load(f)
        for team in data.get('list', []):
            if not team.get('teamId'):
                continue
            rows.append((
                team.get('teamId'),
                team.get('teamName'),
                team.get('teamSName'),
                teamType
            ))

    for jsonfile in glob.glob('utils/json/5_matches/lists/*.json'):
        with open(jsonfile, 'r') as f:
            data = json.load(f)
            
        for type_match in data.get('typeMatches', []):
            teamType = type_match.get('matchType')
            for series_match in type_match.get('seriesMatches', []):
                if 'seriesAdWrapper' not in series_match:
                    continue
                    
                for match in series_match['seriesAdWrapper'].get('matches', []):
                    match_info = match.get('matchInfo', {})
                    
                    for team_key in ['team1', 'team2']:
                        team = match_info.get(team_key)
                        if team and team.get('teamId'):
                            rows.append((
                                team.get('teamId'),
                                team.get('teamName'),
                                team.get('teamSName'),
                                teamType
                            ))

    cursor.executemany("""
        INSERT INTO teams (teamId, teamName, teamSName, teamType)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(teamId) DO UPDATE SET
            teamName  = COALESCE(excluded.teamName,  teams.teamName),
            teamSName = COALESCE(excluded.teamSName, teams.teamSName),
            teamType  = COALESCE(excluded.teamType,  teams.teamType)
    """, rows)

    conn.commit()
    print(f"  → teams: {cursor.execute('SELECT COUNT(*) FROM teams').fetchone()[0]} rows")


# ═══════════════════════════════════════════════════════════
# TABLE 2 — venues
# ═══════════════════════════════════════════════════════════

def venues():
    cursor.execute("DROP TABLE IF EXISTS venues")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS venues (
            venueId       INTEGER PRIMARY KEY,
            venueName     TEXT,
            venueCity     TEXT,
            venueCountry  TEXT,
            venueCapacity INTEGER
        )
    """)

    rows = []

    # Source 1: 1_venues/*.json — venueId from filename (venue_35.json → 35)
    for jsonfile in glob.glob('utils/json/1_venues/*.json'):
        with open(jsonfile, 'r') as f:
            data = json.load(f)
        try:
            venueId = int(os.path.basename(jsonfile).split('_')[-1].replace('.json', ''))
        except (ValueError, IndexError):
            continue
        rows.append((
            venueId,
            data.get('ground'),
            data.get('city'),
            data.get('country'),
            capacity_to_int(data.get('capacity'))
        ))

    # Source 2: 4_series/venues/*.json
    for jsonfile in glob.glob('utils/json/4_series/venues/*.json'):
        with open(jsonfile, 'r') as f:
            data = json.load(f)
        for venue in data.get('seriesVenue', []):
            rows.append((
                venue.get('id'),
                venue.get('ground'),
                venue.get('city'),
                venue.get('country'),
                None
            ))

    # Source 3: 5_matches/info/*.json
    for jsonfile in glob.glob('utils/json/5_matches/info/*.json'):
        with open(jsonfile, 'r') as f:
            data = json.load(f)
        venue = data.get('venueinfo', {})
        rows.append((
            venue.get('id'),
            venue.get('ground'),
            venue.get('city'),
            venue.get('country'),
            capacity_to_int(venue.get('capacity'))
        ))

    # Source 4: 5_matches/lists/*.json — venueInfo inside matchInfo
    for jsonfile in glob.glob('utils/json/5_matches/lists/*.json'):
        with open(jsonfile, 'r') as f:
            data = json.load(f)
        for typeBlock in data.get('typeMatches', []):
            for series in typeBlock.get('seriesMatches', []):
                seriesWrapper = series.get('seriesAdWrapper')
                if not seriesWrapper:
                    continue
                for matchBlock in seriesWrapper.get('matches', []):
                    venue = matchBlock.get('matchInfo', {}).get('venueInfo', {})
                    if not venue.get('id'):
                        continue
                    rows.append((
                        venue.get('id'),
                        venue.get('ground'),
                        venue.get('city'),
                        None,
                        None
                    ))

    cursor.executemany("""
        INSERT INTO venues (venueId, venueName, venueCity, venueCountry, venueCapacity)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(venueId) DO UPDATE SET
            venueName     = COALESCE(excluded.venueName,     venues.venueName),
            venueCity     = COALESCE(excluded.venueCity,     venues.venueCity),
            venueCountry  = COALESCE(excluded.venueCountry,  venues.venueCountry),
            venueCapacity = COALESCE(excluded.venueCapacity, venues.venueCapacity)
    """, rows)

    conn.commit()
    print(f"  → venues: {cursor.execute('SELECT COUNT(*) FROM venues').fetchone()[0]} rows")


# ═══════════════════════════════════════════════════════════
# TABLE 3 — players
# ═══════════════════════════════════════════════════════════

def players():
    cursor.execute("DROP TABLE IF EXISTS players")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            playerId   INTEGER PRIMARY KEY,
            playerName TEXT,
            teamId     INTEGER
        )
    """)

    rows = {}  # playerId → (playerId, playerName, teamId)

    # Source 1: 3_players/*.json — teamId from filename
    for jsonfile in glob.glob('utils/json/3_players/*.json'):
        with open(jsonfile, 'r') as f:
            data = json.load(f)
        try:
            teamId = int(os.path.basename(jsonfile).split('_')[-1].replace('.json', ''))
        except (ValueError, IndexError):
            teamId = None
        for player in data.get('player', []):
            if 'id' not in player:
                continue
            pid = str(player['id'])
            if pid not in rows:
                rows[pid] = (int(player['id']), player.get('name'), teamId)

    # Source 2: 6_scorecards/*.json — batsman and bowler
    for jsonfile in glob.glob('utils/json/6_scorecards/*.json'):
        with open(jsonfile, 'r') as f:
            data = json.load(f)
        for innings in data.get('scorecard', []):
            for player in innings.get('batsman', []) + innings.get('bowler', []):
                pid = str(player.get('id', ''))
                if pid and pid not in rows:
                    rows[pid] = (int(player['id']), player.get('name'), None)

    # Source 3: 7_records battings, bowlings, highest_scores
    for pattern in [
        'utils/json/7_records/battings/*.json',
        'utils/json/7_records/bowlings/*.json',
        'utils/json/7_records/highest_scores/*.json',
    ]:
        for jsonfile in glob.glob(pattern):
            with open(jsonfile, 'r') as f:
                data = json.load(f)
            for entry in data.get('values', []):
                vals = entry.get('values', [])
                if len(vals) >= 2 and vals[0] and vals[1]:
                    pid = str(vals[0])
                    if pid not in rows:
                        rows[pid] = (vals[0], vals[1], None)

    cursor.executemany("""
        INSERT INTO players (playerId, playerName, teamId)
        VALUES (?, ?, ?)
        ON CONFLICT(playerId) DO UPDATE SET
            playerName = COALESCE(players.playerName, excluded.playerName),
            teamId     = COALESCE(players.teamId,     excluded.teamId)
    """, list(rows.values()))

    conn.commit()
    print(f"  → players: {cursor.execute('SELECT COUNT(*) FROM players').fetchone()[0]} rows")


# ═══════════════════════════════════════════════════════════
# TABLE 4 — teamPlayers
# ═══════════════════════════════════════════════════════════

import json

def teamPlayers():
    cursor.execute("DROP TABLE IF EXISTS teamPlayers")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teamPlayers (
            id           INTEGER PRIMARY KEY,
            name         TEXT,
            teamId       INTEGER,
            role         TEXT,
            battingStyle TEXT,
            bowlingStyle TEXT
        )
    """)

    rows = []
    
    with open('utils/json/3_players/team_players_2.json', 'r') as f:
        data = json.load(f)

    role = None

    for player in data.get('player', []):
        if 'id' not in player:
            role = player.get('name')
            continue
            
        rows.append((
            int(player['id']), 
            player.get('name'), 
            2, 
            role, 
            player.get('battingStyle'), 
            player.get('bowlingStyle')
        ))

    cursor.executemany("""
        INSERT INTO teamPlayers (id, name, teamId, role, battingStyle, bowlingStyle)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name         = COALESCE(excluded.name,         teamPlayers.name),
            teamId       = COALESCE(excluded.teamId,       teamPlayers.teamId),
            role         = COALESCE(excluded.role,         teamPlayers.role),
            battingStyle = COALESCE(excluded.battingStyle, teamPlayers.battingStyle),
            bowlingStyle = COALESCE(excluded.bowlingStyle, teamPlayers.bowlingStyle)
    """, rows)

    conn.commit()
    print(f"  → teamPlayers: {cursor.execute('SELECT COUNT(*) FROM teamPlayers').fetchone()[0]} rows")


# ═══════════════════════════════════════════════════════════
# TABLE 5 — crudTable
# ═══════════════════════════════════════════════════════════

def crudTable():
    cursor.execute("DROP TABLE IF EXISTS crudTable")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crudTable (
            id   INTEGER PRIMARY KEY,
            name TEXT,
            team TEXT,
            role TEXT
        )
    """)

    rows = []

    with open('utils/json/3_players/team_players_2.json', 'r') as f:
        data = json.load(f)

    role_groups = {}
    currentRole = None
    for player in data.get('player', []):
        if 'id' not in player:
            currentRole = player.get('name')
            role_groups.setdefault(currentRole, [])
        else:
            if currentRole:
                role_groups[currentRole].append(player)

    for role, player_list in role_groups.items():
        selected = random.sample(player_list, min(3, len(player_list)))
        for player in selected:
            rows.append((
                int(player.get('id')),
                player.get('name'),
                'IND',
                role
            ))

    cursor.executemany("""
        INSERT INTO crudTable (id, name, team, role)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name = COALESCE(excluded.name, crudTable.name),
            team = COALESCE(excluded.team, crudTable.team),
            role = COALESCE(excluded.role, crudTable.role)
    """, rows)

    conn.commit()
    print(f"  → crudTable: {cursor.execute('SELECT COUNT(*) FROM crudTable').fetchone()[0]} rows")


# ═══════════════════════════════════════════════════════════
# TABLE 6 — series
# ═══════════════════════════════════════════════════════════

def series():
    cursor.execute("DROP TABLE IF EXISTS series")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS series (
            seriesId         INTEGER PRIMARY KEY,
            seriesName       TEXT,
            seriesStartDate  TEXT,
            seriesType       TEXT,
            seriesCountry    TEXT,
            seriesTotalMatches INTEGER
        )
    """)

    # --- Source 1: 4_series/lists/*.json ---
    rows = []
    for jsonfile in glob.glob('utils/json/4_series/lists/*.json'):
        with open(jsonfile, 'r') as f:
            data = json.load(f)
        seriesType = os.path.basename(jsonfile).replace('.json', '').split('_')[-1].upper()

        for date_block in data.get('seriesMapProto', []):
            for s in date_block.get('series', []):
                rows.append((
                    s.get('id'),
                    s.get('name'),
                    ts_to_date(s.get('startDt')) if s.get('startDt') else None,
                    seriesType,
                    None,   # seriesCountry — enriched later
                    None    # seriesTotalMatches — enriched later
                ))

    cursor.executemany("""
        INSERT INTO series (seriesId, seriesName, seriesStartDate, seriesType, seriesCountry, seriesTotalMatches)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(seriesId) DO UPDATE SET
            seriesName         = COALESCE(excluded.seriesName,         series.seriesName),
            seriesStartDate    = COALESCE(excluded.seriesStartDate,    series.seriesStartDate),
            seriesType         = COALESCE(excluded.seriesType,         series.seriesType)
    """, rows)

    # --- Source 2: 4_series/matches/*.json ---
    for jsonfile in glob.glob('utils/json/4_series/matches/*.json'):
        with open(jsonfile, 'r') as f:
            data = json.load(f)

        seriesId = seriesName = seriesStartDate = seriesCountry = None
        seriesTotalMatches = 0

        for block in data.get('matchDetails', []):
            if 'matchDetailsMap' not in block:
                continue
            for matchObj in block['matchDetailsMap'].get('match', []):
                match = matchObj.get('matchInfo', {})
                seriesTotalMatches += 1

                if not seriesId:
                    seriesId = match.get('seriesId')
                if not seriesName:
                    seriesName = match.get('seriesName')
                if not seriesStartDate and match.get('startDate'):
                    seriesStartDate = ts_to_date(match.get('startDate'))

                if not seriesCountry:
                    city = match.get('venueInfo', {}).get('city')
                    if city:
                        r = cursor.execute(
                            "SELECT venueCountry FROM venues WHERE venueCity = ?", (city,)
                        ).fetchone()
                        if r:
                            seriesCountry = r[0]

        if seriesId:
            cursor.execute("""
                INSERT INTO series (seriesId, seriesName, seriesStartDate, seriesCountry, seriesTotalMatches)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(seriesId) DO UPDATE SET
                    seriesName         = COALESCE(excluded.seriesName,         series.seriesName),
                    seriesStartDate    = COALESCE(excluded.seriesStartDate,    series.seriesStartDate),
                    seriesCountry      = COALESCE(excluded.seriesCountry,      series.seriesCountry),
                    seriesTotalMatches = COALESCE(excluded.seriesTotalMatches, series.seriesTotalMatches)
            """, (seriesId, seriesName, seriesStartDate, seriesCountry, seriesTotalMatches))

    # --- Source 3: 5_matches/lists/*.json ---
    for jsonfile in glob.glob('utils/json/5_matches/lists/*.json'):
        with open(jsonfile, 'r') as f:
            data = json.load(f)
            
        for type_match in data.get('typeMatches', []):
            seriesType = type_match.get('matchType').upper() # e.g., 'International', 'Women'
            
            for series_match in type_match.get('seriesMatches', []):
                wrapper = series_match.get('seriesAdWrapper')
                if not wrapper:
                    continue
                    
                series_id = wrapper.get('seriesId')
                series_name = wrapper.get('seriesName')
                matches_list = wrapper.get('matches', [])
                
                if not series_id:
                    continue
                    
                series_start_dt = None
                series_country = None
                
                for match in matches_list:
                    m_info = match.get('matchInfo', {})
                    
                    # Grab the series start date from the first available match info
                    if not series_start_dt and m_info.get('seriesStartDt'):
                        series_start_dt = ts_to_date(m_info.get('seriesStartDt'))
                        
                    # Try to resolve country from the venue city
                    if not series_country:
                        city = m_info.get('venueInfo', {}).get('city')
                        if city:
                            r = cursor.execute(
                                "SELECT venueCountry FROM venues WHERE venueCity = ?", (city,)
                            ).fetchone()
                            if r:
                                series_country = r[0]
                                
                cursor.execute("""
                    INSERT INTO series (seriesId, seriesName, seriesStartDate, seriesType, seriesCountry)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(seriesId) DO UPDATE SET
                        seriesName         = COALESCE(excluded.seriesName,         series.seriesName),
                        seriesStartDate    = COALESCE(excluded.seriesStartDate,    series.seriesStartDate),
                        seriesType         = COALESCE(excluded.seriesType,         series.seriesType),
                        seriesCountry      = COALESCE(excluded.seriesCountry,      series.seriesCountry)
                """, (series_id, series_name, series_start_dt, seriesType, series_country))

    conn.commit()
    print(f"  → series: {cursor.execute('SELECT COUNT(*) FROM series').fetchone()[0]} rows")


# ═══════════════════════════════════════════════════════════
# TABLE 7 — matches
# ═══════════════════════════════════════════════════════════

def matches():
    cursor.execute("DROP TABLE IF EXISTS matches")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            matchId         INTEGER PRIMARY KEY,
            seriesId        INTEGER,
            matchDesc       TEXT,
            matchFormat     TEXT,
            matchDate       TEXT,
            matchState      TEXT,
            matchStatus     TEXT,
            firstBatTeamId  INTEGER,
            secondBatTeamId INTEGER,
            venueId         INTEGER,
            matchVenue      TEXT,
            matchCity       TEXT,
            matchCountry    TEXT,
            tossWinTeamId   INTEGER,
            tossSelection   TEXT,
            winningTeamId   INTEGER,
            winningType     TEXT,
            winningMargin   INTEGER
        )
    """)

    rows = []

    # Source 1: 4_series/matches/*.json
    for jsonFile in glob.glob('utils/json/4_series/matches/*.json'):
        with open(jsonFile, 'r') as f:
            data = json.load(f)
        for block in data.get('matchDetails', []):
            if 'matchDetailsMap' not in block:
                continue
            for matchObj in block['matchDetailsMap'].get('match', []):
                match = matchObj.get('matchInfo', {})
                team1 = match.get('team1', {})
                team2 = match.get('team2', {})
                venue = match.get('venueInfo', {})
                status = match.get('status') or ''
                winningTeamId, winningType, winningMargin = parse_winner(
                    status,
                    team1.get('teamName'), team1.get('teamId'),
                    team2.get('teamName'), team2.get('teamId')
                )
                rows.append((
                    match.get('matchId'),
                    match.get('seriesId'),
                    match.get('matchDesc'),
                    normalize_match_format(match.get('matchFormat')),
                    ts_to_date(match.get('startDate')),
                    match.get('state'),
                    status,
                    team1.get('teamId'),
                    team2.get('teamId'),
                    venue.get('id'),
                    venue.get('ground'),
                    venue.get('city'),
                    None,   # matchCountry not available in this source
                    None,   # tossWinTeamId not available in this source
                    None,   # tossSelection not available in this source
                    winningTeamId, winningType, winningMargin
                ))

    # Source 2: 5_matches/lists/*.json
    for jsonFile in glob.glob('utils/json/5_matches/lists/*.json'):
        with open(jsonFile, 'r') as f:
            data = json.load(f)
        for typeBlock in data.get('typeMatches', []):
            for series in typeBlock.get('seriesMatches', []):
                seriesWrapper = series.get('seriesAdWrapper')
                if not seriesWrapper:
                    continue
                for matchBlock in seriesWrapper.get('matches', []):
                    match = matchBlock.get('matchInfo', {})
                    team1 = match.get('team1', {})
                    team2 = match.get('team2', {})
                    venue = match.get('venueInfo', {})
                    status = match.get('status') or ''
                    winningTeamId, winningType, winningMargin = parse_winner(
                        status,
                        team1.get('teamName'), team1.get('teamId'),
                        team2.get('teamName'), team2.get('teamId')
                    )
                    rows.append((
                        match.get('matchId'),
                        match.get('seriesId'),
                        match.get('matchDesc'),
                        normalize_match_format(match.get('matchFormat')),
                        ts_to_date(match.get('startDate')),
                        match.get('state'),
                        status,
                        team1.get('teamId'),
                        team2.get('teamId'),
                        venue.get('id'),
                        venue.get('ground'),
                        venue.get('city'),
                        None,   # matchCountry not available in this source
                        None,   # tossWinTeamId not available in this source
                        None,   # tossSelection not available in this source
                        winningTeamId, winningType, winningMargin
                    ))

    # Source 3: 5_matches/info/*.json — toss + country available
    for jsonFile in glob.glob('utils/json/5_matches/info/*.json'):
        with open(jsonFile, 'r') as f:
            match = json.load(f)
        team1 = match.get('team1', {})
        team2 = match.get('team2', {})
        venue = match.get('venueinfo', {})
        status = match.get('shortstatus') or ''

        # Toss parsing
        tossWinTeamId = tossSelection = None
        tossstatus = match.get('tossstatus') or ''
        toss_match = re.search(r'(.+?)\s+opt\s+to\s+(bat|bowl)', tossstatus, re.IGNORECASE)
        if toss_match:
            tossTeam = toss_match.group(1).strip().lower()
            tossSelection = toss_match.group(2).lower()
            if tossTeam == str(team1.get('teamname', '')).strip().lower():
                tossWinTeamId = team1.get('teamid')
            elif tossTeam == str(team2.get('teamname', '')).strip().lower():
                tossWinTeamId = team2.get('teamid')

        winningTeamId, winningType, winningMargin = parse_winner(
            status,
            team1.get('teamname'), team1.get('teamid'),
            team2.get('teamname'), team2.get('teamid')
        )

        rows.append((
            match.get('matchid'),
            match.get('seriesid'),
            match.get('matchdesc'),
            normalize_match_format(match.get('matchformat')),
            ts_to_date(match.get('startdate')),
            match.get('state'),
            status,
            team1.get('teamid'),
            team2.get('teamid'),
            venue.get('id'),
            venue.get('ground'),
            venue.get('city'),
            venue.get('country'),
            tossWinTeamId,
            tossSelection,
            winningTeamId, winningType, winningMargin
        ))

    cursor.executemany("""
        INSERT INTO matches VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(matchId) DO UPDATE SET
            seriesId        = COALESCE(excluded.seriesId,        matches.seriesId),
            matchDesc       = COALESCE(excluded.matchDesc,       matches.matchDesc),
            matchFormat     = COALESCE(excluded.matchFormat,     matches.matchFormat),
            matchDate       = COALESCE(excluded.matchDate,       matches.matchDate),
            matchState      = COALESCE(excluded.matchState,      matches.matchState),
            matchStatus     = COALESCE(excluded.matchStatus,     matches.matchStatus),
            firstBatTeamId  = COALESCE(excluded.firstBatTeamId,  matches.firstBatTeamId),
            secondBatTeamId = COALESCE(excluded.secondBatTeamId, matches.secondBatTeamId),
            venueId         = COALESCE(excluded.venueId,         matches.venueId),
            matchVenue      = COALESCE(excluded.matchVenue,      matches.matchVenue),
            matchCity       = COALESCE(excluded.matchCity,       matches.matchCity),
            matchCountry    = COALESCE(excluded.matchCountry,    matches.matchCountry),
            tossWinTeamId   = COALESCE(excluded.tossWinTeamId,   matches.tossWinTeamId),
            tossSelection   = COALESCE(excluded.tossSelection,   matches.tossSelection),
            winningTeamId   = COALESCE(excluded.winningTeamId,   matches.winningTeamId),
            winningType     = COALESCE(excluded.winningType,     matches.winningType),
            winningMargin   = COALESCE(excluded.winningMargin,   matches.winningMargin)
    """, rows)

    conn.commit()
    print(f"  → matches: {cursor.execute('SELECT COUNT(*) FROM matches').fetchone()[0]} rows")


# ═══════════════════════════════════════════════════════════
# TABLE 8 — matchBowlings
# ═══════════════════════════════════════════════════════════

def matchBowlings():
    cursor.execute("DROP TABLE IF EXISTS matchBowlings")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matchBowlings (
            matchId  INTEGER,
            innings  INTEGER,
            playerId INTEGER,
            overs    REAL,
            wickets  INTEGER,
            economy  REAL,
            venue    TEXT,
            PRIMARY KEY (matchId, innings, playerId)
        )
    """)

    rows = []

    for jsonfile in glob.glob('utils/json/6_scorecards/*.json'):
        with open(jsonfile, 'r') as f:
            data = json.load(f)

        matchId = scorecard_match_id(data)

        # venue lookup from matches table
        venue = None
        r = cursor.execute("SELECT matchVenue FROM matches WHERE matchId = ?", (matchId,)).fetchone()
        if r:
            venue = r[0]

        for innings in data.get('scorecard', []):
            inningsId = innings.get('inningsid')
            for bowler in innings.get('bowler', []):
                rows.append((
                    matchId,
                    inningsId,
                    bowler.get('id'),
                    balls_to_overs(bowler.get('balls')),
                    bowler.get('wickets'),
                    bowler.get('economy'),
                    venue
                ))

    cursor.executemany("""
        INSERT INTO matchBowlings (matchId, innings, playerId, overs, wickets, economy, venue)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(matchId, innings, playerId) DO UPDATE SET
            overs   = COALESCE(excluded.overs,   matchBowlings.overs),
            wickets = COALESCE(excluded.wickets, matchBowlings.wickets),
            economy = COALESCE(excluded.economy, matchBowlings.economy),
            venue   = COALESCE(excluded.venue,   matchBowlings.venue)
    """, rows)

    conn.commit()
    print(f"  → matchBowlings: {cursor.execute('SELECT COUNT(*) FROM matchBowlings').fetchone()[0]} rows")


# ═══════════════════════════════════════════════════════════
# TABLE 9 — matchBattings
# ═══════════════════════════════════════════════════════════

def matchBattings():
    cursor.execute("DROP TABLE IF EXISTS matchBattings")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matchBattings (
            matchId    INTEGER,
            innings    INTEGER,
            playerId   INTEGER,
            matchFormat TEXT,
            matchDate  TEXT,
            runs       INTEGER,
            overs      REAL,
            strikeRate REAL,
            battingAvg REAL,
            quarter    TEXT,
            PRIMARY KEY (matchId, innings, playerId)
        )
    """)

    rows = []

    for jsonfile in glob.glob('utils/json/6_scorecards/*.json'):
        with open(jsonfile, 'r') as f:
            data = json.load(f)

        matchId = scorecard_match_id(data)

        # matchFormat and matchDate lookup from matches table
        matchFormat = matchDate = quarter = None
        r = cursor.execute(
            "SELECT matchFormat, matchDate FROM matches WHERE matchId = ?", (matchId,)
        ).fetchone()
        if r:
            matchFormat = r[0]
            matchDate = r[1]
            if matchDate:
                year = matchDate[:4]
                month = int(matchDate[5:7])
                quarter = f"{year}-Q{(month - 1) // 3 + 1}"

        for innings in data.get('scorecard', []):
            inningsId = innings.get('inningsid')
            for batsman in innings.get('batsman', []):
                balls = batsman.get('balls', 0)
                if not balls or int(balls) == 0:
                    continue
                overs = balls_to_overs(balls)
                runs = batsman.get('runs')

                # battingAvg = runs / overs
                battingAvg = None
                try:
                    if overs and float(overs) > 0:
                        battingAvg = round(int(runs) / float(overs), 2)
                except (ValueError, TypeError, ZeroDivisionError):
                    pass

                rows.append((
                    matchId,
                    inningsId,
                    batsman.get('id'),
                    matchFormat,
                    matchDate,
                    runs,
                    overs,
                    batsman.get('strkrate'),
                    battingAvg,
                    quarter
                ))

    cursor.executemany("""
        INSERT INTO matchBattings
            (matchId, innings, playerId, matchFormat, matchDate, runs, overs, strikeRate, battingAvg, quarter)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(matchId, innings, playerId) DO UPDATE SET
            matchFormat = COALESCE(excluded.matchFormat, matchBattings.matchFormat),
            matchDate   = COALESCE(excluded.matchDate,   matchBattings.matchDate),
            runs        = COALESCE(excluded.runs,        matchBattings.runs),
            overs       = COALESCE(excluded.overs,       matchBattings.overs),
            strikeRate  = COALESCE(excluded.strikeRate,  matchBattings.strikeRate),
            battingAvg  = COALESCE(excluded.battingAvg,  matchBattings.battingAvg),
            quarter     = COALESCE(excluded.quarter,     matchBattings.quarter)
    """, rows)

    conn.commit()
    print(f"  → matchBattings: {cursor.execute('SELECT COUNT(*) FROM matchBattings').fetchone()[0]} rows")


# ═══════════════════════════════════════════════════════════
# TABLE 10 — matchPartnerships
# ═══════════════════════════════════════════════════════════

def matchPartnerships():
    cursor.execute("DROP TABLE IF EXISTS matchPartnerships")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matchPartnerships (
            matchId         INTEGER,
            innings         INTEGER,
            batsman1Id      INTEGER,
            batsman2Id      INTEGER,
            partnershipRuns INTEGER,
            PRIMARY KEY (matchId, innings, batsman1Id, batsman2Id)
        )
    """)

    rows = []

    for jsonfile in glob.glob('utils/json/6_scorecards/*.json'):
        with open(jsonfile, 'r') as f:
            data = json.load(f)

        matchId = scorecard_match_id(data)

        for innings in data.get('scorecard', []):
            inningsId = innings.get('inningsid')
            for p in innings.get('partnership', {}).get('partnership', []):
                bat1Id = p.get('bat1id')
                bat2Id = p.get('bat2id')
                if not bat1Id or not bat2Id:
                    continue
                rows.append((
                    matchId,
                    inningsId,
                    min(int(bat1Id), int(bat2Id)),  # always lower id as batsman1Id
                    max(int(bat1Id), int(bat2Id)),
                    p.get('totalruns')
                ))

    cursor.executemany("""
        INSERT INTO matchPartnerships (matchId, innings, batsman1Id, batsman2Id, partnershipRuns)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(matchId, innings, batsman1Id, batsman2Id) DO UPDATE SET
            partnershipRuns = COALESCE(excluded.partnershipRuns, matchPartnerships.partnershipRuns)
    """, rows)

    conn.commit()
    print(f"  → matchPartnerships: {cursor.execute('SELECT COUNT(*) FROM matchPartnerships').fetchone()[0]} rows")


# ═══════════════════════════════════════════════════════════
# TABLE 11 — battingCareers
# ═══════════════════════════════════════════════════════════

def battingCareers():
    cursor.execute("DROP TABLE IF EXISTS battingCareers")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS battingCareers (
            playerId     INTEGER,
            matchFormat  TEXT,
            totalMatches INTEGER,
            totalRuns    INTEGER,
            overs        REAL,
            highestScore TEXT,
            battingAvg   REAL,
            strikeRate   REAL,
            hundreds     INTEGER,
            PRIMARY KEY (playerId, matchFormat)
        )
    """)

    rows = []

    for jsonfile in glob.glob('utils/json/8_careers/battings/*.json'):
        with open(jsonfile, 'r') as f:
            data = json.load(f)

        try:
            playerId = data.get('appIndex').get('webURL').split('/')[4]
        except (AttributeError, IndexError):
            continue

        headers = data.get('headers', [])  # ['ROWHEADER', 'Test', 'ODI', 'T20', 'IPL']
        values  = data.get('values', [])

        def safe_val(idx, col):
            try:
                v = values[idx].get('values', [])[col]
                return v if v not in ('', '-', None) else None
            except (IndexError, AttributeError):
                return None

        for i in range(1, len(headers)):
            matchFormat = headers[i].upper()
            rows.append((
                playerId,
                matchFormat,
                safe_val(0, i),   # Matches
                safe_val(2, i),   # Runs
                balls_to_overs(safe_val(3, i)),  # Balls → overs
                safe_val(4, i),   # Highest
                safe_val(5, i),   # Average
                safe_val(6, i),   # SR
                safe_val(12, i)   # 100s
            ))

    cursor.executemany("""
        INSERT INTO battingCareers
            (playerId, matchFormat, totalMatches, totalRuns, overs, highestScore, battingAvg, strikeRate, hundreds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(playerId, matchFormat) DO UPDATE SET
            totalMatches = COALESCE(excluded.totalMatches, battingCareers.totalMatches),
            totalRuns    = COALESCE(excluded.totalRuns,    battingCareers.totalRuns),
            overs        = COALESCE(excluded.overs,        battingCareers.overs),
            highestScore = COALESCE(excluded.highestScore, battingCareers.highestScore),
            battingAvg   = COALESCE(excluded.battingAvg,   battingCareers.battingAvg),
            strikeRate   = COALESCE(excluded.strikeRate,   battingCareers.strikeRate),
            hundreds     = COALESCE(excluded.hundreds,     battingCareers.hundreds)
    """, rows)

    conn.commit()
    print(f"  → battingCareers: {cursor.execute('SELECT COUNT(*) FROM battingCareers').fetchone()[0]} rows")


# ═══════════════════════════════════════════════════════════
# TABLE 12 — bowlingCareers
# ═══════════════════════════════════════════════════════════

def bowlingCareers():
    cursor.execute("DROP TABLE IF EXISTS bowlingCareers")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bowlingCareers (
            playerId     INTEGER,
            matchFormat  TEXT,
            totalMatches INTEGER,
            overs        REAL,
            wickets      INTEGER,
            economy      REAL,
            bowlingAvg   REAL,
            PRIMARY KEY (playerId, matchFormat)
        )
    """)

    rows = []

    for jsonfile in glob.glob('utils/json/8_careers/bowlings/*.json'):
        with open(jsonfile, 'r') as f:
            data = json.load(f)

        try:
            playerId = data.get('appIndex').get('webURL').split('/')[4]
        except (AttributeError, IndexError):
            continue

        headers = data.get('headers', [])
        values  = data.get('values', [])

        def safe_val(idx, col):
            try:
                v = values[idx].get('values', [])[col]
                return v if v not in ('', '-', None) else None
            except (IndexError, AttributeError):
                return None

        for i in range(1, len(headers)):
            matchFormat = headers[i].upper()
            rows.append((
                playerId,
                matchFormat,
                safe_val(0, i),   # Matches
                balls_to_overs(safe_val(2, i)),  # Balls → overs
                safe_val(5, i),   # Wickets
                safe_val(7, i),   # Eco
                safe_val(6, i)    # Avg
            ))

    cursor.executemany("""
        INSERT INTO bowlingCareers
            (playerId, matchFormat, totalMatches, overs, wickets, economy, bowlingAvg)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(playerId, matchFormat) DO UPDATE SET
            totalMatches = COALESCE(excluded.totalMatches, bowlingCareers.totalMatches),
            overs        = COALESCE(excluded.overs,        bowlingCareers.overs),
            wickets      = COALESCE(excluded.wickets,      bowlingCareers.wickets),
            economy      = COALESCE(excluded.economy,      bowlingCareers.economy),
            bowlingAvg   = COALESCE(excluded.bowlingAvg,   bowlingCareers.bowlingAvg)
    """, rows)

    conn.commit()
    print(f"  → bowlingCareers: {cursor.execute('SELECT COUNT(*) FROM bowlingCareers').fetchone()[0]} rows")


# ═══════════════════════════════════════════════════════════
# HELPER — shared filter parsing for all 3 records functions
# ═══════════════════════════════════════════════════════════

def parse_records_filter(data, jsonfile):
    """Extract statType, matchFormat, year, teamId from a records JSON file."""
    statType       = os.path.basename(jsonfile).split('_')[1]
    matchFormatRaw = data.get('filter', {}).get('selectedMatchType', '')
    matchFormat    = normalize_match_format(matchFormatRaw)
    year           = int(data.get('filter', {}).get('selectedYear', 0) or 0)
    teamSName      = data.get('filter', {}).get('selectedTeam', 'ALL')
    teamId         = 0
    if teamSName and teamSName != 'ALL':
        r = cursor.execute(
            "SELECT teamId FROM teams WHERE teamSName = ?", (teamSName,)
        ).fetchone()
        teamId = r[0] if r else 0
    return statType, matchFormat, year, teamId


# ═══════════════════════════════════════════════════════════
# TABLE 13 — battingRecords
# ═══════════════════════════════════════════════════════════

def battingRecords():
    cursor.execute("DROP TABLE IF EXISTS battingRecords")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS battingRecords (
            statType     TEXT,
            year         INTEGER,
            matchFormat  TEXT,
            teamId       INTEGER,
            playerId     INTEGER,
            totalMatches INTEGER,
            runs         INTEGER,
            strikeRate   REAL,
            battingAvg   REAL,
            PRIMARY KEY (statType, year, matchFormat, teamId, playerId)
        )
    """)

    rows = []

    for jsonfile in glob.glob('utils/json/7_records/battings/*.json'):
        with open(jsonfile, 'r') as f:
            data = json.load(f)

        statType, matchFormat, year, teamId = parse_records_filter(data, jsonfile)
        headers = data.get('headers', [])

        # Skip highestScore files — those go to highestScoreRecords
        if 'HS' in headers:
            continue

        # headers: Batter, M, I, R, Avg/SR
        lastHeader = headers[-1] if headers else ''

        for player in data.get('values', []):
            vals = player.get('values', [])
            if len(vals) < 2:
                continue
            playerId     = vals[0]
            totalMatches = vals[2] if len(vals) > 2 else None
            runs         = vals[4] if len(vals) > 4 else None
            strikeRate   = vals[5] if lastHeader == 'SR'  and len(vals) > 5 else None
            battingAvg   = vals[5] if lastHeader == 'Avg' and len(vals) > 5 else None
            rows.append((
                statType, year, matchFormat, teamId, playerId,
                totalMatches, runs, strikeRate, battingAvg
            ))

    cursor.executemany("""
        INSERT INTO battingRecords
            (statType, year, matchFormat, teamId, playerId, totalMatches, runs, strikeRate, battingAvg)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(statType, year, matchFormat, teamId, playerId) DO UPDATE SET
            totalMatches = COALESCE(excluded.totalMatches, battingRecords.totalMatches),
            runs         = COALESCE(excluded.runs,         battingRecords.runs),
            strikeRate   = COALESCE(excluded.strikeRate,   battingRecords.strikeRate),
            battingAvg   = COALESCE(excluded.battingAvg,   battingRecords.battingAvg)
    """, rows)

    conn.commit()
    print(f"  → battingRecords: {cursor.execute('SELECT COUNT(*) FROM battingRecords').fetchone()[0]} rows")


# ═══════════════════════════════════════════════════════════
# TABLE 14 — bowlingRecords
# ═══════════════════════════════════════════════════════════

def bowlingRecords():
    cursor.execute("DROP TABLE IF EXISTS bowlingRecords")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bowlingRecords (
            statType     TEXT,
            year         INTEGER,
            matchFormat  TEXT,
            teamId       INTEGER,
            playerId     INTEGER,
            totalMatches INTEGER,
            overs        TEXT,
            wickets      INTEGER,
            economy      REAL,
            bowlingAvg   REAL,
            PRIMARY KEY (statType, year, matchFormat, teamId, playerId)
        )
    """)

    rows = []

    for jsonfile in glob.glob('utils/json/7_records/bowlings/*.json'):
        with open(jsonfile, 'r') as f:
            data = json.load(f)

        statType, matchFormat, year, teamId = parse_records_filter(data, jsonfile)
        headers = data.get('headers', [])

        # headers: Bowler, M, O, W, Eco/Avg
        lastHeader = headers[-1] if headers else ''

        for player in data.get('values', []):
            vals = player.get('values', [])
            if len(vals) < 2:
                continue
            playerId     = vals[0]
            totalMatches = vals[2] if len(vals) > 2 else None
            overs        = vals[3] if len(vals) > 3 else None  # stored as string e.g. "325.1"
            wickets      = vals[4] if len(vals) > 4 else None
            economy      = vals[5] if lastHeader == 'Eco' and len(vals) > 5 else None
            bowlingAvg   = vals[5] if lastHeader == 'Avg' and len(vals) > 5 else None
            rows.append((
                statType, year, matchFormat, teamId, playerId,
                totalMatches, overs, wickets, economy, bowlingAvg
            ))

    cursor.executemany("""
        INSERT INTO bowlingRecords
            (statType, year, matchFormat, teamId, playerId, totalMatches, overs, wickets, economy, bowlingAvg)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(statType, year, matchFormat, teamId, playerId) DO UPDATE SET
            totalMatches = COALESCE(excluded.totalMatches, bowlingRecords.totalMatches),
            overs        = COALESCE(excluded.overs,        bowlingRecords.overs),
            wickets      = COALESCE(excluded.wickets,      bowlingRecords.wickets),
            economy      = COALESCE(excluded.economy,      bowlingRecords.economy),
            bowlingAvg   = COALESCE(excluded.bowlingAvg,   bowlingRecords.bowlingAvg)
    """, rows)

    conn.commit()
    print(f"  → bowlingRecords: {cursor.execute('SELECT COUNT(*) FROM bowlingRecords').fetchone()[0]} rows")


# ═══════════════════════════════════════════════════════════
# TABLE 15 — highestScoreRecords
# ═══════════════════════════════════════════════════════════

def highestScoreRecords():
    cursor.execute("DROP TABLE IF EXISTS highestScoreRecords")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS highestScoreRecords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playerId     INTEGER,
            matchFormat  TEXT,
            highestScore TEXT,
            overs        REAL
        )
    """)

    rows = []

    for jsonfile in glob.glob('utils/json/7_records/highest_scores/*.json'):
        with open(jsonfile, 'r') as f:
            data = json.load(f)

        _, matchFormat, _, _ = parse_records_filter(data, jsonfile)
        headers = data.get('headers', [])

        # headers: Batter, HS, Balls, SR, Vs
        for player in data.get('values', []):
            vals = player.get('values', [])
            if len(vals) < 2:
                continue
            playerId     = vals[0]
            highestScore = vals[2] if len(vals) > 2 else None
            balls        = vals[3] if len(vals) > 3 else None
            rows.append((
                playerId,
                matchFormat,
                highestScore,
                balls_to_overs(balls)
            ))

    cursor.executemany("""
        INSERT INTO highestScoreRecords (playerId, matchFormat, highestScore, overs)
        VALUES (?, ?, ?, ?)
    """, rows)

    conn.commit()
    print(f"  → highestScoreRecords: {cursor.execute('SELECT COUNT(*) FROM highestScoreRecords').fetchone()[0]} rows")


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    # print("\n🏏 cricDB Builder — Starting...\n")

    # print("🏴 [1/13] teams")
    # teams()

    # print("🏟️  [2/13] venues")
    # venues()

    # print("👤 [3/13] players")
    # players()

    # print("🧢 [4/13] teamPlayers")
    # teamPlayers()

    # print("📋 [5/13] crudTable")
    # crudTable()

    # print("📅 [6/13] series")
    # series()

    # print("🏏 [7/13] matches")
    # matches()

    # print("🎳 [8/13] matchBowlings")
    # matchBowlings()

    # print("🏏 [9/13] matchBattings")
    # matchBattings()

    # print("🤝 [10/13] matchPartnerships")
    # matchPartnerships()

    # print("📈 [11/15] battingCareers")
    # battingCareers()

    # print("📈 [12/15] bowlingCareers")
    # bowlingCareers()

    # print("📊 [13/15] battingRecords")
    # battingRecords()

    # print("📊 [14/15] bowlingRecords")
    # bowlingRecords()

    # print("🏆 [15/15] highestScoreRecords")
    # highestScoreRecords()

    # print("\n✅ cricDB build complete!\n")

    teams()
    venues()
    players()
    teamPlayers()
    crudTable()
    series()
    matches()
    matchBowlings()
    matchBattings()
    matchPartnerships()
    battingCareers()
    bowlingCareers()
    battingRecords()
    bowlingRecords()
    highestScoreRecords()


if __name__ == "__main__":
    main()
