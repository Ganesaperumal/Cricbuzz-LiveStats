# 🏏 Cricbuzz LiveStats — Real-Time Cricket Insights & SQL Analytics

A comprehensive **cricket analytics dashboard** built with Python, Streamlit, SQLite, and the Cricbuzz RapidAPI.  
Fetch live match data, explore player statistics, run 25 SQL queries, and perform full CRUD operations — all from a single web app.

---

## 📸 Features

| Page | Description |
|------|-------------|
| 🏠 **Home** | Project overview, DB stats at a glance |
| 📺 **Live Matches** | Real-time scores from the Cricbuzz API |
| 🏏 **Player Stats** | Search any player, view batting/bowling career stats |
| 🔍 **SQL Analytics** | Run 25 SQL queries (Beginner → Advanced) on the local DB |
| 🛠 **CRUD Operations** | Add / Edit / Delete player records interactively |

---

## 🗂 Project Structure

```
cricbuzz_livestats/
├── app.py                     # Main entry point — run this with Streamlit
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── .gitignore                 # Files excluded from Git
│
├── pages/
│   ├── home.py                # Home / overview page
│   ├── live_matches.py        # Live scores via Cricbuzz API
│   ├── player_stats.py        # Player search & career stats
│   ├── sql_queries.py         # 25 SQL analytical queries
│   └── crud_operations.py     # Create / Read / Update / Delete
│
├── utils/
│   ├── db_connection.py       # Centralised SQLite connection helper
│   ├── cricBuzz.db            # SQLite database (populated by scripts below)
│   ├── .env                   # API keys (do NOT commit this)
│   ├── 0_fileManagement.py    # Utility: manage JSON files
│   ├── 1_fetchJsonAPI.py      # Step 1: Fetch JSON data from Cricbuzz API
│   ├── 2_data2DB.py           # Step 2: Parse JSON and load into SQLite
│   └── 3_cricBuzz_queries.py  # Step 3: Standalone SQL query runner
│
└── utils/json/                # Raw API responses (auto-generated)
    ├── 3_players/
    ├── 4_series/
    ├── 5_matches/
    ├── 6_scorecards/
    ├── 7_records/
    └── 8_careers/
```

---

## ⚙️ Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/cricbuzz-livestats.git
cd cricbuzz-livestats
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API key

Edit `utils/.env` and add your [RapidAPI](https://rapidapi.com/hub) key for the **Cricbuzz Cricket API**:

```
X_RAPIDAPI_KEY="your_api_key_here"
```

> 🔗 Sign up at https://rapidapi.com and subscribe to the **Cricbuzz Cricket** API (free tier available).

### 5. (Optional) Refresh the database

The repo already ships with a populated `cricBuzz.db`.  
To re-fetch fresh data from the API:

```bash
# From the project root
python utils/1_fetchJsonAPI.py   # downloads JSON files
python utils/2_data2DB.py        # parses JSON → SQLite
```

### 6. Launch the app

```bash
streamlit run app.py
```

Then open **http://localhost:8501** in your browser.

---

## 🗄 Database Schema

| Table | Description |
|-------|-------------|
| `teams` | International & domestic teams |
| `players` | Player bio & info |
| `teamPlayers` | Team roster with role/style |
| `venues` | Stadium details (capacity, city, country) |
| `series` | Cricket series list |
| `matches` | Match results with venue, format, winner |
| `matchBattings` | Per-innings batting performance |
| `matchBowlings` | Per-innings bowling performance |
| `matchPartnerships` | Batting partnerships |
| `battingCareers` | Aggregated career batting stats per format |
| `bowlingCareers` | Aggregated career bowling stats per format |
| `highestScoreRecords` | Highest scores per format |
| `crudTable` | Demo table used by the CRUD operations page |

---

## 🧮 SQL Practice Queries (25 Total)

| Level | Questions |
|-------|-----------|
| 🟢 Beginner | Q1–Q8 — SELECT, WHERE, GROUP BY, ORDER BY |
| 🟡 Intermediate | Q9–Q16 — JOINs, subqueries, aggregates |
| 🔴 Advanced | Q17–Q25 — CTEs, window functions, analytics |

All 25 queries are available in the **SQL Analytics** page of the dashboard and can be edited live.

---

## 🛠 Tech Stack

| Technology | Purpose |
|-----------|---------|
| Python 3.10+ | Core language |
| Streamlit | Web dashboard framework |
| SQLite | Local database |
| pandas | Data manipulation |
| requests | HTTP calls to Cricbuzz API |
| python-dotenv | Secure API key loading |

---

## 📋 Requirements

```
streamlit
pandas
requests
python-dotenv
tabulate
```

---

## 🔒 Security Notes

- **Never commit your `.env` file** — it is already listed in `.gitignore`.
- API keys in the source files are demo keys; replace with your own before deployment.

---

## 👨‍💻 Author

Built as part of the **GUVI × HCL Data Science / AIML** capstone project.

---

## 📄 License

This project is for educational purposes only. Cricket data is sourced via the [Cricbuzz Cricket RapidAPI](https://rapidapi.com/cricketapilive/api/cricbuzz-cricket).
