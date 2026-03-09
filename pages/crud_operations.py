"""
CRUD Operations Page
=====================
C → Create  (Add new records)
R → Read    (View records)
U → Update  (Edit records)
D → Delete  (Remove records)

Table: crudTable — columns: playerId, playerName, team, playingRole
"""

import streamlit as st
import sqlite3
import pandas as pd
import time

DB_PATH = "utils/cricBuzz.db"


def get_all_players():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT playerId as id, playerName as name, team, playingRole as role "
        "FROM crudTable ORDER BY playerId",
        conn
    )
    conn.close()
    return df


def add_player(pid, name, team, role):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO crudTable (playerId, playerName, team, playingRole)
        VALUES (?, ?, ?, ?)
    """, (pid, name, team, role))
    conn.commit()
    conn.close()


def update_player(pid, name, team, role):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        UPDATE crudTable
        SET playerName=?, team=?, playingRole=?
        WHERE playerId=?
    """, (name, team, role, pid))
    conn.commit()
    conn.close()


def delete_player(pid):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM crudTable WHERE playerId=?", (pid,))
    conn.commit()
    conn.close()


def show():
    st.markdown("## 🛠 CRUD Operations")
    st.markdown("**CRUD** = Create, Read, Update, Delete — the four basic database operations.")
    st.markdown("---")

    tab_add, tab_update, tab_delete, tab_view = st.tabs([
        "➕ Add Player",
        "✏️ Edit Player",
        "🗑 Delete Player",
        "📋 View All",
    ])

    # ── TAB 1: ADD ────────────────────────────────────────────
    with tab_add:
        st.markdown("### ➕ Add a New Player")

        with st.form("add_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                new_id   = st.number_input("Player ID (unique)", min_value=1, step=1, value=1234)
                new_name = st.text_input("Full Name")
            with col2:
                new_team = st.text_input("International Team")
                new_role = st.selectbox("Role", [
                    "Batsman", "Bowler",
                    "Batting Allrounder", "Bowling Allrounder", "WK-Batsman"
                ])

            if st.form_submit_button("✅ Add Player", type="primary"):
                if not new_name:
                    st.error("Name is required!")
                else:
                    try:
                        add_player(int(new_id), new_name, new_team, new_role)
                        st.success(f"✅ **{new_name}** added!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    # ── TAB 2: UPDATE ─────────────────────────────────────────
    with tab_update:
        st.markdown("### ✏️ Edit an Existing Player")
        df = get_all_players()

        if df.empty:
            st.info("No players found.")
        else:
            options = {f"{r['name']} (ID: {r['id']})": r['id'] for _, r in df.iterrows()}
            sel_label = st.selectbox("Select player to edit", list(options.keys()))
            sel_id    = options[sel_label]
            row       = df[df["id"] == sel_id].iloc[0]

            with st.form("edit_form"):
                col1, col2 = st.columns(2)
                with col1:
                    upd_name = st.text_input("Player Name", value=row["name"])
                    upd_team = st.text_input("Team",        value=row["team"])
                with col2:
                    upd_role = st.text_input("Role",        value=row["role"])

                if st.form_submit_button("💾 Save Changes", type="primary"):
                    try:
                        update_player(sel_id, upd_name, upd_team, upd_role)
                        st.success(f"✅ **{upd_name}** updated!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    # ── TAB 3: DELETE ─────────────────────────────────────────
    with tab_delete:
        st.markdown("### 🗑 Delete a Player")
        st.warning("⚠️ This cannot be undone!")

        df = get_all_players()
        if df.empty:
            st.info("No players to delete.")
        else:
            options = {
                f"{r['name']} (ID: {r['id']}) — {r['team']} ({r['role']})": r['id']
                for _, r in df.iterrows()
            }
            chosen_label = st.selectbox("Select player to delete", list(options.keys()))
            chosen_id    = options[chosen_label]
            confirmed    = st.checkbox(f"Yes, delete **{chosen_label}**")

            if st.button("🗑 Delete", type="primary", disabled=not confirmed):
                try:
                    delete_player(chosen_id)
                    st.success("✅ Player deleted!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    # ── TAB 4: VIEW ───────────────────────────────────────────
    with tab_view:
        st.markdown("### 📋 All Players in Database")
        df = get_all_players()

        search = st.text_input("🔎 Search by name or team")
        if search:
            mask = (
                df["name"].str.contains(search, case=False, na=False) |
                df["team"].str.contains(search, case=False, na=False)
            )
            df = df[mask]

        st.markdown(f"Showing **{len(df)}** players")
        st.dataframe(df, use_container_width=True, hide_index=True)
