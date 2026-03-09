# 🏏 Cricbuzz LiveStats
**Real-Time Cricket Insights & SQL Analytics**

Built with Python • Streamlit • SQLite • Cricbuzz RapidAPI

---

## 🚀 Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 📋 Pages

| Page | Description |
|------|-------------|
| 🏠 Home | Dashboard with DB stats and page navigation |
| 📺 Live Matches | Live scores fetched from Cricbuzz API |
| 🏏 Player Stats | Career batting & bowling stats per player |
| 🔍 SQL Analytics | 25 SQL queries — beginner to advanced |
| 🛠 CRUD Operations | Add / update / delete player records |

---

## 4. Configure your API key

Edit `utils/.env` and add your [RapidAPI](https://rapidapi.com/hub) key for the **Cricbuzz Cricket API**:

```
X_RAPIDAPI_KEY="your_api_key_here"
```

Or enter it directly inside the app via **🔧 Developer → API Key tab**.

---

## 🔧 Developer Mode

Click the **🔧 Developer** button at the bottom of the sidebar.

> **Password:** `cricdev2024`

Developer mode gives access to:
- 🔑 API key management (enter, validate, save to .env)
- 📥 Data fetcher (download JSON from Cricbuzz API)
- 🩺 File health dashboard (see which JSON files are present/missing)
- ⚙️ Configure IDs (edit series/match/player IDs saved to config.json)
- 🗄 DB Sync — two modes:
  - **Sync New Data** — append-only, preserves CRUD entries
  - **Full Rebuild** — drops all tables, clean slate ⚠️

---

## 📁 Project Structure

```
cricbuzz_project/
├── app.py                  ← Main entry point
├── requirements.txt
├── README.md
├── pages/
│   ├── home.py
│   ├── live_matches.py
│   ├── player_stats.py
│   ├── sql_queries.py      ← 25 SQL queries
│   ├── crud_operations.py
│   └── developer.py        ← Developer config page
└── utils/
    ├── cricBuzz.db          ← SQLite database (16 tables)
    ├── fetch_engine.py      ← API fetch logic
    ├── db_sync.py           ← JSON → DB sync engine
    ├── config.json          ← Fetch configuration (IDs, params)
    ├── .env                 ← API key (never commit this)
    └── json/                ← Raw API responses
```

---

## 🗄 Database Tables

`teams` • `venues` • `players` • `teamPlayers` • `crudTable` • `series` • `matches` •
`matchBowlings` • `matchBattings` • `matchPartnerships` • `battingCareers` •
`bowlingCareers` • `battingRecords` • `bowlingRecords` • `highestScoreRecords`

---

*GUVI / HCL Capstone Project*
