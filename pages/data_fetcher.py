"""
Data Fetcher Config Page
=========================
Full-page configuration for all fetch options.
Shown when user clicks ⚙️ Configure in the sidebar.

Features:
  - File health dashboard (Idea 1)
  - Fetch All Missing button (Idea 2)
  - Config grid — edit IDs per option, saved to config.json
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.fetch_engine import (
    load_config, save_config, get_folder_health,
    fetch_all_missing, ALL_OPTION_KEYS
)

# ── Styling injected once ─────────────────────────────────────
_CSS = """
<style>
.cfg-header { color: #e63946; font-family: Oswald,sans-serif;
              letter-spacing: 2px; font-size: 1.3rem; margin-bottom: 2px; }
.cfg-sub    { color: #555; font-size: 0.8rem; margin-bottom: 20px; }

/* Health cards */
.hcard {
  background: #111827; border: 1px solid #1e2a3a;
  border-radius: 8px; padding: 12px 14px;
  display: flex; flex-direction: column; gap: 4px;
}
.hcard-title { font-size: 0.72rem; color: #888; font-family: monospace; }
.hcard-bar-bg {
  height: 6px; background: #1e2a3a; border-radius: 3px; overflow: hidden;
}
.hcard-bar-fill {
  height: 100%; border-radius: 3px;
  transition: width 0.4s;
}
.hcard-count { font-size: 0.68rem; color: #555; text-align: right; }

/* Config cards */
.ccfg-title {
  font-size: 0.8rem; font-weight: 700; color: #ccc;
  margin-bottom: 10px; padding-bottom: 6px;
  border-bottom: 1px solid #1e2a3a;
}
.tag-hint { font-size: 0.68rem; color: #444; margin-top: 2px; }
</style>
"""


def _health_color(present: int, total: int) -> str:
    if total == 0:
        return "#333"
    ratio = present / total
    if ratio == 1.0:
        return "#2ecc71"
    elif ratio >= 0.7:
        return "#f39c12"
    else:
        return "#e63946"


def _show_health_dashboard(cfg: dict):
    st.markdown("### 🩺 File Health Dashboard")
    st.caption("Live status of all expected files across every folder.")

    health = get_folder_health(cfg)

    cols = st.columns(4)
    for i, row in enumerate(health):
        col  = cols[i % 4]
        pct  = int(row["present"] / row["total"] * 100) if row["total"] else 0
        color = _health_color(row["present"], row["total"])
        status = "✅" if row["present"] == row["total"] else ("⚠️" if pct >= 70 else "❌")

        with col:
            st.markdown(f"""
            <div class="hcard">
              <div class="hcard-title">{status} {row['folder']}</div>
              <div class="hcard-bar-bg">
                <div class="hcard-bar-fill"
                     style="width:{pct}%;background:{color}"></div>
              </div>
              <div class="hcard-count">{row['present']}/{row['total']} files</div>
            </div>
            """, unsafe_allow_html=True)

        if row["missing"] and pct < 100:
            with col:
                with st.expander(f"Show {len(row['missing'])} missing"):
                    for mf in row["missing"]:
                        st.caption(f"• {mf}")


def _show_fetch_all(cfg: dict):
    """Idea 2: Fetch All Missing button."""
    st.markdown("---")
    st.markdown("### ⚡ Fetch All Missing Files")
    st.caption("Scans every folder and fetches only the files that are absent. Recent Matches is excluded (use sidebar for that).")

    api_key = st.session_state.get("api_key", "")
    if not api_key:
        st.warning("🔑 Enter your API key first using the **Enter API Key** button in the sidebar.")
        return

    if st.button("⚡ Fetch All Missing Now", type="primary", use_container_width=True):
        progress_bar = st.progress(0, text="Starting…")
        log_area     = st.empty()
        log_lines    = []

        def on_progress(current, total, fname):
            pct = int(current / total * 100)
            progress_bar.progress(pct / 100, text=f"Fetching {current}/{total}: {fname}")

        results = fetch_all_missing(api_key, cfg, progress_callback=on_progress)
        progress_bar.empty()

        fetched = sum(1 for r in results if r["status"] == "fetched")
        errors  = sum(1 for r in results if r["status"] == "error")

        for r in results:
            log_lines.append(r["message"])

        log_area.markdown(
            "<div style='background:#050510;border:1px solid #1a1a1a;border-radius:6px;"
            "padding:10px;max-height:260px;overflow-y:auto;font-size:0.78rem;'>"
            + "".join(f"<div style='padding:2px 0;color:{'#f1f1f1' if r['status']=='fetched' else '#e63946' if r['status']=='error' else '#555'}'>{r['message']}</div>"
                      for r in results)
            + "</div>",
            unsafe_allow_html=True
        )
        if errors:
            st.error(f"⬇️ {fetched} fetched  •  ❌ {errors} errors")
        else:
            st.success(f"⬇️ {fetched} files fetched successfully!")

        # Refresh health after fetch
        st.rerun()


def _parse_ids(raw: str) -> list[int]:
    """Parse comma-separated string of IDs into a list of ints."""
    parts = [x.strip() for x in raw.replace("\n", ",").split(",") if x.strip()]
    result = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            pass
    return result


def _parse_strings(raw: str) -> list[str]:
    """Parse comma-separated string of values into a list of stripped strings."""
    return [x.strip() for x in raw.replace("\n", ",").split(",") if x.strip()]


def _show_config_grid(cfg: dict):
    st.markdown("---")
    st.markdown("### ⚙️ Fetch Configuration")
    st.caption("Edit IDs and parameters for each option. Click **💾 Save All** to persist to `config.json`.")

    opt = cfg["options"]

    # ── Row 1 ──────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown('<div class="ccfg-title">📡 Recent Matches</div>', unsafe_allow_html=True)
        st.text_input("Behaviour", value="Always re-fetch (overwrite=True)",
                      disabled=True, key="cfg_recent_info",
                      help="This option always fetches fresh — no config needed.")
        st.markdown('<div class="tag-hint">⚠️ No configuration needed</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="ccfg-title">👤 Team Players</div>', unsafe_allow_html=True)
        tid_val = ", ".join(str(x) for x in opt["players"]["team_ids"])
        new_tids = st.text_area("Team IDs", value=tid_val, height=80, key="cfg_players",
                                help="2 = India. Add more IDs for other teams.")
        st.markdown('<div class="tag-hint">2=India  3=Australia  5=England…</div>',
                    unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="ccfg-title">📋 Series List</div>', unsafe_allow_html=True)
        yr_val   = ", ".join(opt["series_list"]["years"])
        type_val = ", ".join(opt["series_list"]["types"])
        new_yrs  = st.text_input("Year(s)", value=yr_val, key="cfg_sl_years")
        new_types = st.text_input("Types", value=type_val, key="cfg_sl_types",
                                  help="international, league, domestic, women")

    st.markdown("&nbsp;", unsafe_allow_html=True)

    # ── Row 2 ──────────────────────────────────────────────────
    c4, c5, c6 = st.columns(3)

    with c4:
        st.markdown('<div class="ccfg-title">🏟 Series Matches</div>', unsafe_allow_html=True)
        sm_val = ", ".join(str(x) for x in opt["series_matches"]["series_ids"])
        new_sm = st.text_area("Series IDs", value=sm_val, height=100, key="cfg_sm",
                              help="Paste series IDs — get them from Cricbuzz match URLs.")

    with c5:
        st.markdown('<div class="ccfg-title">📍 Series Venues</div>', unsafe_allow_html=True)
        sv_val = ", ".join(str(x) for x in opt["series_venues"]["series_ids"])
        new_sv = st.text_area("Series IDs", value=sv_val, height=100, key="cfg_sv")

    with c6:
        st.markdown('<div class="ccfg-title">ℹ️ Match Info</div>', unsafe_allow_html=True)
        mi_val = ", ".join(str(x) for x in opt["match_info"]["match_ids"])
        new_mi = st.text_area("Match IDs", value=mi_val, height=100, key="cfg_mi")

    st.markdown("&nbsp;", unsafe_allow_html=True)

    # ── Row 3 ──────────────────────────────────────────────────
    c7, c8, c9 = st.columns(3)

    with c7:
        st.markdown('<div class="ccfg-title">📊 Scorecards</div>', unsafe_allow_html=True)
        sc_val = ", ".join(str(x) for x in opt["scorecards"]["match_ids"])
        new_sc = st.text_area("Match IDs", value=sc_val, height=100, key="cfg_sc")

    with c8:
        st.markdown('<div class="ccfg-title">🏆 Highest Scores</div>', unsafe_allow_html=True)
        hs_val  = ", ".join(opt["highest_scores"]["match_types"])
        new_hs  = st.text_input("Match Types", value=hs_val, key="cfg_hs",
                                help="test, odi, t20")
        st.markdown('<div class="tag-hint">Options: test, odi, t20</div>', unsafe_allow_html=True)

    with c9:
        st.markdown('<div class="ccfg-title">🏏 Batting Records</div>', unsafe_allow_html=True)
        br      = opt["batting_records"]
        new_br_team  = st.text_input("Team ID",      value=str(br["team_id"]),       key="cfg_br_team")
        new_br_years = st.text_input("Years",         value=", ".join(br["years"]),  key="cfg_br_years")
        new_br_stats = st.text_input("Stats Types",   value=", ".join(br["stats_types"]), key="cfg_br_stats",
                                     help="highestAvg, highestSr, mostRuns, mostHundreds…")

    st.markdown("&nbsp;", unsafe_allow_html=True)

    # ── Row 4 ──────────────────────────────────────────────────
    c10, c11, _ = st.columns(3)

    with c10:
        st.markdown('<div class="ccfg-title">🧢 Batting Careers</div>', unsafe_allow_html=True)
        bc_val = ", ".join(str(x) for x in opt["batting_careers"]["player_ids"])
        new_bc = st.text_area("Player IDs", value=bc_val, height=100, key="cfg_bc",
                              help="576=Rohit  587=Jadeja  9647=Hardik…")
        st.markdown('<div class="tag-hint">576=Rohit  587=Jadeja  9647=Hardik  6557=Stokes</div>',
                    unsafe_allow_html=True)

    with c11:
        st.markdown('<div class="ccfg-title">🎳 Bowling Careers</div>', unsafe_allow_html=True)
        bw_val = ", ".join(str(x) for x in opt["bowling_careers"]["player_ids"])
        new_bw = st.text_area("Player IDs", value=bw_val, height=100, key="cfg_bw")

    # ── Save button ────────────────────────────────────────────
    st.markdown("---")
    col_btn, col_msg = st.columns([2, 5])

    with col_btn:
        save_clicked = st.button("💾 Save All to config.json",
                                 type="primary", use_container_width=True)

    if save_clicked:
        # Parse all fields back into cfg
        opt["players"]["team_ids"]              = _parse_ids(st.session_state.cfg_players)
        opt["series_list"]["years"]             = _parse_strings(st.session_state.cfg_sl_years)
        opt["series_list"]["types"]             = _parse_strings(st.session_state.cfg_sl_types)
        opt["series_matches"]["series_ids"]     = _parse_ids(st.session_state.cfg_sm)
        opt["series_venues"]["series_ids"]      = _parse_ids(st.session_state.cfg_sv)
        opt["match_info"]["match_ids"]          = _parse_ids(st.session_state.cfg_mi)
        opt["scorecards"]["match_ids"]          = _parse_ids(st.session_state.cfg_sc)
        opt["highest_scores"]["match_types"]    = _parse_strings(st.session_state.cfg_hs)
        opt["batting_records"]["team_id"]       = int(st.session_state.cfg_br_team or 2)
        opt["batting_records"]["years"]         = _parse_strings(st.session_state.cfg_br_years)
        opt["batting_records"]["stats_types"]   = _parse_strings(st.session_state.cfg_br_stats)
        opt["batting_careers"]["player_ids"]    = _parse_ids(st.session_state.cfg_bc)
        opt["bowling_careers"]["player_ids"]    = _parse_ids(st.session_state.cfg_bw)

        ok = save_config(cfg)
        with col_msg:
            if ok:
                st.success("✅ Saved to config.json — changes will persist across restarts.")
            else:
                st.error("❌ Could not write config.json. Check file permissions.")

        st.session_state["fetcher_config"] = cfg   # update in-memory copy


def show():
    """Main entry point called from app.py."""
    st.markdown(_CSS, unsafe_allow_html=True)

    # ── Page header + Back button ──────────────────────────────
    col_back, col_title = st.columns([1, 6])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state["show_data_config"] = False
            st.rerun()
    with col_title:
        st.markdown('<div class="cfg-header">⚙️ DATA FETCHER CONFIGURATION</div>', unsafe_allow_html=True)
        st.markdown('<div class="cfg-sub">Configure IDs · Check file health · Fetch missing data</div>',
                    unsafe_allow_html=True)

    st.markdown("---")

    # Load config (use cached version if available)
    if "fetcher_config" not in st.session_state:
        st.session_state["fetcher_config"] = load_config()
    cfg = st.session_state["fetcher_config"]

    # ── Sections ──────────────────────────────────────────────
    _show_health_dashboard(cfg)
    _show_fetch_all(cfg)
    _show_config_grid(cfg)
