"""
Developer Config Page
======================
Password-gated. Access via 🔧 Developer button in sidebar.
Default password: cricdev2024

Tabs:
  1. 🔑 API Key     — Enter, validate, save to .env
  2. 📥 Fetch Data  — Dropdown, fetch, auto-sync toggle, results log
  3. 🩺 File Health — Folder status grid with missing file details
  4. ⚙️ Configure   — Edit all fetch IDs, saved to config.json
  5. 🗄 DB Sync     — Sync New Data | Full Rebuild | table row counts
"""

import streamlit as st
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.fetch_engine  import (load_config, save_config, get_folder_health,
                                  run_fetch_option, validate_api_key,
                                  fetch_all_missing)
from utils.db_sync       import sync_new_data, full_rebuild, get_table_counts

DEV_PASSWORD = "cricdev2024"

# ─── CSS ──────────────────────────────────────────────────────
_CSS = """
<style>
.dev-header {
    display:flex; align-items:center; gap:14px;
    padding:18px 0 10px 0; border-bottom:2px solid #2563eb; margin-bottom:20px;
}
.dev-badge {
    background:#2563eb22; border:1px solid #2563eb66;
    border-radius:6px; padding:4px 12px;
    font-size:0.72rem; color:#60a5fa; font-weight:700;
    letter-spacing:1px; text-transform:uppercase;
}
.dev-title {
    font-family:Oswald,sans-serif; font-size:1.4rem;
    color:#f1f1f1; letter-spacing:2px; margin:0;
}

/* Health cards */
.hcard {
    background:#111827; border:1px solid #1e2a3a;
    border-radius:8px; padding:12px 14px;
}
.hcard-title { font-size:0.7rem; color:#888; font-family:monospace; }
.hbar-bg { height:5px; background:#1e2a3a; border-radius:3px; overflow:hidden; margin:5px 0 3px; }
.hbar-fill { height:100%; border-radius:3px; }
.hcard-count { font-size:0.65rem; color:#555; text-align:right; }

/* DB table grid */
.db-table-card {
    background:#111827; border:1px solid #1e2a3a;
    border-radius:6px; padding:10px 14px;
    display:flex; justify-content:space-between; align-items:center;
}
.db-table-name { font-size:0.78rem; color:#aaa; font-family:monospace; }
.db-table-count { font-size:1rem; font-weight:700; color:#2563eb; }

/* Config cards */
.ccfg-title {
    font-size:0.8rem; font-weight:700; color:#ccc;
    margin-bottom:8px; padding-bottom:6px;
    border-bottom:1px solid #1e2a3a;
}
.tag-hint { font-size:0.66rem; color:#444; margin-top:2px; }

/* Log box */
.log-box {
    background:#050510; border:1px solid #1a1a1a;
    border-radius:6px; padding:10px;
    max-height:280px; overflow-y:auto;
    font-size:0.75rem; font-family:monospace; line-height:1.8;
}
</style>
"""


# ─── Helpers ──────────────────────────────────────────────────

def _health_color(present, total):
    if total == 0: return "#333"
    r = present / total
    return "#22c55e" if r == 1.0 else "#f59e0b" if r >= 0.7 else "#ef4444"


def _parse_ids(raw):
    parts = [x.strip() for x in raw.replace("\n", ",").split(",") if x.strip()]
    out = []
    for p in parts:
        try: out.append(int(p))
        except ValueError: pass
    return out


def _parse_strs(raw):
    return [x.strip() for x in raw.replace("\n", ",").split(",") if x.strip()]


# ─── TAB 1: API Key ───────────────────────────────────────────

def _tab_api_key():
    st.markdown("### 🔑 RapidAPI Key")
    st.caption("Your key is stored in `utils/.env`. It is never sent anywhere except directly to the Cricbuzz RapidAPI.")

    key_set = bool(st.session_state.get("api_key", ""))
    status  = ("🟢 Key is set and validated" if st.session_state.get("api_key_valid") is True else
               "🔴 Key set but validation failed" if st.session_state.get("api_key_valid") is False else
               "🟡 Key set — not yet validated" if key_set else "⚫ No key entered")
    st.info(status)

    col1, col2 = st.columns([3, 1])
    with col1:
        new_key = st.text_input("Paste your RapidAPI key",
                                value=st.session_state.get("api_key", ""),
                                type="password", key="dev_api_key_field",
                                placeholder="Paste full key here…")
    with col2:
        save_env = st.checkbox("Save to utils/.env", value=True, key="dev_save_env")

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🔍 Validate Key", use_container_width=True):
            if not new_key:
                st.warning("Enter a key first.")
            else:
                with st.spinner("Testing key against API…"):
                    ok, msg = validate_api_key(new_key)
                st.session_state["api_key_valid"] = ok
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    with c2:
        if st.button("💾 Save Key", type="primary", use_container_width=True):
            if not new_key:
                st.warning("Enter a key first.")
            else:
                st.session_state["api_key"]       = new_key
                st.session_state["api_key_valid"] = None
                if save_env:
                    try:
                        env_path = os.path.join("utils", ".env")
                        lines, found = [], False
                        if os.path.exists(env_path):
                            with open(env_path) as f: lines = f.readlines()
                            for i, line in enumerate(lines):
                                if line.startswith("X_RAPIDAPI_KEY="):
                                    lines[i] = f'X_RAPIDAPI_KEY="{new_key}"\n'
                                    found = True
                        if not found:
                            lines.append(f'X_RAPIDAPI_KEY="{new_key}"\n')
                        with open(env_path, "w") as f: f.writelines(lines)
                        st.success("✅ Key saved to utils/.env and session.")
                    except Exception as e:
                        st.error(f"Could not write .env: {e}")
                else:
                    st.success("✅ Key saved to session only (not .env).")

    with c3:
        if st.button("🗑 Clear Key", use_container_width=True):
            st.session_state["api_key"]       = ""
            st.session_state["api_key_valid"] = None
            st.rerun()

    st.markdown("---")
    st.caption("Get a free key at [rapidapi.com → Cricbuzz Cricket API](https://rapidapi.com/hub)")


# ─── TAB 2: Fetch Data ────────────────────────────────────────

FETCH_OPTIONS = {
    "📡 Recent Matches (1 file, always fresh)":         "recent",
    "👤 India Team Players (1 file)":                   "players",
    "📋 Series List 2024 (4 files)":                    "series_list",
    "🏟 Series Matches (12 files)":                     "series_matches",
    "📍 Series Venues (6 files)":                       "series_venues",
    "ℹ️ Match Info (11 files)":                         "match_info",
    "📊 Scorecards (18 files)":                         "scorecards",
    "🏆 Highest Scores — Test/ODI/T20 (3 files)":       "highest_scores",
    "🏏 Batting Records (7 files)":                     "batting_records",
    "🧢 Batting Careers (14 files)":                    "batting_careers",
    "🎳 Bowling Careers (5 files)":                     "bowling_careers",
}


def _tab_fetch(cfg):
    st.markdown("### 📥 Fetch Data from API")

    api_key = st.session_state.get("api_key", "")
    if not api_key:
        st.warning("🔑 Go to the **API Key** tab and enter your key first.")

    col1, col2 = st.columns([3, 1])
    with col1:
        sel_label = st.selectbox("Select data to fetch", list(FETCH_OPTIONS.keys()),
                                 key="dev_fetch_select")
    with col2:
        auto_sync = st.checkbox("Auto-sync DB after fetch", value=False,
                                key="dev_auto_sync",
                                help="Runs append-only DB sync automatically after a successful fetch")

    # Fetch All Missing
    with st.expander("⚡ Fetch All Missing Files at once"):
        st.caption("Scans every folder, fetches only files that are absent. Recent Matches excluded.")
        if st.button("⚡ Fetch All Missing", type="primary", use_container_width=True,
                     disabled=not api_key):
            log_lines = []
            prog = st.progress(0, text="Starting…")
            log_area = st.empty()

            def on_prog(cur, tot, fname):
                prog.progress(cur / tot, text=f"{cur}/{tot}: {fname}")

            results = fetch_all_missing(api_key, cfg, progress_callback=on_prog)
            prog.empty()

            for r in results:
                log_lines.append(r["message"])

            fetched = sum(1 for r in results if r["status"] == "fetched")
            errors  = sum(1 for r in results if r["status"] == "error")
            html    = "".join(
                f"<div style='color:{'#f1f1f1' if r['status']=='fetched' else '#ef4444' if r['status']=='error' else '#444'}'>{r['message']}</div>"
                for r in results
            )
            log_area.markdown(f'<div class="log-box">{html}</div>', unsafe_allow_html=True)

            if errors:
                st.error(f"⬇️ {fetched} fetched  •  ❌ {errors} errors")
            else:
                st.success(f"⬇️ {fetched} files fetched!")

            if auto_sync and fetched > 0:
                st.info("🔄 Auto-syncing DB…")
                sync_log = []
                sync_new_data(log_callback=sync_log.append)
                st.success("✅ DB synced!")

    st.markdown("---")

    # Single option fetch
    fetch_btn = st.button("▶ Fetch & Save", type="primary",
                          disabled=not api_key, use_container_width=False)
    if fetch_btn:
        sel_key = FETCH_OPTIONS[sel_label]
        with st.spinner(f"Fetching {sel_label}…"):
            results = run_fetch_option(sel_key, api_key, cfg)
        st.session_state["dev_fetch_results"] = results
        st.session_state["fetcher_config"]    = cfg

        # Auto-sync if enabled and something was fetched
        if auto_sync and any(r["status"] == "fetched" for r in results):
            with st.spinner("Auto-syncing DB…"):
                sync_new_data()
            st.success("✅ DB synced after fetch!")

        st.rerun()

    # Results log
    results = st.session_state.get("dev_fetch_results", [])
    if results:
        fetched = sum(1 for r in results if r["status"] == "fetched")
        skipped = sum(1 for r in results if r["status"] == "skipped")
        errors  = sum(1 for r in results if r["status"] == "error")

        parts = []
        if fetched: parts.append(f"⬇️ {fetched} fetched")
        if skipped: parts.append(f"📁 {skipped} skipped")
        if errors:  parts.append(f"❌ {errors} errors")
        st.caption(" • ".join(parts))

        html = "".join(
            "<div style='color:{c};padding:1px 0'>{msg}"
            "<span style='color:#374151;font-size:0.65rem'>{ts}</span></div>".format(
                c="#f1f1f1" if r["status"]=="fetched" else "#ef4444" if r["status"]=="error" else "#374151",
                msg=r["message"],
                ts=f"  {r['last_fetched']}" if r.get("last_fetched") else ""
            )
            for r in results
        )
        st.markdown(f'<div class="log-box">{html}</div>', unsafe_allow_html=True)


# ─── TAB 3: File Health ───────────────────────────────────────

def _tab_health(cfg):
    st.markdown("### 🩺 File Health Dashboard")
    st.caption("Expected vs present files in every JSON folder. Click a card to see missing files.")

    if st.button("🔄 Refresh", key="health_refresh"):
        st.rerun()

    health = get_folder_health(cfg)
    cols   = st.columns(4)

    for i, row in enumerate(health):
        col   = cols[i % 4]
        pct   = int(row["present"] / row["total"] * 100) if row["total"] else 0
        color = _health_color(row["present"], row["total"])
        icon  = "✅" if pct == 100 else "⚠️" if pct >= 70 else "❌"

        with col:
            st.markdown(f"""
            <div class="hcard">
              <div class="hcard-title">{icon} {row['folder']}</div>
              <div class="hbar-bg">
                <div class="hbar-fill" style="width:{pct}%;background:{color}"></div>
              </div>
              <div class="hcard-count">{row['present']}/{row['total']}</div>
            </div>
            """, unsafe_allow_html=True)

            if row["missing"]:
                with col:
                    with st.expander(f"🔍 {len(row['missing'])} missing"):
                        for mf in row["missing"]:
                            st.caption(f"• {mf}")

    # Summary totals
    st.markdown("---")
    total_exp = sum(r["total"] for r in health)
    total_pre = sum(r["present"] for r in health)
    total_mis = total_exp - total_pre
    c1, c2, c3 = st.columns(3)
    c1.metric("📁 Total Expected", total_exp)
    c2.metric("✅ Present",        total_pre)
    c3.metric("❌ Missing",        total_mis, delta=f"-{total_mis}" if total_mis else "0",
              delta_color="inverse")


# ─── TAB 4: Configure IDs ─────────────────────────────────────

def _tab_configure(cfg):
    st.markdown("### ⚙️ Fetch Configuration")
    st.caption("Edit IDs and parameters. Click **💾 Save All** to persist to `utils/config.json`.")

    opt = cfg["options"]

    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1:
        st.markdown('<div class="ccfg-title">📡 Recent Matches</div>', unsafe_allow_html=True)
        st.text_input("Behaviour", "Always re-fetch (overwrite=True)",
                      disabled=True, key="cfg_recent_disp")
        st.markdown('<div class="tag-hint">⚠️ No configuration needed</div>', unsafe_allow_html=True)

    with r1c2:
        st.markdown('<div class="ccfg-title">👤 Team Players</div>', unsafe_allow_html=True)
        st.text_area("Team IDs", ", ".join(str(x) for x in opt["players"]["team_ids"]),
                     height=80, key="cfg_players",
                     help="2=India  3=Australia  5=England  6=SriLanka…")
        st.markdown('<div class="tag-hint">Comma-separated team IDs</div>', unsafe_allow_html=True)

    with r1c3:
        st.markdown('<div class="ccfg-title">📋 Series List</div>', unsafe_allow_html=True)
        st.text_input("Year(s)", ", ".join(opt["series_list"]["years"]), key="cfg_sl_years")
        st.text_input("Types",   ", ".join(opt["series_list"]["types"]), key="cfg_sl_types",
                      help="international, league, domestic, women")

    st.markdown("&nbsp;", unsafe_allow_html=True)
    r2c1, r2c2, r2c3 = st.columns(3)

    with r2c1:
        st.markdown('<div class="ccfg-title">🏟 Series Matches</div>', unsafe_allow_html=True)
        st.text_area("Series IDs", ", ".join(str(x) for x in opt["series_matches"]["series_ids"]),
                     height=100, key="cfg_sm")

    with r2c2:
        st.markdown('<div class="ccfg-title">📍 Series Venues</div>', unsafe_allow_html=True)
        st.text_area("Series IDs", ", ".join(str(x) for x in opt["series_venues"]["series_ids"]),
                     height=100, key="cfg_sv")

    with r2c3:
        st.markdown('<div class="ccfg-title">ℹ️ Match Info</div>', unsafe_allow_html=True)
        st.text_area("Match IDs", ", ".join(str(x) for x in opt["match_info"]["match_ids"]),
                     height=100, key="cfg_mi")

    st.markdown("&nbsp;", unsafe_allow_html=True)
    r3c1, r3c2, r3c3 = st.columns(3)

    with r3c1:
        st.markdown('<div class="ccfg-title">📊 Scorecards</div>', unsafe_allow_html=True)
        st.text_area("Match IDs", ", ".join(str(x) for x in opt["scorecards"]["match_ids"]),
                     height=100, key="cfg_sc")

    with r3c2:
        st.markdown('<div class="ccfg-title">🏆 Highest Scores</div>', unsafe_allow_html=True)
        st.text_input("Match Types", ", ".join(opt["highest_scores"]["match_types"]),
                      key="cfg_hs", help="test, odi, t20")

        br = opt["batting_records"]
        st.markdown('<div class="ccfg-title" style="margin-top:10px">🏏 Batting Records</div>', unsafe_allow_html=True)
        st.text_input("Team ID",    str(br["team_id"]),              key="cfg_br_team")
        st.text_input("Years",      ", ".join(br["years"]),          key="cfg_br_years")
        st.text_input("Stats Types", ", ".join(br["stats_types"]),   key="cfg_br_stats")

    with r3c3:
        st.markdown('<div class="ccfg-title">🧢 Batting Careers</div>', unsafe_allow_html=True)
        st.text_area("Player IDs", ", ".join(str(x) for x in opt["batting_careers"]["player_ids"]),
                     height=80, key="cfg_bc",
                     help="576=Rohit  587=Jadeja  9647=Hardik")
        st.markdown('<div class="ccfg-title" style="margin-top:8px">🎳 Bowling Careers</div>', unsafe_allow_html=True)
        st.text_area("Player IDs", ", ".join(str(x) for x in opt["bowling_careers"]["player_ids"]),
                     height=60, key="cfg_bw")

    st.markdown("---")
    cb1, cb2 = st.columns([2, 5])
    with cb1:
        save_all = st.button("💾 Save All to config.json", type="primary", use_container_width=True)

    if save_all:
        opt["players"]["team_ids"]           = _parse_ids(st.session_state.cfg_players)
        opt["series_list"]["years"]          = _parse_strs(st.session_state.cfg_sl_years)
        opt["series_list"]["types"]          = _parse_strs(st.session_state.cfg_sl_types)
        opt["series_matches"]["series_ids"]  = _parse_ids(st.session_state.cfg_sm)
        opt["series_venues"]["series_ids"]   = _parse_ids(st.session_state.cfg_sv)
        opt["match_info"]["match_ids"]       = _parse_ids(st.session_state.cfg_mi)
        opt["scorecards"]["match_ids"]       = _parse_ids(st.session_state.cfg_sc)
        opt["highest_scores"]["match_types"] = _parse_strs(st.session_state.cfg_hs)
        opt["batting_records"]["team_id"]    = int(st.session_state.cfg_br_team or 2)
        opt["batting_records"]["years"]      = _parse_strs(st.session_state.cfg_br_years)
        opt["batting_records"]["stats_types"]= _parse_strs(st.session_state.cfg_br_stats)
        opt["batting_careers"]["player_ids"] = _parse_ids(st.session_state.cfg_bc)
        opt["bowling_careers"]["player_ids"] = _parse_ids(st.session_state.cfg_bw)

        ok = save_config(cfg)
        st.session_state["fetcher_config"] = cfg
        with cb2:
            if ok: st.success("✅ Saved to config.json — persists across restarts.")
            else:  st.error("❌ Could not write config.json. Check permissions.")


# ─── TAB 5: DB Sync ───────────────────────────────────────────

def _tab_db_sync():
    st.markdown("### 🗄 Database Sync")

    # Table counts
    counts = get_table_counts()
    st.markdown("#### 📊 Current Table Row Counts")
    cols = st.columns(5)
    for i, (table, count) in enumerate(counts.items()):
        with cols[i % 5]:
            st.markdown(f"""
            <div class="db-table-card">
              <span class="db-table-name">{table}</span>
              <span class="db-table-count">{count:,}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🔄 Sync New Data")
        st.caption("""
        **Append-only.** Creates tables if missing, upserts new records.
        - ✅ Your CRUD entries are preserved
        - ✅ Fast — only inserts what's new
        - ✅ Safe to run multiple times
        """)
        if st.button("🔄 Sync New Data", type="primary", use_container_width=True):
            log_lines = []
            log_area  = st.empty()
            with st.spinner("Syncing…"):
                def log_cb(msg):
                    log_lines.append(msg)
                    html = "".join(f"<div style='color:#d1d5db'>{l}</div>" for l in log_lines)
                    log_area.markdown(f'<div class="log-box">{html}</div>', unsafe_allow_html=True)
                sync_new_data(log_callback=log_cb)
            st.success("✅ Append sync complete! Refresh to see updated counts.")

    with col2:
        st.markdown("#### 💣 Full Rebuild")
        st.caption("""
        **Drops all tables, rebuilds from scratch.**
        - ⚠️ Your CRUD entries will be **deleted**
        - ⚠️ All existing data wiped
        - ✅ Clean slate — no orphan records
        - ✅ Use after major JSON data changes
        """)
        confirm = st.checkbox("⚠️ I understand CRUD data will be lost", key="rebuild_confirm")
        if st.button("💣 Full Rebuild", type="secondary",
                     use_container_width=True, disabled=not confirm):
            log_lines = []
            log_area  = st.empty()
            with st.spinner("Rebuilding…"):
                def log_cb(msg):
                    log_lines.append(msg)
                    html = "".join(f"<div style='color:#d1d5db'>{l}</div>" for l in log_lines)
                    log_area.markdown(f'<div class="log-box">{html}</div>', unsafe_allow_html=True)
                full_rebuild(log_callback=log_cb)
            st.success("✅ Full rebuild complete! Refresh to see updated counts.")


# ─── Password Gate ────────────────────────────────────────────

def _password_gate() -> bool:
    """Returns True if developer is authenticated."""
    if st.session_state.get("dev_authenticated"):
        return True

    st.markdown("""
    <div style='display:flex;align-items:center;justify-content:center;
                height:60vh;flex-direction:column;gap:20px;'>
        <div style='font-size:3rem;'>🔧</div>
        <div style='font-family:Oswald,sans-serif;font-size:1.4rem;
                    color:#f1f1f1;letter-spacing:2px;'>DEVELOPER ACCESS</div>
        <div style='color:#555;font-size:0.85rem;'>Enter password to continue</div>
    </div>
    """, unsafe_allow_html=True)

    _, mid, _ = st.columns([2, 1, 2])
    with mid:
        pwd = st.text_input("Password", type="password", key="dev_pwd_input",
                            label_visibility="collapsed",
                            placeholder="Enter developer password…")
        if st.button("🔓 Unlock", type="primary", use_container_width=True):
            if pwd == DEV_PASSWORD:
                st.session_state["dev_authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Incorrect password.")
    return False


# ─── Main Entry ───────────────────────────────────────────────

def show():
    st.markdown(_CSS, unsafe_allow_html=True)

    if not _password_gate():
        return

    # ── Header ──────────────────────────────────────────────
    col_back, col_hdr = st.columns([1, 8])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state["show_developer"] = False
            st.session_state["dev_authenticated"] = False
            st.rerun()
    with col_hdr:
        st.markdown("""
        <div class="dev-header">
          <span class="dev-badge">🔧 Developer Mode</span>
          <span class="dev-title">DEVELOPER CONFIGURATION</span>
        </div>
        """, unsafe_allow_html=True)

    # Load config
    if "fetcher_config" not in st.session_state:
        st.session_state["fetcher_config"] = load_config()
    cfg = st.session_state["fetcher_config"]

    # ── Tabs ────────────────────────────────────────────────
    t1, t2, t3, t4, t5 = st.tabs([
        "🔑 API Key",
        "📥 Fetch Data",
        "🩺 File Health",
        "⚙️ Configure IDs",
        "🗄 DB Sync",
    ])

    with t1: _tab_api_key()
    with t2: _tab_fetch(cfg)
    with t3: _tab_health(cfg)
    with t4: _tab_configure(cfg)
    with t5: _tab_db_sync()
