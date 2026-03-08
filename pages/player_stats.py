import streamlit as st
import requests

# ── API Setup ────────────────────────────────────────────────
API_KEY = "c0bb2e1bf7msh2c687bd9e297ccfp152ea8jsnc723e10d20fd"
HEADERS = {
    "x-rapidapi-key":  API_KEY,
    "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
}
BASE_URL = "https://cricbuzz-cricket.p.rapidapi.com"


def search_player(player_name):
    """
    Search for players by name using the Cricbuzz API.
    Returns a list of players matching the search term.
    """
    url    = f"{BASE_URL}/stats/v1/player/search"
    params = {"plrN": player_name}

    response = requests.get(url, headers=HEADERS, params=params)
    data     = response.json()

    # Players are inside the "player" key
    return data.get("player", [])


def get_player_info(player_id):
    """
    Get basic info (name, age, country, role) for a player.
    """
    url      = f"{BASE_URL}/stats/v1/player/{player_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


def get_player_batting(player_id):
    """
    Get batting stats (runs, average, strike rate etc) for a player.
    """
    url      = f"{BASE_URL}/stats/v1/player/{player_id}/batting"
    response = requests.get(url, headers=HEADERS)
    return response.json()


def get_player_bowling(player_id):
    """
    Get bowling stats (wickets, economy, average etc) for a player.
    """
    url      = f"{BASE_URL}/stats/v1/player/{player_id}/bowling"
    response = requests.get(url, headers=HEADERS)
    return response.json()


def get_player_career(player_id):
    """
    Get career info (debut match, last match) for a player.
    """
    url      = f"{BASE_URL}/stats/v1/player/{player_id}/career"
    response = requests.get(url, headers=HEADERS)
    return response.json()


def show_batting_table(batting_data):
    """
    Display batting stats in a clean table format.
    The API returns data as headers + rows, so we parse it here.
    """
    headers = batting_data.get("headers", [])   # e.g. ["ROWHEADER", "Test", "ODI", "T20"]
    rows    = batting_data.get("values",  [])   # each row has a "values" list

    if not headers or not rows:
        st.info("No batting stats available.")
        return

    # Build a simple table: stat name → value per format
    formats = headers[1:]   # Remove "ROWHEADER", keep ["Test", "ODI", "T20", ...]

    # Show as columns — one column per format
    cols = st.columns(len(formats))
    for i, (col, fmt) in enumerate(zip(cols, formats)):
        with col:
            st.markdown(f"**{fmt}**")
            for row in rows:
                values = row.get("values", [])
                if len(values) > i + 1:
                    stat_name  = values[0]           # e.g. "Runs"
                    stat_value = values[i + 1]       # e.g. "4053"
                    st.markdown(f"{stat_name}: **{stat_value}**")


def show_bowling_table(bowling_data):
    """
    Display bowling stats in a clean table format.
    Same structure as batting.
    """
    headers = bowling_data.get("headers", [])
    rows    = bowling_data.get("values",  [])

    if not headers or not rows:
        st.info("No bowling stats available.")
        return

    formats = headers[1:]
    cols    = st.columns(len(formats))

    for i, (col, fmt) in enumerate(zip(cols, formats)):
        with col:
            st.markdown(f"**{fmt}**")
            for row in rows:
                values = row.get("values", [])
                if len(values) > i + 1:
                    stat_name  = values[0]
                    stat_value = values[i + 1]
                    # Skip rows that are all zeros — not interesting
                    if stat_value not in ["0", "0.0", "-/-"]:
                        st.markdown(f"{stat_name}: **{stat_value}**")


def show():
    st.markdown("## 🏏 Player Stats")
    st.markdown("Search any cricket player and see their live stats from Cricbuzz API.")
    st.markdown("---")

    # ── Step 1: Search for a player ─────────────────────────
    st.markdown("### Step 1 — Search Player")

    # Text input for player name
    search_name = st.text_input(
        "Enter player name",
        placeholder="e.g. Virat Kohli, Rohit, Bumrah..."
    )

    # When user clicks Search
    if st.button("🔍 Search", type="primary"):
        if not search_name.strip():
            st.warning("Please type a player name first!")
            return

        with st.spinner(f"Searching for '{search_name}'..."):
            players = search_player(search_name)

        if not players:
            st.error("No players found. Try a different name!")
            return

        # Save results in session state so they don't disappear
        st.session_state["search_results"] = players
        st.session_state["selected_player_id"] = None

    # ── Step 2: Show search results ──────────────────────────
    if "search_results" in st.session_state:
        players = st.session_state["search_results"]

        st.markdown("### Step 2 — Select a Player")
        st.markdown(f"Found **{len(players)}** player(s):")

        # Build a dropdown from search results
        # Format: "Player Name (Team)"
        options = {}
        for p in players:
            label = f"{p.get('name', 'Unknown')} — {p.get('teamName', '')}"
            options[label] = p.get("id")

        chosen_label = st.selectbox("Choose a player", list(options.keys()))
        chosen_id    = options[chosen_label]

        # Save the chosen player id
        st.session_state["selected_player_id"] = chosen_id

    # ── Step 3: Show player stats ────────────────────────────
    if st.session_state.get("selected_player_id"):
        player_id = st.session_state["selected_player_id"]

        st.markdown("---")
        st.markdown("### Step 3 — Player Details")

        with st.spinner("Loading player stats..."):
            info    = get_player_info(player_id)
            batting = get_player_batting(player_id)
            bowling = get_player_bowling(player_id)
            career  = get_player_career(player_id)

        # ── Basic info card ──────────────────────────────────
        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown(f"""
            <div style="
                background: #1a1a2e;
                border: 2px solid #e63946;
                border-radius: 10px;
                padding: 20px;
                text-align: center;
            ">
                <div style="font-size: 3rem;">🏏</div>
                <div style="color:#fff; font-size:1.3rem; font-weight:bold; margin-top:8px;">
                    {info.get('name', 'Unknown')}
                </div>
                <div style="color:#aaa; font-size:0.9rem;">
                    {info.get('intlTeam', '')}
                </div>
                <div style="color:#e63946; font-size:0.85rem; margin-top:6px;">
                    {info.get('role', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            # Show key facts in a simple grid
            facts = {
                "🎂 Date of Birth":  info.get("DoB", "N/A"),
                "📍 Birth Place":    info.get("birthPlace", "N/A"),
                "🏏 Batting Style":  info.get("bat", "N/A"),
                "🎳 Bowling Style":  info.get("bowl", "N/A"),
                "📏 Height":         info.get("height", "N/A"),
            }
            for label, value in facts.items():
                if value and value != "N/A":
                    st.markdown(f"**{label}:** {value}")

            # Show rankings if available
            rankings = info.get("rankings", {})
            bat_rank = rankings.get("bat", {})
            if bat_rank.get("testRank"):
                st.markdown(f"**🏆 Test Ranking:** #{bat_rank['testRank']}")

        # ── Career debut info ────────────────────────────────
        st.markdown("---")
        st.markdown("### 📅 Career Timeline")

        career_values = career.get("values", [])
        if career_values:
            cols = st.columns(len(career_values))
            for col, entry in zip(cols, career_values):
                with col:
                    fmt = entry.get("name", "").upper()
                    st.markdown(f"""
                    <div style="
                        background: #1a1a2e;
                        border: 1px solid #333;
                        border-radius: 8px;
                        padding: 12px;
                        text-align: center;
                    ">
                        <div style="color:#e63946; font-weight:bold;">{fmt}</div>
                        <div style="color:#aaa; font-size:0.75rem; margin-top:6px;">
                            Debut:<br/>
                            <span style="color:#fff;">{entry.get('debut', 'N/A')}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # ── Batting stats ────────────────────────────────────
        st.markdown("---")
        st.markdown("### 🏏 Batting Statistics")
        show_batting_table(batting)

        # ── Bowling stats ────────────────────────────────────
        st.markdown("---")
        st.markdown("### 🎳 Bowling Statistics")
        show_bowling_table(bowling)
