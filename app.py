"""
Cricbuzz LiveStats — Main App
Run with: streamlit run app.py
"""
import streamlit as st
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="Cricbuzz LiveStats", page_icon="🏏", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;600;700&family=Source+Sans+3:wght@300;400;600&display=swap');

/* ── Hide Streamlit auto-nav ── */
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"],
[data-testid="stSidebarNavSeparator"] { display:none !important; }
#MainMenu,footer,header              { visibility:hidden !important; }

/* ── Base ── */
html,body,[class*="css"] {
    font-family:'Source Sans 3',sans-serif;
    background:#0d0d0d; color:#f1f1f1;
}
h1,h2,h3 { font-family:'Oswald',sans-serif; letter-spacing:1px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background:linear-gradient(180deg,#0a0a0a 0%,#0f172a 100%);
    border-right:2px solid #2563eb;
}
[data-testid="stSidebar"] * { color:#f1f1f1 !important; }

/* ── Stat cards ── */
.stat-card {
    background:#111827; border:1px solid #2563eb;
    border-radius:8px; padding:20px; text-align:center; margin:8px 0;
}
.stat-card h2 { color:#3b82f6; font-size:2rem; margin:0; }
.stat-card p  { color:#9ca3af; margin:4px 0 0; font-size:13px; }

/* ── Developer button at sidebar bottom ── */
div[data-testid="stSidebar"] .dev-btn-container {
    position:sticky; bottom:0;
    background:linear-gradient(0deg,#0a0a0a 60%,transparent);
    padding:12px 0 8px; margin-top:auto;
}
</style>
""", unsafe_allow_html=True)

# ── Session state defaults ─────────────────────────────────────
for key, default in [
    ("current_page",     "🏠  Home"),
    ("api_key",          ""),
    ("api_key_valid",    None),
    ("show_developer",   False),
    ("dev_authenticated",False),
    ("dev_fetch_results",[]),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏏 CricStats")
    st.markdown("---")

    NAV_PAGES = [
        "🏠  Home",
        "📺  Live Matches",
        "🏏  Player Stats",
        "🔍  SQL Analytics",
        "🛠   CRUD Operations",
    ]

    # Sync radio with session_state (home card clicks update current_page)
    current = st.session_state.get("current_page", "🏠  Home")
    if current not in NAV_PAGES:
        current = "🏠  Home"

    page = st.radio("Navigation", NAV_PAGES,
                    index=NAV_PAGES.index(current),
                    label_visibility="collapsed")

    # Keep session_state in sync if user clicks sidebar radio
    if page != st.session_state["current_page"]:
        st.session_state["current_page"] = page
        st.session_state["show_developer"] = False
        st.rerun()

    # ── Push developer button to very bottom ──────────────────
    st.markdown("<br>" * 8, unsafe_allow_html=True)
    st.markdown("---")

    if st.button("🔧 Developer", use_container_width=True,
                 help="Developer configuration — password protected"):
        st.session_state["show_developer"] = True
        st.rerun()

# ── PAGE ROUTING ──────────────────────────────────────────────
if st.session_state.get("show_developer"):
    from pages.developer import show
    show()

elif "Home" in st.session_state["current_page"]:
    from pages.home import show
    show()

elif "Live" in st.session_state["current_page"]:
    from pages.live_matches import show
    show()

elif "Player" in st.session_state["current_page"]:
    from pages.player_stats import show
    show()

elif "SQL" in st.session_state["current_page"]:
    from pages.sql_queries import show
    show()

elif "CRUD" in st.session_state["current_page"]:
    from pages.crud_operations import show
    show()
