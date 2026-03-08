"""
CRUD Operations Page
=====================
CRUD stands for:
  C → Create  (Add new records)
  R → Read    (View records)
  U → Update  (Edit records)
  D → Delete  (Remove records)

This page lets us do all four on our players table.
"""

import streamlit as st
import sqlite3
import pandas as pd

DB_PATH = "utils/cricBuzz.db"

def get_all_players():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT playerId, playerName, team, playingRole, battingStyle, bowlingStyle FROM crudTable ORDER BY playerId",
        conn
    )
    conn.close()
    return df


def add_player(playerId, playerName, team, playingRole, battingStyle, bowlingStyle):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO crudTable (playerId, playerName, team, playingRole, battingStyle, bowlingStyle)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (playerId, playerName, team, playingRole, battingStyle, bowlingStyle))
    conn.commit()
    conn.close()


def update_player(playerId, playerName, team, playingRole, battingStyle, bowlingStyle):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        UPDATE crudTable
        SET playerName=?, team=?, playingRole=?, battingStyle=?, bowlingStyle=?
        WHERE playerId=?
    """, (playerName, team, playingRole, battingStyle, bowlingStyle, playerId))
    conn.commit()
    conn.close()


def delete_player(playerId):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM crudTable WHERE playerId=?", (playerId,))
    conn.commit()
    conn.close()


def show():
    st.markdown("## 🛠 CRUD Operations")
    st.markdown("""
    **CRUD** = Create, Read, Update, Delete

    These are the four basic operations we do on any database.
    Use the tabs below to try each one!
    """)
    st.markdown("---")

    tab_add, tab_update, tab_delete, tab_view = st.tabs([
        "➕ Add Player",
        "✏️ Edit Player",
        "🗑 Delete Player",
        "📋 View All"
    ])

    # ── TAB 1: ADD ──────────────────────────────────
    with tab_add:
        st.markdown("### ➕ Add a New Player")
        st.markdown("Fill in the details below and click **Add Player**.")

        with st.form("add_form"):
            col1, col2 = st.columns(2)

            with col1:
                new_id = st.number_input("Player ID (unique number)", min_value=1, step=1, value=1234)
                new_playerName = st.text_input("Full playerName")
                new_team = st.text_input("International Team")

            with col2:
                new_role = st.selectbox("Role", [
                    "Batsman", "Bowler",
                    "Batting Allrounder", "Bowling Allrounder",
                    "WK-Batsman"
                ])
                new_bat = st.selectbox("Batting Style", ["Right-hand bat", "Left-hand bat", ""])
                new_bowl = st.text_input("Bowling Style")

            submitted = st.form_submit_button("✅ Add Player", type="primary")

            if submitted:
                if not new_playerName:
                    st.error("playerName is required!")
                else:
                    try:
                        add_player(int(new_id), new_playerName, new_team,
                                   new_role, new_bat, new_bowl)
                        st.success(f"✅ Player **{new_playerName}** added to the database!")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    # ── TAB 2: UPDATE ─────────────────────────────────
    with tab_update:
        st.markdown("### ✏️ Edit an Existing Player")

        players_df = get_all_players()

        if players_df.empty:
            st.info("No players found in database.")
        else:
            options = {
                f"{row['playerName']} (ID: {row['playerId']})": row['playerId']
                for _, row in players_df.iterrows()
            }

            selected_label = st.selectbox("Select player to edit", list(options.keys()))
            selected_id = options[selected_label]

            row = players_df[players_df["playerId"] == selected_id].iloc[0]

            with st.form("edit_form"):
                col1, col2 = st.columns(2)

                with col1:
                    upd_playerName = st.text_input("playerName", value=row["playerName"])
                    upd_role = st.text_input("Role", value=row["playingRole"])
                    upd_team = st.text_input("Team", value=row["team"])

                with col2:
                    upd_bat = st.text_input("Batting Style", value=row["battingStyle"])
                    upd_bowl = st.text_input("Bowling Style", value=row["bowlingStyle"])

                save_btn = st.form_submit_button("💾 Save Changes", type="primary")

                if save_btn:
                    try:
                        update_player(selected_id, upd_playerName, upd_team,
                                      upd_role, upd_bat, upd_bowl)
                        st.success(f"✅ Player **{upd_playerName}** updated!")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    # ── TAB 3: DELETE ─────────────────────────────────
    with tab_delete:
        st.markdown("### 🗑 Delete a Player")
        st.warning("⚠️ This cannot be undone! Be careful.")

        players_df = get_all_players()

        if players_df.empty:
            st.info("No players to delete.")
        else:
            options = {
                f"{row['playerName']} — {row['team']} ({row['playingRole']})": row['playerId']
                for _, row in players_df.iterrows()
            }

            chosen_label = st.selectbox("Select player to delete", list(options.keys()))
            chosen_id = options[chosen_label]

            confirmed = st.checkbox(f"Yes, I want to delete **{chosen_label}**")

            if st.button("🗑 Delete", type="primary", disabled=not confirmed):
                try:
                    delete_player(chosen_id)
                    st.success("✅ Player deleted!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    # ── TAB 4: VIEW ─────────────────────────────────
    with tab_view:
        st.markdown("### 📋 All Players in Database")

        players_df = get_all_players()

        search = st.text_input("🔎 Search by playerName or team")

        if search:
            mask = (
                players_df["playerName"].str.contains(search, case=False, na=False) |
                players_df["team"].str.contains(search, case=False, na=False)
            )
            players_df = players_df[mask]

        st.markdown(f"Showing **{len(players_df)}** players")
        st.dataframe(players_df, use_container_width=True, hide_index=True)