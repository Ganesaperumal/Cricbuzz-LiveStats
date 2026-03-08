"""
Home Page
==========
This is the welcome page of our Cricbuzz LiveStats app.
It shows a project overview and quick stats.
"""

import streamlit as st
import sqlite3

DB_PATH = "utils/cricBuzz.db"

def get_db_counts():
    """
    Connect to our SQLite database and count how many
    records we have in each table.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Count rows in each table
        cursor.execute("SELECT COUNT(*) FROM teams")
        teams = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM players")
        players = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM matches")
        matches = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM series")
        series = cursor.fetchone()[0]

        conn.close()
        return teams, players, matches, series

    except Exception as e:
        # If database not found, return zeros
        return 0, 0, 0, 0


def show():
    # ── App Title ────────────────────────────────────────────
    st.markdown("""
    <div style='text-align:center; padding: 30px 0 20px 0;'>
        <h1 style='font-family:Oswald,sans-serif; font-size:3rem;
                   color:#e63946; letter-spacing:3px;'>
            🏏 CRICBUZZ LIVESTATS
        </h1>
        <p style='color:#888; font-size:1rem; letter-spacing:2px;'>
            REAL-TIME CRICKET INSIGHTS & SQL ANALYTICS
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Quick Stats from Database ────────────────────────────
    st.markdown("### 📊 What's in our Database?")

    teams, players, matches, series = get_db_counts()

    col1, col2, col3, col4 = st.columns(4)

    # Each column shows one stat
    with col1:
        st.markdown(f"""
        <div class='stat-card'>
            <h2>{teams}</h2>
            <p>Teams</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class='stat-card'>
            <h2>{players}</h2>
            <p>Players</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class='stat-card'>
            <h2>{matches}</h2>
            <p>Matches</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class='stat-card'>
            <h2>25</h2>
            <p>SQL Queries</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── About Section ────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 📌 About This Project")
        st.markdown("""
        This project is a **cricket analytics dashboard** built using:

        - 🐍 **Python** — The programming language we use
        - 🌐 **Cricbuzz API** — Gives us live cricket data
        - 🗄 **SQLite** — A simple database to store data
        - 📊 **Streamlit** — Turns our Python code into a website
        - 🔍 **SQL** — Language to query the database

        We fetch real cricket data from the internet and
        display it in a clean, interactive dashboard!
        """)

    with col_right:
        st.markdown("### 🗂 Project Files")
        st.code("""
cricbuzz_livestats/
├── app.py               ← Start here! Main file
├── data_loader.py       ← Loads JSON into database
├── cricbuzz.db          ← Our SQLite database
└── pages/
    ├── home.py          ← This page
    ├── live_matches.py  ← Live API data
    ├── player_stats.py  ← Player search + stats
    ├── sql_queries.py   ← 25 SQL queries
    └── crud_operations.py ← Add/Edit/Delete
        """)

    st.markdown("---")

    # ── Page Guide ───────────────────────────────────────────
    st.markdown("### 🗺 Pages in This App")

    col1, col2, col3, col4 = st.columns(4)

    pages = [
        ("📺", "Live Matches",
         "See live scores fetched directly from the Cricbuzz API"),
        ("🏏", "Player Stats",
         "Search any player and see their career batting & bowling stats"),
        ("🔍", "SQL Analytics",
         "Run 25 SQL queries on our database — beginner to advanced"),
        ("🛠", "CRUD Operations",
         "Add, update, or delete player records in the database"),
    ]

    for col, (icon, title, desc) in zip([col1, col2, col3, col4], pages):
        with col:
            st.markdown(f"""
            <div style='background:#1a1a2e; border:1px solid #333;
                        border-radius:8px; padding:16px; text-align:center;
                        height:150px;'>
                <div style='font-size:2rem;'>{icon}</div>
                <div style='color:#e63946; font-weight:bold;
                            margin:8px 0 4px 0;'>{title}</div>
                <div style='color:#888; font-size:0.8rem;'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption("Built with Python • Streamlit • SQLite • Cricbuzz RapidAPI")
