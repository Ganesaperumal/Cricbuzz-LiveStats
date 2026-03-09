import streamlit as st
import requests
import os

BASE_URL = "https://cricbuzz-cricket.p.rapidapi.com"

def _get_api_key():
    key = st.session_state.get("api_key", "").strip()
    if key:
        return key
    try:
        with open(os.path.join("utils", ".env")) as f:
            for line in f:
                if line.startswith("X_RAPIDAPI_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return ""

def _get(api_key, endpoint, params=None):
    headers = {"x-rapidapi-key": api_key,
               "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"}
    resp = requests.get(f"{BASE_URL}/{endpoint}", headers=headers,
                        params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()

def show_batting_table(data):
    headers = data.get("headers", [])
    rows    = data.get("values", [])
    if not headers or not rows:
        st.info("No batting stats available.")
        return
    formats = headers[1:]
    cols = st.columns(len(formats))
    for i, (col, fmt) in enumerate(zip(cols, formats)):
        with col:
            st.markdown(f"**{fmt}**")
            for row in rows:
                vals = row.get("values", [])
                if len(vals) > i + 1 and vals[i+1] not in ("","-","0","0.0",None):
                    st.markdown(f"{vals[0]}: **{vals[i+1]}**")

def show_bowling_table(data):
    headers = data.get("headers", [])
    rows    = data.get("values", [])
    if not headers or not rows:
        st.info("No bowling stats available.")
        return
    formats = headers[1:]
    cols = st.columns(len(formats))
    for i, (col, fmt) in enumerate(zip(cols, formats)):
        with col:
            st.markdown(f"**{fmt}**")
            for row in rows:
                vals = row.get("values", [])
                if len(vals) > i + 1 and vals[i+1] not in ("","-","0","0.0","0/0",None):
                    st.markdown(f"{vals[0]}: **{vals[i+1]}**")

def show():
    st.markdown("## 🏏 Player Stats")
    st.markdown("Search any cricket player and see their live stats from Cricbuzz API.")
    st.markdown("---")

    api_key = _get_api_key()
    if not api_key:
        st.error("🔑 API key not set. Go to **🔧 Developer → API Key** and save your RapidAPI key.")
        return

    # ── Search ────────────────────────────────────────────────
    st.markdown("### Step 1 — Search Player")
    search_name = st.text_input("Enter player name",
                                placeholder="e.g. Virat Kohli, Rohit, Bumrah…")

    if st.button("🔍 Search", type="primary"):
        if not search_name.strip():
            st.warning("Type a player name first!")
        else:
            with st.spinner(f"Searching for '{search_name}'…"):
                try:
                    data = _get(api_key, "stats/v1/player/search", {"plrN": search_name})
                    players = data.get("player", [])
                except Exception as e:
                    st.error(f"❌ {e}")
                    players = []
            if not players:
                st.error("No players found. Try a different name!")
            else:
                st.session_state["search_results"]     = players
                st.session_state["selected_player_id"] = None

    # ── Select ────────────────────────────────────────────────
    if "search_results" in st.session_state:
        players = st.session_state["search_results"]
        st.markdown(f"### Step 2 — Select ({len(players)} found)")
        options = {f"{p.get('name','Unknown')} — {p.get('teamName','')}": p.get("id")
                   for p in players}
        chosen_label = st.selectbox("Choose a player", list(options.keys()))
        st.session_state["selected_player_id"] = options[chosen_label]

    # ── Stats ─────────────────────────────────────────────────
    if st.session_state.get("selected_player_id"):
        pid = st.session_state["selected_player_id"]
        st.markdown("---")
        st.markdown("### Step 3 — Player Details")

        with st.spinner("Loading stats…"):
            try:
                info    = _get(api_key, f"stats/v1/player/{pid}")
                batting = _get(api_key, f"stats/v1/player/{pid}/batting")
                bowling = _get(api_key, f"stats/v1/player/{pid}/bowling")
                career  = _get(api_key, f"stats/v1/player/{pid}/career")
            except Exception as e:
                st.error(f"❌ Could not load stats: {e}")
                return

        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"""
            <div style="background:#111827;border:2px solid #2563eb;border-radius:10px;
                        padding:20px;text-align:center;">
                <div style="font-size:3rem;">🏏</div>
                <div style="color:#fff;font-size:1.3rem;font-weight:bold;margin-top:8px;">
                    {info.get('name','Unknown')}</div>
                <div style="color:#9ca3af;font-size:0.9rem;">{info.get('intlTeam','')}</div>
                <div style="color:#3b82f6;font-size:0.85rem;margin-top:6px;">
                    {info.get('role','')}</div>
            </div>""", unsafe_allow_html=True)

        with col2:
            for label, val in [
                ("🎂 Date of Birth", info.get("DoB")),
                ("📍 Birth Place",   info.get("birthPlace")),
                ("🏏 Batting Style", info.get("bat")),
                ("🎳 Bowling Style", info.get("bowl")),
                ("📏 Height",        info.get("height")),
            ]:
                if val and val != "N/A":
                    st.markdown(f"**{label}:** {val}")
            bat_rank = info.get("rankings", {}).get("bat", {})
            if bat_rank.get("testRank"):
                st.markdown(f"**🏆 Test Ranking:** #{bat_rank['testRank']}")

        st.markdown("---")
        st.markdown("### 📅 Career Timeline")
        career_vals = career.get("values", [])
        if career_vals:
            for col, entry in zip(st.columns(len(career_vals)), career_vals):
                with col:
                    st.markdown(f"""
                    <div style="background:#111827;border:1px solid #1e3a5f;
                                border-radius:8px;padding:12px;text-align:center;">
                        <div style="color:#3b82f6;font-weight:bold;">
                            {entry.get('name','').upper()}</div>
                        <div style="color:#9ca3af;font-size:0.75rem;margin-top:6px;">
                            Debut:<br/>
                            <span style="color:#fff;">{entry.get('debut','N/A')}</span>
                        </div>
                    </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 🏏 Batting Statistics")
        show_batting_table(batting)

        st.markdown("---")
        st.markdown("### 🎳 Bowling Statistics")
        show_bowling_table(bowling)
