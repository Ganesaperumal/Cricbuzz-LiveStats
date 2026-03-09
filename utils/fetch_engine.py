"""
Fetch Engine
=============
Handles all API fetch logic for the Data Fetcher sidebar.

Features:
  - validate_api_key()        → Idea 3: test key before fetching
  - get_folder_health()       → Idea 1: file health dashboard
  - run_fetch_option()        → fetch one selected option, skip existing files
  - fetch_all_missing()       → Idea 2: fetch every missing file in one shot
  - load_config() / save_config()
  - _record_timestamp()       → Idea 4: store last-fetched time per file
"""

import os
import json
import time
import requests
from datetime import datetime

# ── Paths ─────────────────────────────────────────────────────
BASE_URL    = "https://cricbuzz-cricket.p.rapidapi.com/"
JSON_FOLDER = os.path.join("utils", "json")
CONFIG_PATH = os.path.join("utils", "config.json")

# ── Config helpers ────────────────────────────────────────────

def load_config() -> dict:
    """Load config.json; return defaults if file is missing or corrupt."""
    defaults = {
        "options": {
            "players":          {"team_ids": [2]},
            "series_list":      {"years": ["2024"], "types": ["international","league","domestic","women"]},
            "series_matches":   {"series_ids": [7607,7175,8071,6885,6920,7476,8402,8404,9237,9638,10587,11253]},
            "series_venues":    {"series_ids": [6885,6920,7175,7476,7607,8071]},
            "match_info":       {"match_ids": [100290,117398,117440,138974,139175,139216,139285,70375,76570,91805,92021]},
            "scorecards":       {"match_ids": [100290,100292,100301,100337,100348,100366,115059,115095,117413,117416,117440,118853,130129,130146,130168,138974,139129,139478]},
            "highest_scores":   {"match_types": ["test","odi","t20"]},
            "batting_records":  {"team_id": 2, "years": ["2020","2022","2023","2025"], "stats_types": ["highestAvg","highestSr"]},
            "batting_careers":  {"player_ids": [576,587,9647,6557,7662,6250,10276,10863,11808,11855,13682,1457,247,26]},
            "bowling_careers":  {"player_ids": [587,6250,6557,7662,9647]},
        },
        "last_fetched": {}
    }
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure last_fetched key exists
            data.setdefault("last_fetched", {})
            data.setdefault("options", defaults["options"])
            return data
    except Exception:
        return defaults


def save_config(cfg: dict) -> bool:
    """Write config dict back to config.json. Returns True on success."""
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        return True
    except Exception:
        return False


def _record_timestamp(cfg: dict, file_key: str):
    """Store current datetime as last-fetched for a file key."""
    cfg["last_fetched"][file_key] = datetime.now().strftime("%Y-%m-%d %H:%M")


def get_last_fetched(cfg: dict, file_key: str) -> str:
    """Return human-readable last-fetched string or empty string."""
    return cfg.get("last_fetched", {}).get(file_key, "")


# ── API key validation (Idea 3) ───────────────────────────────

def validate_api_key(api_key: str) -> tuple[bool, str]:
    """
    Hit a lightweight endpoint to test if the key is valid.
    Returns (is_valid: bool, message: str).
    """
    if not api_key or len(api_key) < 10:
        return False, "Key too short — paste the full RapidAPI key."
    try:
        headers = {
            "x-rapidapi-key":  api_key,
            "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
        }
        resp = requests.get(
            BASE_URL + "matches/v1/recent",
            headers=headers,
            timeout=8
        )
        if resp.status_code == 200:
            return True, "✅ Key is valid!"
        elif resp.status_code == 403:
            return False, "❌ Invalid key — access denied (403)."
        elif resp.status_code == 429:
            return False, "⚠️ Key valid but rate-limited (429). Try again shortly."
        else:
            return False, f"❌ Unexpected status: {resp.status_code}"
    except requests.exceptions.Timeout:
        return False, "⏱ Request timed out — check your internet connection."
    except Exception as e:
        return False, f"❌ Error: {e}"


# ── File helpers ──────────────────────────────────────────────

def _file_path(subfolder: str, filename: str) -> str:
    return os.path.join(JSON_FOLDER, subfolder, filename)


def _file_exists(subfolder: str, filename: str) -> bool:
    # Exact match first
    p = _file_path(subfolder, filename)
    if os.path.isfile(p) and os.path.getsize(p) > 0:
        return True
    # Glob match: files like player_batting_576_rohit.json
    # when we expect player_batting_576.json
    stem = filename.replace(".json", "")
    folder_path = os.path.join(JSON_FOLDER, subfolder)
    import glob as _glob
    matches = _glob.glob(os.path.join(folder_path, f"{stem}*.json"))
    return any(os.path.getsize(m) > 0 for m in matches)


def _fetch_and_save(api_key: str, endpoint: str, subfolder: str,
                    filename: str, params: dict = None) -> tuple[bool, str]:
    """
    Fetch one URL and save to utils/json/<subfolder>/<filename>.
    Returns (success: bool, message: str).
    """
    headers = {
        "x-rapidapi-key":  api_key,
        "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
    }
    full_path = _file_path(subfolder, filename)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    try:
        resp = requests.get(BASE_URL + endpoint, headers=headers,
                            params=params, timeout=15)
        resp.raise_for_status()
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(resp.json(), f, indent=2)
        return True, f"⬇️  {filename}"
    except requests.exceptions.Timeout:
        return False, f"⏱ Timeout: {filename}"
    except Exception as e:
        return False, f"❌ {filename}: {e}"


# ── File health dashboard (Idea 1) ───────────────────────────

EXPECTED_FILES = {
    "3_players":            ["team_players_2.json"],
    "4_series/lists":       ["series_list_2024_international.json","series_list_2024_league.json",
                             "series_list_2024_domestic.json","series_list_2024_women.json"],
    "4_series/matches":     [f"series_matches_{sid}.json"
                             for sid in [7607,7175,8071,6885,6920,7476,8402,8404,9237,9638,10587,11253]],
    "4_series/venues":      [f"series_venues_{sid}.json" for sid in [6885,6920,7175,7476,7607,8071]],
    "5_matches/lists":      ["matches_recent.json"],
    "5_matches/info":       [f"match_info_{mid}.json"
                             for mid in [100290,117398,117440,138974,139175,139216,139285,70375,76570,91805,92021]],
    "6_scorecards":         [f"match_scorecard_{mid}.json"
                             for mid in [100290,100292,100301,100337,100348,100366,115059,115095,
                                         117413,117416,117440,118853,130129,130146,130168,138974,139129,139478]],
    "7_records/highest_scores": [f"stats_highestScore_{t}.json" for t in ["test","odi","t20"]],
    "7_records/battings":   ["stats_highestAvg_2_odi.json","stats_highestAvg_2_t20.json",
                             "stats_highestAvg_2_test.json","stats_highestSr_2_2020.json",
                             "stats_highestSr_2_2022.json","stats_highestSr_2_2023.json",
                             "stats_highestSr_2_2025.json"],
    "8_careers/battings":   [f"player_batting_{pid}.json"
                             for pid in [576,587,9647,6557,7662,6250,10276,10863,11808,11855,13682,1457,247,26]],
    "8_careers/bowlings":   [f"player_bowling_{pid}.json" for pid in [587,6250,6557,7662,9647]],
}


def get_folder_health(cfg: dict) -> list[dict]:
    """
    Returns a list of dicts — one per folder — with:
      folder, total, present, missing_files
    Also updates EXPECTED_FILES dynamically from config IDs.
    """
    # Sync series_matches from config
    sm_ids = cfg["options"].get("series_matches", {}).get("series_ids", [])
    EXPECTED_FILES["4_series/matches"] = [f"series_matches_{sid}.json" for sid in sm_ids]

    sv_ids = cfg["options"].get("series_venues", {}).get("series_ids", [])
    EXPECTED_FILES["4_series/venues"] = [f"series_venues_{sid}.json" for sid in sv_ids]

    mi_ids = cfg["options"].get("match_info", {}).get("match_ids", [])
    EXPECTED_FILES["5_matches/info"] = [f"match_info_{mid}.json" for mid in mi_ids]

    sc_ids = cfg["options"].get("scorecards", {}).get("match_ids", [])
    EXPECTED_FILES["6_scorecards"] = [f"match_scorecard_{mid}.json" for mid in sc_ids]

    bp_ids = cfg["options"].get("batting_careers", {}).get("player_ids", [])
    EXPECTED_FILES["8_careers/battings"] = [f"player_batting_{pid}.json" for pid in bp_ids]

    bw_ids = cfg["options"].get("bowling_careers", {}).get("player_ids", [])
    EXPECTED_FILES["8_careers/bowlings"] = [f"player_bowling_{pid}.json" for pid in bw_ids]

    results = []
    for folder, files in EXPECTED_FILES.items():
        present = [f for f in files if _file_exists(folder, f)]
        missing = [f for f in files if not _file_exists(folder, f)]
        results.append({
            "folder":  folder,
            "total":   len(files),
            "present": len(present),
            "missing": missing,
        })
    return results


# ── Build file task list for each option ──────────────────────

def _build_tasks(option_key: str, cfg: dict) -> list[dict]:
    """
    Return list of task dicts: {endpoint, subfolder, filename, params, always_fresh}
    """
    opt = cfg["options"]
    tasks = []

    match_type_map = {"test": "1", "odi": "2", "t20": "3"}

    if option_key == "recent":
        tasks.append({"endpoint": "matches/v1/recent",
                      "subfolder": "5_matches/lists",
                      "filename": "matches_recent.json",
                      "params": None, "always_fresh": True})

    elif option_key == "players":
        for tid in opt["players"]["team_ids"]:
            tasks.append({"endpoint": f"teams/v1/{tid}/players",
                          "subfolder": "3_players",
                          "filename": f"team_players_{tid}.json",
                          "params": None, "always_fresh": False})

    elif option_key == "series_list":
        for year in opt["series_list"]["years"]:
            for stype in opt["series_list"]["types"]:
                tasks.append({"endpoint": f"series/v1/archives/{stype}",
                              "subfolder": "4_series/lists",
                              "filename": f"series_list_{year}_{stype}.json",
                              "params": {"year": year}, "always_fresh": False})

    elif option_key == "series_matches":
        for sid in opt["series_matches"]["series_ids"]:
            tasks.append({"endpoint": f"series/v1/{sid}",
                          "subfolder": "4_series/matches",
                          "filename": f"series_matches_{sid}.json",
                          "params": None, "always_fresh": False})

    elif option_key == "series_venues":
        for sid in opt["series_venues"]["series_ids"]:
            tasks.append({"endpoint": f"series/v1/{sid}/venues",
                          "subfolder": "4_series/venues",
                          "filename": f"series_venues_{sid}.json",
                          "params": None, "always_fresh": False})

    elif option_key == "match_info":
        for mid in opt["match_info"]["match_ids"]:
            tasks.append({"endpoint": f"mcenter/v1/{mid}",
                          "subfolder": "5_matches/info",
                          "filename": f"match_info_{mid}.json",
                          "params": None, "always_fresh": False})

    elif option_key == "scorecards":
        for mid in opt["scorecards"]["match_ids"]:
            tasks.append({"endpoint": f"mcenter/v1/{mid}/hscard",
                          "subfolder": "6_scorecards",
                          "filename": f"match_scorecard_{mid}.json",
                          "params": None, "always_fresh": False})

    elif option_key == "highest_scores":
        for mtype in opt["highest_scores"]["match_types"]:
            mt_id = match_type_map.get(mtype)
            if mt_id:
                tasks.append({"endpoint": "stats/v1/topstats/0",
                              "subfolder": "7_records/highest_scores",
                              "filename": f"stats_highestScore_{mtype}.json",
                              "params": {"statsType": "highestScore", "matchType": mt_id},
                              "always_fresh": False})

    elif option_key == "batting_records":
        br = opt["batting_records"]
        for stype in br.get("stats_types", []):
            for year in br.get("years", []):
                tasks.append({"endpoint": "stats/v1/topstats/0",
                              "subfolder": "7_records/battings",
                              "filename": f"stats_{stype}_{br['team_id']}_{year}.json",
                              "params": {"statsType": stype, "team": str(br["team_id"]), "year": year},
                              "always_fresh": False})

    elif option_key == "batting_careers":
        for pid in opt["batting_careers"]["player_ids"]:
            tasks.append({"endpoint": f"stats/v1/player/{pid}/batting",
                          "subfolder": "8_careers/battings",
                          "filename": f"player_batting_{pid}.json",
                          "params": None, "always_fresh": False})

    elif option_key == "bowling_careers":
        for pid in opt["bowling_careers"]["player_ids"]:
            tasks.append({"endpoint": f"stats/v1/player/{pid}/bowling",
                          "subfolder": "8_careers/bowlings",
                          "filename": f"player_bowling_{pid}.json",
                          "params": None, "always_fresh": False})

    return tasks


# ── Run fetch for one selected option ─────────────────────────

def run_fetch_option(option_key: str, api_key: str, cfg: dict) -> list[dict]:
    """
    Fetch all files for the selected option.
    Skips files that already exist (unless always_fresh=True).
    Returns list of result dicts: {filename, status, message, last_fetched}

    status: "fetched" | "skipped" | "error"
    """
    tasks   = _build_tasks(option_key, cfg)
    results = []

    for task in tasks:
        fname   = task["filename"]
        already = _file_exists(task["subfolder"], fname)

        if already and not task["always_fresh"]:
            lf = get_last_fetched(cfg, fname)
            results.append({
                "filename":     fname,
                "status":       "skipped",
                "message":      f"📁  {fname}",
                "last_fetched": lf,
            })
            continue

        ok, msg = _fetch_and_save(api_key, task["endpoint"],
                                  task["subfolder"], fname, task["params"])
        if ok:
            _record_timestamp(cfg, fname)
            save_config(cfg)

        results.append({
            "filename":     fname,
            "status":       "fetched" if ok else "error",
            "message":      msg,
            "last_fetched": get_last_fetched(cfg, fname),
        })
        time.sleep(0.8)   # be polite to the API

    return results


# ── Fetch All Missing (Idea 2) ────────────────────────────────

ALL_OPTION_KEYS = [
    "recent", "players", "series_list", "series_matches", "series_venues",
    "match_info", "scorecards", "highest_scores", "batting_records",
    "batting_careers", "bowling_careers",
]


def fetch_all_missing(api_key: str, cfg: dict,
                      progress_callback=None) -> list[dict]:
    """
    Scan every option, fetch only missing files.
    progress_callback(current, total, filename) called for each file.
    Returns combined results list.
    """
    # Build full task list, skip always_fresh (recent) to avoid wasting a call
    all_tasks = []
    for key in ALL_OPTION_KEYS:
        if key == "recent":
            continue
        all_tasks.extend(_build_tasks(key, cfg))

    # Filter to only missing
    missing = [t for t in all_tasks
               if not _file_exists(t["subfolder"], t["filename"])]

    if not missing:
        return [{"filename": "—", "status": "skipped",
                 "message": "📁  All files already exist. Nothing to fetch!", "last_fetched": ""}]

    results = []
    total   = len(missing)

    for i, task in enumerate(missing):
        fname = task["filename"]
        if progress_callback:
            progress_callback(i + 1, total, fname)

        ok, msg = _fetch_and_save(api_key, task["endpoint"],
                                  task["subfolder"], fname, task["params"])
        if ok:
            _record_timestamp(cfg, fname)
            save_config(cfg)

        results.append({
            "filename":     fname,
            "status":       "fetched" if ok else "error",
            "message":      msg,
            "last_fetched": get_last_fetched(cfg, fname),
        })
        time.sleep(0.8)

    return results
