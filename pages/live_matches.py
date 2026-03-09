import streamlit as st
import requests
import os

def _get_api_key():
    """Read key from session_state first, then utils/.env"""
    key = st.session_state.get("api_key", "").strip()
    if key:
        return key
    try:
        env_path = os.path.join("utils", ".env")
        with open(env_path) as f:
            for line in f:
                if line.startswith("X_RAPIDAPI_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return ""

FLAG_MAP = {
    "IND":"🇮🇳","AUS":"🇦🇺","ENG":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","PAK":"🇵🇰","SA":"🇿🇦",
    "NZ":"🇳🇿","WI":"🏝️","SL":"🇱🇰","BAN":"🇧🇩","ZIM":"🇿🇼",
    "AFG":"🇦🇫","IRE":"🇮🇪","SCO":"🏴󠁧󠁢󠁳󠁣󠁴󠁿","UAE":"🇦🇪","NAM":"🇳🇦",
}
FORMAT_BADGE = {
    "TEST":("🔴","#c0392b"),"ODI":("🟢","#27ae60"),
    "T20":("🔵","#2563eb"),"T20I":("🔵","#2563eb"),
}

def get_matches(api_key, endpoint="live"):
    url = f"https://cricbuzz-cricket.p.rapidapi.com/matches/v1/{endpoint}"
    headers = {"x-rapidapi-key": api_key,
               "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        out = []
        for tm in data.get("typeMatches", []):
            for sm in tm.get("seriesMatches", []):
                for m in sm.get("seriesAdWrapper", {}).get("matches", []):
                    out.append(m)
        return out, None
    except requests.exceptions.HTTPError as e:
        return [], f"API Error {e.response.status_code}: {e}"
    except Exception as e:
        return [], str(e)

def fmt_innings(data):
    parts = []
    for key in ["inngs1","inngs2"]:
        inn = data.get(key)
        if inn:
            parts.append(f"{inn.get('runs',0)}/{inn.get('wickets',0)} "
                         f"<small>({inn.get('overs',0)} ov)</small>")
    return " &amp; ".join(parts) if parts else "<small>Yet to bat</small>"

def show():
    st.markdown("## 📺 Live Matches")
    st.markdown("---")

    api_key = _get_api_key()
    if not api_key:
        st.error("🔑 API key not set. Go to **🔧 Developer → API Key** and save your RapidAPI key.")
        return

    # Toggle live vs recent
    mode = st.radio("Show", ["🟢 Live", "🕐 Recent"], horizontal=True, label_visibility="collapsed")
    endpoint = "live" if "Live" in mode else "recent"

    with st.spinner("Fetching matches…"):
        matches, err = get_matches(api_key, endpoint)

    if err:
        st.error(f"❌ {err}")
        return

    if not matches:
        st.info(f"No {endpoint} matches right now. Try again later!")
        return

    st.caption(f"{'🟢' if endpoint=='live' else '🕐'} {len(matches)} matches")

    for i in range(0, len(matches), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            if i + j >= len(matches):
                break
            m  = matches[i+j]
            mi = m.get("matchInfo") or {}
            ms = m.get("matchScore") or {}
            t1 = mi.get("team1") or {}
            t2 = mi.get("team2") or {}
            flag1 = FLAG_MAP.get(t1.get("teamSName",""), "🏏")
            flag2 = FLAG_MAP.get(t2.get("teamSName",""), "🏏")
            fmt_emoji, fmt_color = FORMAT_BADGE.get(mi.get("matchFormat",""), ("🏏","#6b7280"))
            state = mi.get("state","")
            status_color = "#f59e0b" if state in ("In Progress","Stumps","Lunch","Tea","Rain") \
                      else "#22c55e" if state == "Complete" else "#6b7280"
            status_dot   = "🟡" if state in ("In Progress","Stumps","Lunch","Tea","Rain") \
                      else "✅" if state == "Complete" else "🔘"
            v = mi.get("venueInfo") or {}

            col.markdown(f"""
<div style="background:#111827;border:1px solid #1e3a5f;border-radius:12px;
            padding:14px;margin-bottom:8px;">
  <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
    <span style="font-size:0.7rem;color:#6b7280;">{mi.get('matchDesc','')} • {mi.get('seriesName','')}</span>
    <span style="font-size:0.7rem;font-weight:bold;color:{fmt_color};
                 background:{fmt_color}22;padding:2px 8px;border-radius:20px;">
      {fmt_emoji} {mi.get('matchFormat','')}
    </span>
  </div>
  <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
    <div style="flex:1;">
      <div style="font-size:1rem;font-weight:bold;color:#fff;">{flag1} {t1.get('teamName','')}</div>
      <div style="font-size:0.85rem;color:#fbbf24;margin-top:2px;">{fmt_innings(ms.get('team1Score') or {})}</div>
    </div>
    <div style="color:#3b82f6;font-weight:bold;font-size:0.85rem;">VS</div>
    <div style="flex:1;text-align:right;">
      <div style="font-size:1rem;font-weight:bold;color:#fff;">{t2.get('teamName','')} {flag2}</div>
      <div style="font-size:0.85rem;color:#fbbf24;margin-top:2px;">{fmt_innings(ms.get('team2Score') or {})}</div>
    </div>
  </div>
  <hr style="border:none;border-top:1px solid #1e3a5f;margin:10px 0;">
  <div style="font-size:0.75rem;color:{status_color};">{status_dot} {mi.get('status','')}</div>
  <div style="font-size:0.7rem;color:#374151;margin-top:3px;">📍 {v.get('ground','')}, {v.get('city','')}</div>
</div>""", unsafe_allow_html=True)
