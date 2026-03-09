"""
Home Page — blue theme, clickable navigation cards.
"""
import streamlit as st
import sqlite3

DB_PATH = "utils/cricBuzz.db"

def get_db_counts():
    try:
        conn   = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        teams   = cursor.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
        players = cursor.execute("SELECT COUNT(*) FROM players").fetchone()[0]
        matches = cursor.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
        series  = cursor.execute("SELECT COUNT(*) FROM series").fetchone()[0]
        conn.close()
        return teams, players, matches, series
    except Exception:
        return 0, 0, 0, 0


def show():
    st.markdown("""
    <div style='text-align:center;padding:30px 0 10px 0;'>
        <h1 style='font-family:Oswald,sans-serif;font-size:3rem;
                   color:#2563eb;letter-spacing:3px;margin:0;'>
            🏏 CRICBUZZ LIVESTATS
        </h1>
        <p style='color:#888;font-size:1rem;letter-spacing:2px;margin-top:6px;'>
            REAL-TIME CRICKET INSIGHTS &amp; SQL ANALYTICS
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### 📊 What's in our Database?")
    teams, players, matches, series = get_db_counts()
    for col, val, label in zip(st.columns(4),
                                [teams, players, matches, 25],
                                ["Teams","Players","Matches","SQL Queries"]):
        with col:
            st.markdown(f"<div class='stat-card'><h2>{val}</h2><p>{label}</p></div>",
                        unsafe_allow_html=True)

    st.markdown("---")

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("### 📌 About This Project")
        st.markdown("""
A **cricket analytics dashboard** built using:
- 🐍 **Python** — Core language
- 🌐 **Cricbuzz RapidAPI** — Live cricket data
- 🗄 **SQLite** — Local database storage
- 📊 **Streamlit** — Interactive web UI
- 🔍 **SQL** — 25 analytics queries
        """)
    with col_r:
        st.markdown("### 🗂 Project Structure")
        st.code("""cricbuzz_project/
├── app.py
├── pages/
│   ├── home.py
│   ├── live_matches.py
│   ├── player_stats.py
│   ├── sql_queries.py
│   └── crud_operations.py
└── utils/
    ├── cricBuzz.db
    ├── fetch_engine.py
    ├── db_sync.py
    └── config.json""")

    st.markdown("---")
    st.markdown("### 🗺 Explore the App")
    st.caption("Click any card to navigate directly to that page.")

    PAGES = [
        ("📺","Live Matches",   "See live scores fetched directly from the Cricbuzz API",        "📺  Live Matches"),
        ("🏏","Player Stats",   "Search any player and see their career batting & bowling stats", "🏏  Player Stats"),
        ("🔍","SQL Analytics",  "Run 25 SQL queries on our database — beginner to advanced",      "🔍  SQL Analytics"),
        ("🛠","CRUD Operations","Add, update, or delete player records in the database",           "🛠   CRUD Operations"),
    ]

    cols = st.columns(4)
    for col, (icon, title, desc, page_key) in zip(cols, PAGES):
        with col:
            st.markdown(f"""
            <div style='background:#111827;border:1px solid #1e3a5f;border-radius:10px;
                        padding:20px 14px;text-align:center;height:155px;
                        display:flex;flex-direction:column;align-items:center;
                        justify-content:center;gap:5px;'>
                <div style='font-size:2.2rem;'>{icon}</div>
                <div style='color:#3b82f6;font-weight:700;font-size:0.92rem;'>{title}</div>
                <div style='color:#6b7280;font-size:0.74rem;line-height:1.4;'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Open {title}", key=f"nav_{title}", use_container_width=True):
                st.session_state["current_page"] = page_key
                st.rerun()

    st.markdown("---")
    st.caption("Built with Python • Streamlit • SQLite • Cricbuzz RapidAPI")
