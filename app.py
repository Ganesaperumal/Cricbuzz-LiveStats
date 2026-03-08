"""
Cricbuzz LiveStats - Main App
==============================
This is the starting point of our Streamlit app.
Run it with:  streamlit run app.py
"""

import streamlit as st

# ── Page Configuration ───────────────────────────────────────
# This sets the browser tab title, icon, and layout
st.set_page_config(
    page_title="Cricbuzz LiveStats",
    page_icon="🏏",
    layout="wide"
)

# ── Custom Styling ───────────────────────────────────────────
# We use CSS to make the app look nice with a dark cricket theme
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;600;700&family=Source+Sans+3:wght@300;400;600&display=swap');

/* Apply font to everything */
html, body, [class*="css"] {
    font-family: 'Source Sans 3', sans-serif;
    background-color: #0d0d0d;
    color: #f1f1f1;
}

/* Headings use a bolder font */
h1, h2, h3 {
    font-family: 'Oswald', sans-serif;
    letter-spacing: 1px;
}

/* Sidebar background */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0a0a 0%, #1a1a2e 100%);
    border-right: 2px solid #e63946;
}
[data-testid="stSidebar"] * { color: #f1f1f1 !important; }

/* Red accent cards */
.stat-card {
    background: #1a1a2e;
    border: 1px solid #e63946;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    margin: 8px 0;
}
.stat-card h2 { color: #e63946; font-size: 2rem; margin: 0; }
.stat-card p  { color: #aaa; margin: 4px 0 0 0; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar Navigation ───────────────────────────────────────
# This creates the left sidebar menu
with st.sidebar:
    st.markdown("## 🏏 CricStats")
    st.markdown("---")

    # Radio buttons for page selection
    page = st.radio(
        "Go to",
        [
            "🏠  Home",
            "📺  Live Matches",
            "🏏  Player Stats",
            "🔍  SQL Analytics",
            "🛠   CRUD Operations"
        ]
    )

    st.markdown("---")
    st.caption("Powered by Cricbuzz API")

# ── Page Routing ─────────────────────────────────────────────
# Based on which page the user selected, load that page file

if "Home" in page:
    from pages.home import show
    show()

elif "Live" in page:
    from pages.live_matches import show
    show()

elif "Player" in page:
    from pages.player_stats import show
    show()

elif "SQL" in page:
    from pages.sql_queries import show
    show()

elif "CRUD" in page:
    from pages.crud_operations import show
    show()
