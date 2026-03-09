"""
DB Sync Engine
===============
Two modes:
  sync_new_data()  → Append-only. Creates tables if missing, upserts new records.
                     Preserves CRUD entries. Fast.
  full_rebuild()   → Drops all tables, rebuilds from scratch. Clean slate.

Both accept an optional log_callback(message: str) for live UI feedback.
"""

import sqlite3
import glob
import json
import re
import os
from datetime import datetime

DB_PATH = "utils/cricBuzz.db"

# ─────────────────────────────────────────────────────────────
# Helpers (copied from 2_data2DB.py — keep in sync)
# ─────────────────────────────────────────────────────────────

def _capacity_to_int(s):
    if not s: return None
    try:
        digits = "".join(re.findall(r"\d", str(s)))
        return int(digits) if digits else None
    except Exception: return None

def _balls_to_overs(balls):
    if balls is None: return None
    try:
        balls = int(balls)
        return int(balls / 6) + (balls % 6) / 10
    except Exception: return None

def _ts_to_date(ts):
    if not ts: return None
    try:
        return datetime.fromtimestamp(int(ts) / 1000).strftime("%Y-%m-%d")
    except Exception: return None

def _normalize_fmt(fmt):
    if not fmt: return None
    m = {"t20i":"T20","t 20":"T20","t20":"T20","odi":"ODI","test":"TEST","ipl":"IPL"}
    return m.get(str(fmt).strip().lower(), str(fmt).strip().upper())

def _scorecard_match_id(data):
    try:
        return data.get("appindex", {}).get("weburl", "").split("/")[-2].split(".")[0]
    except Exception: return None

def _parse_winner(status, t1name, t1id, t2name, t2id):
    wid = wtype = wmargin = None
    if not status: return wid, wtype, wmargin
    s = status.strip()
    m = re.search(r"^(.+?)\s+won\s+by\s+an\s+innings\s+and\s+(\d+)\s+runs", s, re.IGNORECASE)
    if m:
        wn = m.group(1).strip().lower()
        wmargin = int(m.group(2)); wtype = "innings"
        if t1name and wn == str(t1name).strip().lower(): wid = t1id
        elif t2name and wn == str(t2name).strip().lower(): wid = t2id
        return wid, wtype, wmargin
    m = re.search(r"^(.+?)\s+won\s+by\s+(\d+)\s+(runs?|wkts?)", s, re.IGNORECASE)
    if m:
        wn = m.group(1).strip().lower(); wmargin = int(m.group(2))
        wtype = "runs" if "run" in m.group(3).lower() else "wkts"
        if t1name and wn == str(t1name).strip().lower(): wid = t1id
        elif t2name and wn == str(t2name).strip().lower(): wid = t2id
        return wid, wtype, wmargin
    if re.match(r"match tied",      s, re.IGNORECASE): return None, "tied",      None
    if re.match(r"match abandoned", s, re.IGNORECASE): return None, "abandoned", None
    if re.match(r"match drawn",     s, re.IGNORECASE): return None, "drawn",     None
    if re.match(r"no result",       s, re.IGNORECASE): return None, "no result", None
    if re.match(r"match cancelled", s, re.IGNORECASE): return None, "cancelled", None
    return None, None, None

def _parse_records_filter(cursor, data, jsonfile):
    statType    = os.path.basename(jsonfile).split("_")[1]
    matchFormat = _normalize_fmt(data.get("filter", {}).get("selectedMatchType", ""))
    year        = int(data.get("filter", {}).get("selectedYear", 0) or 0)
    teamSName   = data.get("filter", {}).get("selectedTeam", "ALL")
    teamId      = 0
    if teamSName and teamSName != "ALL":
        r = cursor.execute("SELECT teamId FROM teams WHERE teamSName = ?", (teamSName,)).fetchone()
        teamId = r[0] if r else 0
    return statType, matchFormat, year, teamId


# ─────────────────────────────────────────────────────────────
# Table builders — two variants per table:
#   _create_<table>(cursor)      → CREATE TABLE IF NOT EXISTS (append-safe)
#   _drop_create_<table>(cursor) → DROP + CREATE (full rebuild)
# ─────────────────────────────────────────────────────────────

TABLES_ORDER = [
    "teams","venues","players","teamPlayers","crudTable",
    "series","matches","matchBowlings","matchBattings",
    "matchPartnerships","battingCareers","bowlingCareers",
    "battingRecords","bowlingRecords","highestScoreRecords",
]

DDL = {
    "teams": """CREATE TABLE IF NOT EXISTS teams (
        teamId   INTEGER PRIMARY KEY,
        teamName TEXT, teamSName TEXT, teamType TEXT)""",

    "venues": """CREATE TABLE IF NOT EXISTS venues (
        venueId INTEGER PRIMARY KEY, venueName TEXT, venueCity TEXT,
        venueCountry TEXT, venueCapacity INTEGER)""",

    "players": """CREATE TABLE IF NOT EXISTS players (
        playerId INTEGER PRIMARY KEY, playerName TEXT, teamId INTEGER)""",

    "teamPlayers": """CREATE TABLE IF NOT EXISTS teamPlayers (
        id INTEGER PRIMARY KEY, name TEXT, teamId INTEGER, role TEXT,
        battingStyle TEXT, bowlingStyle TEXT)""",

    "crudTable": """CREATE TABLE IF NOT EXISTS crudTable (
        playerId INTEGER PRIMARY KEY, playerName TEXT, team TEXT,
        playingRole TEXT, battingStyle TEXT, bowlingStyle TEXT)""",

    "series": """CREATE TABLE IF NOT EXISTS series (
        seriesId INTEGER PRIMARY KEY, seriesName TEXT,
        seriesStartDate TEXT, seriesType TEXT, seriesCountry TEXT,
        seriesTotalMatches INTEGER)""",

    "matches": """CREATE TABLE IF NOT EXISTS matches (
        matchId INTEGER PRIMARY KEY, seriesId INTEGER, matchDesc TEXT,
        matchFormat TEXT, matchDate TEXT, matchState TEXT, matchStatus TEXT,
        firstBatTeamId INTEGER, secondBatTeamId INTEGER, venueId INTEGER,
        matchVenue TEXT, matchCity TEXT, matchCountry TEXT,
        tossWinTeamId INTEGER, tossSelection TEXT,
        winningTeamId INTEGER, winningType TEXT, winningMargin INTEGER)""",

    "matchBowlings": """CREATE TABLE IF NOT EXISTS matchBowlings (
        matchId INTEGER, innings INTEGER, playerId INTEGER,
        overs REAL, wickets INTEGER, economy REAL, venue TEXT,
        PRIMARY KEY (matchId, innings, playerId))""",

    "matchBattings": """CREATE TABLE IF NOT EXISTS matchBattings (
        matchId INTEGER, innings INTEGER, playerId INTEGER,
        matchFormat TEXT, matchDate TEXT, runs INTEGER, overs REAL,
        strikeRate REAL, battingAvg REAL, quarter TEXT,
        PRIMARY KEY (matchId, innings, playerId))""",

    "matchPartnerships": """CREATE TABLE IF NOT EXISTS matchPartnerships (
        matchId INTEGER, innings INTEGER, batsman1Id INTEGER,
        batsman2Id INTEGER, partnershipRuns INTEGER,
        PRIMARY KEY (matchId, innings, batsman1Id, batsman2Id))""",

    "battingCareers": """CREATE TABLE IF NOT EXISTS battingCareers (
        playerId INTEGER, matchFormat TEXT, totalMatches INTEGER,
        totalRuns INTEGER, overs REAL, highestScore TEXT,
        battingAvg REAL, strikeRate REAL, hundreds INTEGER,
        PRIMARY KEY (playerId, matchFormat))""",

    "bowlingCareers": """CREATE TABLE IF NOT EXISTS bowlingCareers (
        playerId INTEGER, matchFormat TEXT, totalMatches INTEGER,
        overs REAL, wickets INTEGER, economy REAL, bowlingAvg REAL,
        PRIMARY KEY (playerId, matchFormat))""",

    "battingRecords": """CREATE TABLE IF NOT EXISTS battingRecords (
        statType TEXT, year INTEGER, matchFormat TEXT, teamId INTEGER,
        playerId INTEGER, totalMatches INTEGER, runs INTEGER,
        strikeRate REAL, battingAvg REAL,
        PRIMARY KEY (statType, year, matchFormat, teamId, playerId))""",

    "bowlingRecords": """CREATE TABLE IF NOT EXISTS bowlingRecords (
        statType TEXT, year INTEGER, matchFormat TEXT, teamId INTEGER,
        playerId INTEGER, totalMatches INTEGER, overs TEXT,
        wickets INTEGER, economy REAL, bowlingAvg REAL,
        PRIMARY KEY (statType, year, matchFormat, teamId, playerId))""",

    "highestScoreRecords": """CREATE TABLE IF NOT EXISTS highestScoreRecords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        playerId INTEGER, matchFormat TEXT,
        highestScore TEXT, overs REAL)""",
}


# ─────────────────────────────────────────────────────────────
# Insert functions (shared by both modes)
# ─────────────────────────────────────────────────────────────

def _insert_teams(conn, cursor, log):
    rows = []
    for f in glob.glob("utils/json/4_series/lists/*.json") + glob.glob("utils/json/5_matches/lists/*.json"):
        try:
            with open(f) as fh: data = json.load(fh)
        except Exception: continue
        for team in data.get("teamMatchList", []):
            t = team.get("team", {})
            rows.append((t.get("teamId"), t.get("teamName"), t.get("teamSName"), t.get("teamType")))
        for m in data.get("typeMatches", []):
            for sm in m.get("seriesMatches", []):
                for match in sm.get("seriesAdWrapper", {}).get("matches", []):
                    for key in ["team1", "team2"]:
                        t = match.get("matchInfo", {}).get(key, {})
                        rows.append((t.get("teamId"), t.get("teamName"), t.get("teamSName"), t.get("teamType")))
    cursor.executemany("""
        INSERT INTO teams (teamId, teamName, teamSName, teamType) VALUES (?,?,?,?)
        ON CONFLICT(teamId) DO UPDATE SET
            teamName=COALESCE(excluded.teamName, teams.teamName),
            teamSName=COALESCE(excluded.teamSName, teams.teamSName),
            teamType=COALESCE(excluded.teamType, teams.teamType)
    """, [r for r in rows if r[0]])
    conn.commit()
    c = cursor.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
    log(f"  ✅ teams: {c} rows")


def _insert_venues(conn, cursor, log):
    rows = []
    for f in glob.glob("utils/json/4_series/venues/*.json"):
        try:
            with open(f) as fh: data = json.load(fh)
        except Exception: continue
        for v in data.get("venueList", []):
            rows.append((v.get("id"), v.get("name"), v.get("city"),
                         v.get("country"), _capacity_to_int(v.get("capacity"))))
    cursor.executemany("""
        INSERT INTO venues (venueId, venueName, venueCity, venueCountry, venueCapacity)
        VALUES (?,?,?,?,?)
        ON CONFLICT(venueId) DO UPDATE SET
            venueName=COALESCE(excluded.venueName, venues.venueName),
            venueCity=COALESCE(excluded.venueCity, venues.venueCity),
            venueCountry=COALESCE(excluded.venueCountry, venues.venueCountry),
            venueCapacity=COALESCE(excluded.venueCapacity, venues.venueCapacity)
    """, [r for r in rows if r[0]])
    conn.commit()
    c = cursor.execute("SELECT COUNT(*) FROM venues").fetchone()[0]
    log(f"  ✅ venues: {c} rows")


def _insert_players(conn, cursor, log):
    rows = []
    for f in glob.glob("utils/json/3_players/*.json"):
        try:
            with open(f) as fh: data = json.load(fh)
        except Exception: continue
        teamId = None
        try:
            teamId = data.get("appIndex", {}).get("webURL", "").split("/")[4]
        except Exception: pass
        for p in data.get("player", []):
            for player in p.get("playerList", []):
                rows.append((player.get("id"), player.get("name"), teamId))
    cursor.executemany("""
        INSERT INTO players (playerId, playerName, teamId) VALUES (?,?,?)
        ON CONFLICT(playerId) DO UPDATE SET
            playerName=COALESCE(excluded.playerName, players.playerName),
            teamId=COALESCE(excluded.teamId, players.teamId)
    """, [r for r in rows if r[0]])
    conn.commit()
    c = cursor.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    log(f"  ✅ players: {c} rows")


def _insert_teamPlayers(conn, cursor, log):
    rows = []
    for f in glob.glob("utils/json/3_players/*.json"):
        try:
            with open(f) as fh: data = json.load(fh)
        except Exception: continue
        teamId = None
        try:
            teamId = data.get("appIndex", {}).get("webURL", "").split("/")[4]
        except Exception: pass
        for group in data.get("player", []):
            for p in group.get("playerList", []):
                rows.append((p.get("id"), p.get("name"), teamId,
                             p.get("role"), p.get("battingStyle"), p.get("bowlingStyle")))
    cursor.executemany("""
        INSERT INTO teamPlayers (id, name, teamId, role, battingStyle, bowlingStyle)
        VALUES (?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
            name=COALESCE(excluded.name, teamPlayers.name),
            teamId=COALESCE(excluded.teamId, teamPlayers.teamId),
            role=COALESCE(excluded.role, teamPlayers.role),
            battingStyle=COALESCE(excluded.battingStyle, teamPlayers.battingStyle),
            bowlingStyle=COALESCE(excluded.bowlingStyle, teamPlayers.bowlingStyle)
    """, [r for r in rows if r[0]])
    conn.commit()
    c = cursor.execute("SELECT COUNT(*) FROM teamPlayers").fetchone()[0]
    log(f"  ✅ teamPlayers: {c} rows")


def _insert_crudTable(conn, cursor, log):
    # Only populate if empty — preserve user CRUD entries
    existing = cursor.execute("SELECT COUNT(*) FROM crudTable").fetchone()[0]
    if existing > 0:
        log(f"  ⏭  crudTable: {existing} rows (preserved — not overwritten)")
        return
    rows = []
    for f in glob.glob("utils/json/3_players/*.json"):
        try:
            with open(f) as fh: data = json.load(fh)
        except Exception: continue
        for group in data.get("player", []):
            team = group.get("title", "")
            for p in group.get("playerList", []):
                rows.append((p.get("id"), p.get("name"), team,
                             p.get("role"), p.get("battingStyle"), p.get("bowlingStyle")))
    cursor.executemany("""
        INSERT OR IGNORE INTO crudTable
            (playerId, playerName, team, playingRole, battingStyle, bowlingStyle)
        VALUES (?,?,?,?,?,?)
    """, [r for r in rows if r[0]])
    conn.commit()
    c = cursor.execute("SELECT COUNT(*) FROM crudTable").fetchone()[0]
    log(f"  ✅ crudTable: {c} rows")


def _insert_series(conn, cursor, log):
    rows = []
    for f in glob.glob("utils/json/4_series/lists/*.json"):
        try:
            with open(f) as fh: data = json.load(fh)
        except Exception: continue
        for item in data.get("seriesMapProto", []):
            for s in item.get("series", []):
                rows.append((s.get("id"), s.get("name"),
                             _ts_to_date(s.get("startDate")), s.get("seriesType"),
                             s.get("seriesCategory"), s.get("numberOfMatches")))
    cursor.executemany("""
        INSERT INTO series (seriesId, seriesName, seriesStartDate, seriesType, seriesCountry, seriesTotalMatches)
        VALUES (?,?,?,?,?,?)
        ON CONFLICT(seriesId) DO UPDATE SET
            seriesName=COALESCE(excluded.seriesName, series.seriesName),
            seriesStartDate=COALESCE(excluded.seriesStartDate, series.seriesStartDate),
            seriesType=COALESCE(excluded.seriesType, series.seriesType),
            seriesCountry=COALESCE(excluded.seriesCountry, series.seriesCountry),
            seriesTotalMatches=COALESCE(excluded.seriesTotalMatches, series.seriesTotalMatches)
    """, [r for r in rows if r[0]])
    conn.commit()
    c = cursor.execute("SELECT COUNT(*) FROM series").fetchone()[0]
    log(f"  ✅ series: {c} rows")


def _insert_matches(conn, cursor, log):
    rows = []
    patterns = (glob.glob("utils/json/4_series/matches/*.json") +
                glob.glob("utils/json/5_matches/lists/*.json") +
                glob.glob("utils/json/5_matches/info/*.json"))
    for f in patterns:
        try:
            with open(f) as fh: data = json.load(fh)
        except Exception: continue
        match_list = []
        for tm in data.get("typeMatches", []):
            for sm in tm.get("seriesMatches", []):
                for m in sm.get("seriesAdWrapper", {}).get("matches", []):
                    match_list.append(m.get("matchInfo", {}))
        if "matchInfo" in data:
            match_list.append(data["matchInfo"])
        for mi in match_list:
            t1id = mi.get("team1", {}).get("teamId")
            t2id = mi.get("team2", {}).get("teamId")
            t1n  = mi.get("team1", {}).get("teamName")
            t2n  = mi.get("team2", {}).get("teamName")
            wid, wtype, wmargin = _parse_winner(
                mi.get("status"), t1n, t1id, t2n, t2id)
            v = mi.get("venueInfo", {})
            rows.append((
                mi.get("matchId"), mi.get("seriesId"), mi.get("matchDesc"),
                _normalize_fmt(mi.get("matchFormat")),
                _ts_to_date(mi.get("startDate")),
                mi.get("state"), mi.get("status"),
                t1id, t2id, v.get("id"),
                v.get("ground"), v.get("city"), v.get("country"),
                mi.get("tossResults", {}).get("tossWinnerId"),
                mi.get("tossResults", {}).get("decision"),
                wid, wtype, wmargin
            ))
    cursor.executemany("""
        INSERT INTO matches
            (matchId,seriesId,matchDesc,matchFormat,matchDate,matchState,matchStatus,
             firstBatTeamId,secondBatTeamId,venueId,matchVenue,matchCity,matchCountry,
             tossWinTeamId,tossSelection,winningTeamId,winningType,winningMargin)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(matchId) DO UPDATE SET
            matchState=COALESCE(excluded.matchState, matches.matchState),
            matchStatus=COALESCE(excluded.matchStatus, matches.matchStatus),
            winningTeamId=COALESCE(excluded.winningTeamId, matches.winningTeamId),
            winningType=COALESCE(excluded.winningType, matches.winningType),
            winningMargin=COALESCE(excluded.winningMargin, matches.winningMargin)
    """, [r for r in rows if r[0]])
    conn.commit()
    c = cursor.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
    log(f"  ✅ matches: {c} rows")


def _insert_matchBowlings(conn, cursor, log):
    rows = []
    for f in glob.glob("utils/json/6_scorecards/*.json"):
        try:
            with open(f) as fh: data = json.load(fh)
        except Exception: continue
        matchId = _scorecard_match_id(data)
        venue = None
        r = cursor.execute("SELECT matchVenue FROM matches WHERE matchId=?", (matchId,)).fetchone()
        if r: venue = r[0]
        for inn in data.get("scorecard", []):
            for b in inn.get("bowler", []):
                rows.append((matchId, inn.get("inningsid"), b.get("id"),
                             _balls_to_overs(b.get("balls")), b.get("wickets"), b.get("economy"), venue))
    cursor.executemany("""
        INSERT INTO matchBowlings (matchId,innings,playerId,overs,wickets,economy,venue)
        VALUES (?,?,?,?,?,?,?)
        ON CONFLICT(matchId,innings,playerId) DO UPDATE SET
            overs=COALESCE(excluded.overs,matchBowlings.overs),
            wickets=COALESCE(excluded.wickets,matchBowlings.wickets),
            economy=COALESCE(excluded.economy,matchBowlings.economy),
            venue=COALESCE(excluded.venue,matchBowlings.venue)
    """, [r for r in rows if r[0] and r[2]])
    conn.commit()
    c = cursor.execute("SELECT COUNT(*) FROM matchBowlings").fetchone()[0]
    log(f"  ✅ matchBowlings: {c} rows")


def _insert_matchBattings(conn, cursor, log):
    rows = []
    for f in glob.glob("utils/json/6_scorecards/*.json"):
        try:
            with open(f) as fh: data = json.load(fh)
        except Exception: continue
        matchId = _scorecard_match_id(data)
        matchFormat = matchDate = quarter = None
        r = cursor.execute("SELECT matchFormat,matchDate FROM matches WHERE matchId=?", (matchId,)).fetchone()
        if r:
            matchFormat, matchDate = r
            if matchDate:
                m = int(matchDate[5:7])
                quarter = f"{matchDate[:4]}-Q{(m-1)//3+1}"
        for inn in data.get("scorecard", []):
            for bat in inn.get("batsman", []):
                balls = bat.get("balls", 0)
                if not balls or int(balls) == 0: continue
                overs = _balls_to_overs(balls)
                runs = bat.get("runs")
                avg = None
                try:
                    if overs and float(overs) > 0:
                        avg = round(int(runs) / float(overs), 2)
                except Exception: pass
                rows.append((matchId, inn.get("inningsid"), bat.get("id"),
                             matchFormat, matchDate, runs, overs,
                             bat.get("strkrate"), avg, quarter))
    cursor.executemany("""
        INSERT INTO matchBattings
            (matchId,innings,playerId,matchFormat,matchDate,runs,overs,strikeRate,battingAvg,quarter)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(matchId,innings,playerId) DO UPDATE SET
            runs=COALESCE(excluded.runs,matchBattings.runs),
            overs=COALESCE(excluded.overs,matchBattings.overs),
            strikeRate=COALESCE(excluded.strikeRate,matchBattings.strikeRate),
            battingAvg=COALESCE(excluded.battingAvg,matchBattings.battingAvg)
    """, [r for r in rows if r[0] and r[2]])
    conn.commit()
    c = cursor.execute("SELECT COUNT(*) FROM matchBattings").fetchone()[0]
    log(f"  ✅ matchBattings: {c} rows")


def _insert_matchPartnerships(conn, cursor, log):
    rows = []
    for f in glob.glob("utils/json/6_scorecards/*.json"):
        try:
            with open(f) as fh: data = json.load(fh)
        except Exception: continue
        matchId = _scorecard_match_id(data)
        for inn in data.get("scorecard", []):
            for p in inn.get("partnership", {}).get("partnership", []):
                b1, b2 = p.get("bat1id"), p.get("bat2id")
                if not b1 or not b2: continue
                rows.append((matchId, inn.get("inningsid"),
                             min(int(b1), int(b2)), max(int(b1), int(b2)),
                             p.get("totalruns")))
    cursor.executemany("""
        INSERT INTO matchPartnerships (matchId,innings,batsman1Id,batsman2Id,partnershipRuns)
        VALUES (?,?,?,?,?)
        ON CONFLICT(matchId,innings,batsman1Id,batsman2Id) DO UPDATE SET
            partnershipRuns=COALESCE(excluded.partnershipRuns,matchPartnerships.partnershipRuns)
    """, [r for r in rows if r[0]])
    conn.commit()
    c = cursor.execute("SELECT COUNT(*) FROM matchPartnerships").fetchone()[0]
    log(f"  ✅ matchPartnerships: {c} rows")


def _insert_battingCareers(conn, cursor, log):
    rows = []
    for f in glob.glob("utils/json/8_careers/battings/*.json"):
        try:
            with open(f) as fh: data = json.load(fh)
        except Exception: continue
        try:
            playerId = data.get("appIndex").get("webURL").split("/")[4]
        except Exception: continue
        headers = data.get("headers", [])
        values  = data.get("values", [])
        def sv(idx, col):
            try:
                v = values[idx].get("values", [])[col]
                return v if v not in ("","-",None) else None
            except Exception: return None
        for i in range(1, len(headers)):
            rows.append((playerId, headers[i].upper(),
                         sv(0,i), sv(2,i), _balls_to_overs(sv(3,i)),
                         sv(4,i), sv(5,i), sv(6,i), sv(12,i)))
    cursor.executemany("""
        INSERT INTO battingCareers
            (playerId,matchFormat,totalMatches,totalRuns,overs,highestScore,battingAvg,strikeRate,hundreds)
        VALUES (?,?,?,?,?,?,?,?,?)
        ON CONFLICT(playerId,matchFormat) DO UPDATE SET
            totalMatches=COALESCE(excluded.totalMatches,battingCareers.totalMatches),
            totalRuns=COALESCE(excluded.totalRuns,battingCareers.totalRuns),
            battingAvg=COALESCE(excluded.battingAvg,battingCareers.battingAvg),
            strikeRate=COALESCE(excluded.strikeRate,battingCareers.strikeRate),
            hundreds=COALESCE(excluded.hundreds,battingCareers.hundreds)
    """, rows)
    conn.commit()
    c = cursor.execute("SELECT COUNT(*) FROM battingCareers").fetchone()[0]
    log(f"  ✅ battingCareers: {c} rows")


def _insert_bowlingCareers(conn, cursor, log):
    rows = []
    for f in glob.glob("utils/json/8_careers/bowlings/*.json"):
        try:
            with open(f) as fh: data = json.load(fh)
        except Exception: continue
        try:
            playerId = data.get("appIndex").get("webURL").split("/")[4]
        except Exception: continue
        headers = data.get("headers", [])
        values  = data.get("values", [])
        def sv(idx, col):
            try:
                v = values[idx].get("values", [])[col]
                return v if v not in ("","-",None) else None
            except Exception: return None
        for i in range(1, len(headers)):
            rows.append((playerId, headers[i].upper(),
                         sv(0,i), _balls_to_overs(sv(2,i)),
                         sv(5,i), sv(7,i), sv(6,i)))
    cursor.executemany("""
        INSERT INTO bowlingCareers
            (playerId,matchFormat,totalMatches,overs,wickets,economy,bowlingAvg)
        VALUES (?,?,?,?,?,?,?)
        ON CONFLICT(playerId,matchFormat) DO UPDATE SET
            totalMatches=COALESCE(excluded.totalMatches,bowlingCareers.totalMatches),
            wickets=COALESCE(excluded.wickets,bowlingCareers.wickets),
            economy=COALESCE(excluded.economy,bowlingCareers.economy),
            bowlingAvg=COALESCE(excluded.bowlingAvg,bowlingCareers.bowlingAvg)
    """, rows)
    conn.commit()
    c = cursor.execute("SELECT COUNT(*) FROM bowlingCareers").fetchone()[0]
    log(f"  ✅ bowlingCareers: {c} rows")


def _insert_battingRecords(conn, cursor, log):
    rows = []
    for f in glob.glob("utils/json/7_records/battings/*.json"):
        try:
            with open(f) as fh: data = json.load(fh)
        except Exception: continue
        statType, matchFormat, year, teamId = _parse_records_filter(cursor, data, f)
        headers = data.get("headers", [])
        if "HS" in headers: continue
        lastH = headers[-1] if headers else ""
        for player in data.get("values", []):
            vals = player.get("values", [])
            if len(vals) < 2: continue
            rows.append((statType, year, matchFormat, teamId,
                         vals[0], vals[2] if len(vals)>2 else None,
                         vals[4] if len(vals)>4 else None,
                         vals[5] if lastH=="SR"  and len(vals)>5 else None,
                         vals[5] if lastH=="Avg" and len(vals)>5 else None))
    cursor.executemany("""
        INSERT INTO battingRecords
            (statType,year,matchFormat,teamId,playerId,totalMatches,runs,strikeRate,battingAvg)
        VALUES (?,?,?,?,?,?,?,?,?)
        ON CONFLICT(statType,year,matchFormat,teamId,playerId) DO UPDATE SET
            totalMatches=COALESCE(excluded.totalMatches,battingRecords.totalMatches),
            runs=COALESCE(excluded.runs,battingRecords.runs)
    """, rows)
    conn.commit()
    c = cursor.execute("SELECT COUNT(*) FROM battingRecords").fetchone()[0]
    log(f"  ✅ battingRecords: {c} rows")


def _insert_bowlingRecords(conn, cursor, log):
    rows = []
    for f in glob.glob("utils/json/7_records/bowlings/*.json"):
        try:
            with open(f) as fh: data = json.load(fh)
        except Exception: continue
        statType, matchFormat, year, teamId = _parse_records_filter(cursor, data, f)
        headers = data.get("headers", [])
        lastH = headers[-1] if headers else ""
        for player in data.get("values", []):
            vals = player.get("values", [])
            if len(vals) < 2: continue
            rows.append((statType, year, matchFormat, teamId,
                         vals[0], vals[2] if len(vals)>2 else None,
                         vals[3] if len(vals)>3 else None,
                         vals[4] if len(vals)>4 else None,
                         vals[5] if lastH=="Eco" and len(vals)>5 else None,
                         vals[5] if lastH=="Avg" and len(vals)>5 else None))
    cursor.executemany("""
        INSERT INTO bowlingRecords
            (statType,year,matchFormat,teamId,playerId,totalMatches,overs,wickets,economy,bowlingAvg)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(statType,year,matchFormat,teamId,playerId) DO UPDATE SET
            wickets=COALESCE(excluded.wickets,bowlingRecords.wickets),
            economy=COALESCE(excluded.economy,bowlingRecords.economy)
    """, rows)
    conn.commit()
    c = cursor.execute("SELECT COUNT(*) FROM bowlingRecords").fetchone()[0]
    log(f"  ✅ bowlingRecords: {c} rows")


def _insert_highestScoreRecords(conn, cursor, log):
    # Delete existing before re-inserting (no unique key for dedup)
    cursor.execute("DELETE FROM highestScoreRecords")
    rows = []
    for f in glob.glob("utils/json/7_records/highest_scores/*.json"):
        try:
            with open(f) as fh: data = json.load(fh)
        except Exception: continue
        _, matchFormat, _, _ = _parse_records_filter(cursor, data, f)
        for player in data.get("values", []):
            vals = player.get("values", [])
            if len(vals) < 2: continue
            rows.append((vals[0], matchFormat,
                         vals[2] if len(vals)>2 else None,
                         _balls_to_overs(vals[3] if len(vals)>3 else None)))
    cursor.executemany("""
        INSERT INTO highestScoreRecords (playerId,matchFormat,highestScore,overs)
        VALUES (?,?,?,?)
    """, rows)
    conn.commit()
    c = cursor.execute("SELECT COUNT(*) FROM highestScoreRecords").fetchone()[0]
    log(f"  ✅ highestScoreRecords: {c} rows")


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

INSERT_FNS = [
    ("teams",               _insert_teams),
    ("venues",              _insert_venues),
    ("players",             _insert_players),
    ("teamPlayers",         _insert_teamPlayers),
    ("crudTable",           _insert_crudTable),
    ("series",              _insert_series),
    ("matches",             _insert_matches),
    ("matchBowlings",       _insert_matchBowlings),
    ("matchBattings",       _insert_matchBattings),
    ("matchPartnerships",   _insert_matchPartnerships),
    ("battingCareers",      _insert_battingCareers),
    ("bowlingCareers",      _insert_bowlingCareers),
    ("battingRecords",      _insert_battingRecords),
    ("bowlingRecords",      _insert_bowlingRecords),
    ("highestScoreRecords", _insert_highestScoreRecords),
]


def sync_new_data(log_callback=print) -> bool:
    """
    Append-only sync. Creates tables if missing, upserts records.
    CRUD entries are preserved. Safe to run repeatedly.
    """
    try:
        conn   = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        log_callback("🔄 Starting append sync…")
        for table, _ in INSERT_FNS:
            cursor.execute(DDL[table])
        conn.commit()
        for label, fn in INSERT_FNS:
            log_callback(f"⚙️  Processing {label}…")
            fn(conn, cursor, log_callback)
        conn.close()
        log_callback("✅ Append sync complete!")
        return True
    except Exception as e:
        log_callback(f"❌ Error: {e}")
        return False


def full_rebuild(log_callback=print) -> bool:
    """
    Full rebuild. Drops all tables and rebuilds from scratch.
    ⚠️ CRUD entries will be lost.
    """
    try:
        conn   = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        log_callback("⚠️  Dropping all tables…")
        for table in reversed(TABLES_ORDER):
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        conn.commit()
        log_callback("🔨 Rebuilding tables from JSON…")
        for table, _ in INSERT_FNS:
            cursor.execute(DDL[table])
        conn.commit()
        for label, fn in INSERT_FNS:
            log_callback(f"⚙️  Processing {label}…")
            fn(conn, cursor, log_callback)
        conn.close()
        log_callback("✅ Full rebuild complete!")
        return True
    except Exception as e:
        log_callback(f"❌ Error: {e}")
        return False


def get_table_counts() -> dict:
    """Return row counts for all tables as {table: count}."""
    counts = {}
    try:
        conn   = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        for table in TABLES_ORDER:
            try:
                c = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                counts[table] = c
            except Exception:
                counts[table] = 0
        conn.close()
    except Exception:
        for table in TABLES_ORDER:
            counts[table] = 0
    return counts
