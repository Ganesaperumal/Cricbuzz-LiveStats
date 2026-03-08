import streamlit as st
import requests

API_KEY = "c0bb2e1bf7msh2c687bd9e297ccfp152ea8jsnc723e10d20fd"
HEADERS = {
    "x-rapidapi-key":  API_KEY,
    "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
}

# Map team short names to flag emojis
FLAG_MAP = {
    "IND": "🇮🇳", "AUS": "🇦🇺", "ENG": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "PAK": "🇵🇰", "SA":  "🇿🇦",
    "NZ":  "🇳🇿", "WI":  "🏝️",  "SL":  "🇱🇰", "BAN": "🇧🇩", "ZIM": "🇿🇼",
    "AFG": "🇦🇫", "IRE": "🇮🇪", "SCO": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "UAE": "🇦🇪", "NAM": "🇳🇦",
    "OTG": "🏏", "CNTBRY": "🏏", "AKL": "🏏", "ND":  "🏏", "WEL": "🏏",
    "CD":  "🏏", "INDA": "🇮🇳", "ENGA": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "AUT": "🇦🇹", "SUI": "🇨🇭",
    "BEL": "🇧🇪", "PORT": "🇵🇹", "MALTA": "🇲🇹",
}

FORMAT_BADGE = {
    "TEST": ("🔴", "#c0392b"), "ODI": ("🟢", "#27ae60"), "T20": ("🔵", "#2980b9"),
    "T20I": ("🔵", "#2980b9"),
}

def get_live_matches():
    url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"
    try:
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        all_matches = []
        for type_match in data.get("typeMatches", []):
            for series in type_match.get("seriesMatches", []):
                series_data = series.get("seriesAdWrapper", {})
                for match in series_data.get("matches", []):
                    all_matches.append(match)
        return all_matches
    except Exception as error:
        st.error(f"Could not fetch live data: {error}")
        return []


def format_innings(data):
    parts = []
    for key in ["inngs1", "inngs2"]:
        inn = data.get(key)
        if inn:
            parts.append(f"{inn.get('runs', 0)}/{inn.get('wickets', 0)} <small>({inn.get('overs', 0)} ov)</small>")
    return " &amp; ".join(parts) if parts else "<small>Yet to bat</small>"


def show():
    st.markdown("## 📺 Live Matches")
    st.markdown("Live scores via Cricbuzz API.")
    st.markdown("---")

    with st.spinner("Fetching matches..."):
        matches = get_live_matches()

    if not matches:
        st.warning("No live matches right now. Try again later!")
        return

    st.caption(f"🟢 {len(matches)} live/recent matches")

    # Render cards in columns of 2
    for i in range(0, len(matches), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            if i + j >= len(matches):
                break
            match = matches[i + j]

            match_info  = match.get("matchInfo")  or {}
            match_score = match.get("matchScore") or {}

            team1_info   = match_info.get("team1") or {}
            team2_info   = match_info.get("team2") or {}
            team1        = team1_info.get("teamName", "Team 1")
            team2        = team2_info.get("teamName", "Team 2")
            team1_short  = team1_info.get("teamSName", "")
            team2_short  = team2_info.get("teamSName", "")
            flag1        = FLAG_MAP.get(team1_short, "🏏")
            flag2        = FLAG_MAP.get(team2_short, "🏏")

            match_format = match_info.get("matchFormat", "")
            match_desc   = match_info.get("matchDesc", "")
            series_name  = match_info.get("seriesName", "")
            status       = match_info.get("status", "")
            venue        = match_info.get("venueInfo") or {}
            venue_name   = venue.get("ground", "")
            venue_city   = venue.get("city", "")
            state        = match_info.get("state", "")

            team1_score = format_innings(match_score.get("team1Score") or {})
            team2_score = format_innings(match_score.get("team2Score") or {})

            fmt_emoji, fmt_color = FORMAT_BADGE.get(match_format, ("🏏", "#7f8c8d"))

            # Status color
            if state in ("In Progress", "Stumps", "Lunch", "Tea", "Rain"):
                status_color = "#f39c12"
                status_dot   = "🟡"
            elif state == "Complete":
                status_color = "#2ecc71"
                status_dot   = "✅"
            else:
                status_color = "#95a5a6"
                status_dot   = "🔘"

            card = f"""
<div style="background:#1e1e2e;border:1px solid #2e2e4e;border-radius:12px;
            padding:14px;margin-bottom:8px;font-family:sans-serif;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
    <span style="font-size:0.7rem;color:#888;">{match_desc} • {series_name}</span>
    <span style="font-size:0.7rem;font-weight:bold;color:{fmt_color};
                 background:{fmt_color}22;padding:2px 7px;border-radius:20px;">
      {fmt_emoji} {match_format}
    </span>
  </div>
  <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
    <div style="flex:1;">
      <div style="font-size:1rem;font-weight:bold;color:#fff;">{flag1} {team1}</div>
      <div style="font-size:0.85rem;color:#f1c40f;margin-top:2px;">{team1_score}</div>
    </div>
    <div style="color:#e63946;font-weight:bold;font-size:0.85rem;">VS</div>
    <div style="flex:1;text-align:right;">
      <div style="font-size:1rem;font-weight:bold;color:#fff;">{team2} {flag2}</div>
      <div style="font-size:0.85rem;color:#f1c40f;margin-top:2px;">{team2_score}</div>
    </div>
  </div>
  <hr style="border:none;border-top:1px solid #2e2e4e;margin:10px 0;">
  <div style="font-size:0.75rem;color:{status_color};">{status_dot} {status}</div>
  <div style="font-size:0.7rem;color:#555;margin-top:3px;">📍 {venue_name}, {venue_city}</div>
</div>"""

            col.markdown(card, unsafe_allow_html=True)