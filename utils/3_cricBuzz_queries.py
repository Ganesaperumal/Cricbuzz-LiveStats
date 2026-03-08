import sqlite3
import pandas as pd
from tabulate import tabulate

conn = sqlite3.connect('utils/cricBuzz.db')

SEP = "-" * 80

def show(title, df):
    print(SEP)
    print(title)
    print(tabulate(df, headers='keys', tablefmt='simple_outline', showindex=False))
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# BEGINNER LEVEL
# ═══════════════════════════════════════════════════════════════════════════════

# Q1 — Find all players who represent India.
# Display full name, playing role, batting style, bowling style.

query = """
SELECT
    UPPER(name)      AS "Full Name",
    role             AS "Playing Role",
    battingStyle     AS "Batting Style",
    bowlingStyle     AS "Bowling Style"
FROM teamPlayers
WHERE teamId = 2
ORDER BY role;
"""
show("Q1: Indian players — role & style", pd.read_sql_query(query, conn))


# Q2 — All matches played in the last few days.
# Match description, both team names, venue with city, match date. Sort by most recent.

query = """
SELECT
    m.matchDesc                              AS "Match Description",
    t1.teamName                              AS "Team 1",
    t2.teamName                              AS "Team 2",
    m.matchVenue || ', ' || m.matchCity      AS "Venue",
    m.matchDate                              AS "Match Date"
FROM matches m
JOIN teams t1
    ON m.firstBatTeamId  = t1.teamId
JOIN teams t2
    ON m.secondBatTeamId = t2.teamId
WHERE LOWER(m.matchState) = 'complete'
  AND m.matchVenue IS NOT NULL
  AND m.matchCity  IS NOT NULL
ORDER BY m.matchDate DESC
LIMIT 15;
"""

show("Q2: Recent completed matches", pd.read_sql_query(query, conn))


# Q3 — Top 10 highest ODI run scorers.
# Player name, total runs, batting average, centuries.

query = """
SELECT
    p.playerName                      AS "Player Name",
    hs.highestScore                   AS "Highest Score",
    bc.battingAvg                     AS "Batting Avg",
    bc.hundreds                       AS "Centuries"
FROM highestScoreRecords hs
JOIN players p
    ON hs.playerId = p.playerId
LEFT JOIN battingCareers bc
    ON hs.playerId   = bc.playerId
    AND bc.matchFormat = 'ODI'
WHERE hs.matchFormat = 'ODI'
ORDER BY hs.highestScore DESC
LIMIT 10;
"""
show("Q3: Top 10 ODI run scorers", pd.read_sql_query(query, conn))


# Q4 — Venues with seating capacity > 25,000. Top 10 by largest capacity.

query = """
SELECT
    venueName     AS "Venue Name",
    venueCity     AS "City",
    venueCountry  AS "Country",
    venueCapacity AS "Capacity"
FROM venues
WHERE venueCapacity > 25000
ORDER BY venueCapacity DESC
LIMIT 10;   
"""
show("Q4: Venues with capacity > 25,000", pd.read_sql_query(query, conn))


# Q5 — Matches won by each team. Team name + total wins, most wins first.

query = """
SELECT
    t.teamName   AS "Team Name",
    COUNT(*)     AS "Total Wins"
FROM matches m
JOIN teams t
    ON m.winningTeamId = t.teamId
WHERE t.teamType = 'International'
GROUP BY m.winningTeamId
ORDER BY "Total Wins" DESC
"""
show("Q5: Match wins by team", pd.read_sql_query(query, conn))


# Q6 — Player count by playing role (Batsman, Bowler, All-Rounder, Wicket-keeper).

query = """
SELECT
    role         AS "Role",
    COUNT(*)     AS "No of Players"
FROM teamPlayers
GROUP BY role
ORDER BY "No of Players" DESC;
"""
show("Q6: Players per playing role", pd.read_sql_query(query, conn))


# Q7 — Highest individual batting score in each format (Test, ODI, T20).

query = """
SELECT
    playerName       AS "Player Name",
    matchFormat      AS "Format",
    highestScore     AS "Highest Score"
FROM (
    SELECT
        p.playerName,
        hs.matchFormat,
        hs.highestScore,
        RANK() OVER (
            PARTITION BY hs.matchFormat
            ORDER BY CAST(REPLACE(hs.highestScore, '*', '') AS INTEGER) DESC
        ) AS rnk
    FROM highestScoreRecords hs
    JOIN players p
        ON hs.playerId = p.playerId
    WHERE hs.matchFormat != 'IPL'
)
WHERE rnk = 1;
"""
show("Q7: Highest score per format", pd.read_sql_query(query, conn))


# Q8 — Cricket series that started in 2024.
# Series name, host country, match type, start date, total matches.

query = """
SELECT
    seriesName           AS "Series Name",
    seriesCountry        AS "Host Country",
    seriesType           AS "Match Type",
    seriesStartDate      AS "Start Date",
    seriesTotalMatches   AS "Total Matches"
FROM series
WHERE strftime('%Y', seriesStartDate) = '2024'
  AND seriesCountry    IS NOT NULL
  AND seriesTotalMatches IS NOT NULL
ORDER BY seriesType;
"""
show("Q8: 2024 cricket series", pd.read_sql_query(query, conn))


# ═══════════════════════════════════════════════════════════════════════════════
# INTERMEDIATE LEVEL
# ═══════════════════════════════════════════════════════════════════════════════

# Q9 — All-rounders with > 1000 runs AND > 50 wickets in career.
# Player name, total runs, total wickets, format.

query = """
SELECT
    p.playerName       AS "Player Name",
    bc.totalRuns       AS "Total Runs",
    bwc.wickets        AS "Total Wickets",
    bc.matchFormat     AS "Cricket Format"
FROM battingCareers bc
JOIN bowlingCareers bwc
    ON  bc.playerId    = bwc.playerId
    AND bc.matchFormat = bwc.matchFormat
JOIN players p
    ON bc.playerId = p.playerId
WHERE bc.totalRuns  > 1000
  AND bwc.wickets   > 50
  AND bc.matchFormat != 'IPL'
ORDER BY bc.matchFormat DESC
LIMIT 10;   
"""
show("Q9: All-rounders (1000+ runs & 50+ wickets)", pd.read_sql_query(query, conn))


# Q10 — Last 20 completed matches.
# Match description, both teams, winning team, victory margin, victory type, venue.

query = """
SELECT
    m.matchDesc                          AS "Match Description",
    t1.teamSName                         AS "Team 1",
    t2.teamSName                         AS "Team 2",
    CASE
        WHEN m.winningTeamId = t1.teamId THEN t1.teamSName
        WHEN m.winningTeamId = t2.teamId THEN t2.teamSName
        ELSE 'No Result'
    END                                  AS "Winner",
    m.winningMargin                      AS "Victory Margin",
    m.winningType                        AS "Victory Type",
    m.matchVenue || ', ' || m.matchCity  AS "Venue"
FROM matches m
JOIN teams t1
    ON m.firstBatTeamId  = t1.teamId
JOIN teams t2
    ON m.secondBatTeamId = t2.teamId
WHERE LOWER(m.matchState) = 'complete'
  AND m.matchVenue IS NOT NULL
ORDER BY m.matchDate DESC
LIMIT 20;
"""
show("Q10: Last 20 completed matches", pd.read_sql_query(query, conn))


# Q11 — Player performance across formats.
# Players in >= 2 formats: Test runs, ODI runs, T20 runs, overall batting avg.

query = """
SELECT
    p.playerName                                                       AS "Player Name",
    MAX(CASE WHEN bc.matchFormat = 'TEST' THEN bc.totalRuns END)      AS "Test Runs",
    MAX(CASE WHEN bc.matchFormat = 'ODI'  THEN bc.totalRuns END)      AS "ODI Runs",
    MAX(CASE WHEN bc.matchFormat = 'T20'  THEN bc.totalRuns END)      AS "T20 Runs",
    ROUND(AVG(bc.battingAvg), 2)                                      AS "Overall Batting Avg"
FROM battingCareers bc
JOIN players p
    ON bc.playerId = p.playerId
GROUP BY bc.playerId, p.playerName
HAVING COUNT(DISTINCT bc.matchFormat) >= 2
ORDER BY "ODI Runs" DESC NULLS LAST
LIMIT 10;
"""
show("Q11: Player performance across formats", pd.read_sql_query(query, conn))


# Q12 — Home vs Away wins per team.
# Compare venue country with team name (proxy for home).

query = """
SELECT
    t.teamName                                                           AS "Team",
    SUM(CASE WHEN v.venueCountry = t.teamName THEN 1 ELSE 0 END)       AS "Home Wins",
    SUM(CASE WHEN v.venueCountry != t.teamName
              AND v.venueCountry IS NOT NULL THEN 1 ELSE 0 END)         AS "Away Wins"
FROM matches m
JOIN teams t
    ON m.winningTeamId = t.teamId
LEFT JOIN venues v
    ON m.venueId = v.venueId
WHERE m.winningTeamId IS NOT NULL 
  AND t.teamType = 'International'
GROUP BY t.teamId, t.teamName
HAVING (
    SUM(CASE WHEN v.venueCountry = t.teamName THEN 1 ELSE 0 END) +
    SUM(CASE WHEN v.venueCountry != t.teamName AND v.venueCountry IS NOT NULL THEN 1 ELSE 0 END)
) > 0
ORDER BY "Home Wins" DESC
"""
show("Q12: Home vs Away wins by team", pd.read_sql_query(query, conn))


# Q13 — Batting partnerships >= 100 runs in same innings.
# Both player names, partnership runs, innings.

query = """
SELECT
    p1.playerName     AS "Player 1",
    p2.playerName     AS "Player 2",
    mp.partnershipRuns AS "Partnership Runs",
    mp.innings        AS "Innings"
FROM matchPartnerships mp
JOIN players p1
    ON mp.batsman1Id = p1.playerId
JOIN players p2
    ON mp.batsman2Id = p2.playerId
WHERE mp.partnershipRuns >= 100
ORDER BY mp.partnershipRuns DESC
LIMIT 10;
"""
show("Q13: Partnerships ≥ 100 runs", pd.read_sql_query(query, conn))


# Q14 — Bowling at venues: >= 3 matches, >= 4 overs per match.
# Avg economy, total wickets, matches per venue.

query = """
SELECT
    p.playerName               AS "Bowler Name",
    mb.venue                   AS "Venue",
    COUNT(DISTINCT mb.matchId) AS "Matches",
    ROUND(AVG(mb.economy), 1)  AS "Avg Economy",
    SUM(mb.wickets)            AS "Total Wickets"
FROM matchBowlings mb
JOIN players p
    ON mb.playerId = p.playerId
WHERE mb.overs >= 4
  AND mb.venue IS NOT NULL
GROUP BY mb.playerId, p.playerName, mb.venue
HAVING COUNT(DISTINCT mb.matchId) >= 3
ORDER BY p.playerName
LIMIT 12;
"""
show("Q14: Bowling performance by venue", pd.read_sql_query(query, conn))


# Q15 — Players performing well in close matches.
# Close match: < 50 runs OR < 5 wickets margin.
# Avg runs, total close matches played, wins when they batted.

query = """
SELECT
    p.playerName                   AS "Player",
    ROUND(AVG(mb.runs), 2)         AS "Avg Runs",
    COUNT(DISTINCT mb.matchId)     AS "Close Matches Played",
    SUM(
        CASE
            WHEN mb.innings = 1 AND m.winningTeamId = m.firstBatTeamId  THEN 1
            WHEN mb.innings = 2 AND m.winningTeamId = m.secondBatTeamId THEN 1
            ELSE 0
        END
    )                              AS "Wins When Batted"
FROM matchBattings mb
JOIN matches m
    ON mb.matchId = m.matchId
JOIN players p
    ON mb.playerId = p.playerId
WHERE (
        (m.winningType = 'runs' AND m.winningMargin < 50)
     OR (m.winningType = 'wkts' AND m.winningMargin < 5)
)
GROUP BY mb.playerId, p.playerName
ORDER BY "Close Matches Played" DESC
LIMIT 10;
"""
show("Q15: Player performance in close matches", pd.read_sql_query(query, conn))

# Q16 — Batting performance by year since 2020.
# Avg runs & strike rate per year, players with >= 5 matches that year.

query = """
WITH FilteredBatting AS (
    -- Step 1: Get the base records since 2020 with 5+ matches
    SELECT *
    FROM battingRecords
    WHERE year >= 2020
      AND totalMatches >= 5
      -- AND matchFormat = 'ODI' -- Uncomment if you only want ODIs
),
FrequentPlayers AS (
    -- Step 2: Find playerIds that appear more than 3 times
    SELECT playerId
    FROM FilteredBatting
    GROUP BY playerId
    HAVING COUNT(*) > 3
)
-- Step 3: Join everything together for the final output
SELECT
    p.playerName                            AS "Player Name",
    b.year                                  AS "Year",
    ROUND(b.runs * 1.0 / b.totalMatches, 2) AS "Avg Runs",
    b.strikeRate                            AS "Avg Strike Rate",
    b.totalMatches                          AS "Matches"
FROM FilteredBatting b
JOIN FrequentPlayers fp
    ON b.playerId = fp.playerId
JOIN players p
    ON b.playerId = p.playerId
ORDER BY p.playerName, b.year ASC
LIMIT 18;
"""
show("Q16: Yearly batting performance (Frequent Players)", pd.read_sql_query(query, conn))


# ═══════════════════════════════════════════════════════════════════════════════
# ADVANCED LEVEL
# ═══════════════════════════════════════════════════════════════════════════════

# Q17 — Toss advantage: % of matches won by toss winner, by toss decision.

query = """
SELECT
    t.teamName                                                               AS "Team",
    m.tossSelection                                                          AS "Toss Decision",
    COUNT(*)                                                                 AS "Total Matches",
    SUM(CASE WHEN m.winningTeamId = m.tossWinTeamId THEN 1 ELSE 0 END)     AS "Wins After Toss",
    ROUND(
        SUM(CASE WHEN m.winningTeamId = m.tossWinTeamId THEN 1.0 ELSE 0 END)
        * 100.0 / COUNT(*),
    2)                                                                       AS "Win %"
FROM matches m
JOIN teams t
    ON m.tossWinTeamId = t.teamId
WHERE m.tossWinTeamId IS NOT NULL
  AND m.tossSelection  IS NOT NULL
  AND t.teamType = 'International'
GROUP BY t.teamName, m.tossSelection
ORDER BY t.teamName, m.tossSelection;
"""
show("Q17: Toss advantage analysis", pd.read_sql_query(query, conn))


# Q18 — Most economical bowlers in ODI & T20.
# >= 10 matches, avg >= 2 overs per match.

query = """
SELECT
    p.playerName               AS "Bowler Name",
    COUNT(DISTINCT mb.matchId) AS "Matches",
    SUM(mb.wickets)            AS "Total Wickets",
    ROUND(AVG(mb.economy), 2)  AS "Avg Economy"
FROM matchBowlings mb
JOIN players p
    ON mb.playerId = p.playerId
JOIN matches m
    ON mb.matchId = m.matchId
WHERE m.matchFormat IN ('ODI', 'T20')
GROUP BY mb.playerId, p.playerName
HAVING COUNT(DISTINCT mb.matchId) >= 10
   AND AVG(mb.overs) >= 2
ORDER BY "Avg Economy"
LIMIT 10;
"""
show("Q18: Most economical bowlers (ODI & T20)", pd.read_sql_query(query, conn))


# Q19 — Most consistent batsmen.
# >= 10 balls per innings (overs >= 1.4), played since 2022.
# Lower std deviation = more consistent.

query = """
SELECT
    p.playerName                                          AS "Batsman Name",
    COUNT(DISTINCT mb.matchId)                            AS "Innings",
    ROUND(AVG(mb.runs), 2)                               AS "Avg Runs",
    ROUND(
        SQRT(AVG(mb.runs * mb.runs) - AVG(mb.runs) * AVG(mb.runs)),
    2)                                                    AS "Std Deviation"
FROM matchBattings mb
JOIN players p
    ON mb.playerId = p.playerId
WHERE mb.overs    >= 1.4
  AND mb.matchDate >= '2022-01-01'
GROUP BY mb.playerId, p.playerName
HAVING COUNT(DISTINCT mb.matchId) >= 4
ORDER BY "Std Deviation"
LIMIT 15;
"""

show("Q19: Most consistent batsmen since 2022", pd.read_sql_query(query, conn))


# Q20 — Matches & batting avg by format per player.
# Only players with >= 20 total matches across all formats.

query = """
SELECT
    p.playerName                     AS "Player Name",
    SUM(bc.totalMatches)             AS "Total Matches",
    SUM(CASE WHEN bc.matchFormat = 'TEST' THEN bc.totalMatches ELSE 0 END)      AS "Test Matches",
    ROUND(MAX(CASE WHEN bc.matchFormat = 'TEST' THEN bc.battingAvg END), 2)     AS "Test Avg",
    SUM(CASE WHEN bc.matchFormat = 'ODI'  THEN bc.totalMatches ELSE 0 END)      AS "ODI Matches",
    ROUND(MAX(CASE WHEN bc.matchFormat = 'ODI'  THEN bc.battingAvg END), 2)     AS "ODI Avg",
    SUM(CASE WHEN bc.matchFormat = 'T20'  THEN bc.totalMatches ELSE 0 END)      AS "T20 Matches",
    ROUND(MAX(CASE WHEN bc.matchFormat = 'T20'  THEN bc.battingAvg END), 2)     AS "T20 Avg"
FROM battingCareers bc
LEFT JOIN players p
    ON bc.playerId = p.playerId
WHERE bc.matchFormat IN ('TEST', 'ODI', 'T20')
AND p.playerName IS NOT NULL
GROUP BY bc.playerId, p.playerName
HAVING SUM(bc.totalMatches) >= 20
ORDER BY "Total Matches" DESC
LIMIT 10;
"""

show("Q20: Matches & avg by format (20+ total matches)", pd.read_sql_query(query, conn))

# Q21 — Comprehensive performance ranking.
# Batting: (runs×0.01) + (avg×0.5) + (sr×0.3)
# Bowling: (wkts×2) + ((50-bowlingAvg)×0.5) + ((6-economy)×2)

query = """
WITH scores AS (
    SELECT
        p.playerName,

        -- Batting scores per format
        ROUND(MAX(CASE WHEN bc.matchFormat = 'ODI'
            THEN bc.totalRuns * 0.01 + bc.battingAvg * 0.5 + bc.strikeRate * 0.3 END), 2) AS bat_odi,
        ROUND(MAX(CASE WHEN bc.matchFormat = 'TEST'
            THEN bc.totalRuns * 0.01 + bc.battingAvg * 0.5 + bc.strikeRate * 0.3 END), 2) AS bat_test,
        ROUND(MAX(CASE WHEN bc.matchFormat = 'T20'
            THEN bc.totalRuns * 0.01 + bc.battingAvg * 0.5 + bc.strikeRate * 0.3 END), 2) AS bat_t20,

        -- Bowling scores per format
        ROUND(MAX(CASE WHEN bwc.matchFormat = 'ODI'
            THEN bwc.wickets * 2 + (50 - bwc.bowlingAvg) * 0.5 + (6 - bwc.economy) * 2 END), 2) AS bowl_odi,
        ROUND(MAX(CASE WHEN bwc.matchFormat = 'TEST'
            THEN bwc.wickets * 2 + (50 - bwc.bowlingAvg) * 0.5 + (6 - bwc.economy) * 2 END), 2) AS bowl_test,
        ROUND(MAX(CASE WHEN bwc.matchFormat = 'T20'
            THEN bwc.wickets * 2 + (50 - bwc.bowlingAvg) * 0.5 + (6 - bwc.economy) * 2 END), 2) AS bowl_t20

    FROM players p
    LEFT JOIN battingCareers bc
        ON p.playerId = bc.playerId AND bc.matchFormat IN ('ODI','TEST','T20')
    LEFT JOIN bowlingCareers bwc
        ON p.playerId = bwc.playerId AND bwc.matchFormat IN ('ODI','TEST','T20')
    GROUP BY p.playerId, p.playerName
),
combined AS (
    SELECT
        playerName,
        ROUND(COALESCE(bat_odi,  0) + COALESCE(bowl_odi,  0), 2) AS "ODI Score",
        ROUND(COALESCE(bat_test, 0) + COALESCE(bowl_test, 0), 2) AS "Test Score",
        ROUND(COALESCE(bat_t20,  0) + COALESCE(bowl_t20,  0), 2) AS "T20 Score"
    FROM scores
    WHERE bat_odi IS NOT NULL OR bat_test IS NOT NULL OR bat_t20 IS NOT NULL
)
SELECT
    RANK() OVER (ORDER BY "ODI Score" + "Test Score" + "T20 Score" DESC) AS "Overall Rank",
    playerName                                                             AS "Player Name",
    "ODI Score",
    RANK() OVER (ORDER BY "ODI Score"  DESC) AS "ODI Rank",
    "Test Score",
    RANK() OVER (ORDER BY "Test Score" DESC) AS "TEST Rank",
    "T20 Score",
    RANK() OVER (ORDER BY "T20 Score"  DESC) AS "T20 Rank"
FROM combined
ORDER BY "Overall Rank"
LIMIT 15;
"""

show("Q21: Comprehensive player performance ranking", pd.read_sql_query(query, conn))


# Q22 — Head-to-head analysis between teams (>= 5 matches in last 3 years).

query = """
WITH pairs AS (
    SELECT
        matchId,
        CASE WHEN firstBatTeamId < secondBatTeamId
             THEN firstBatTeamId ELSE secondBatTeamId END AS teamA,
        CASE WHEN firstBatTeamId < secondBatTeamId
             THEN secondBatTeamId ELSE firstBatTeamId END AS teamB,
        firstBatTeamId,
        secondBatTeamId,
        winningTeamId,
        winningMargin
    FROM matches
    WHERE matchState = 'complete'
      AND matchDate >= date('now', '-3 years')
)
SELECT
    t1.teamName                                                       AS "Team A",
    t2.teamName                                                       AS "Team B",
    COUNT(*)                                                          AS "Total Matches",
    SUM(CASE WHEN winningTeamId = teamA THEN 1 ELSE 0 END)           AS "Team A Wins",
    SUM(CASE WHEN winningTeamId = teamB THEN 1 ELSE 0 END)           AS "Team B Wins",
    ROUND(SUM(CASE WHEN winningTeamId = teamA THEN 1.0 ELSE 0 END)
          * 100.0 / COUNT(*), 2)                                     AS "Team A Win %",
    ROUND(SUM(CASE WHEN winningTeamId = teamB THEN 1.0 ELSE 0 END)
          * 100.0 / COUNT(*), 2)                                     AS "Team B Win %",
    ROUND(AVG(CASE WHEN winningTeamId = teamA THEN winningMargin END), 2) AS "Team A Avg Margin",
    ROUND(AVG(CASE WHEN winningTeamId = teamB THEN winningMargin END), 2) AS "Team B Avg Margin",
    SUM(CASE WHEN firstBatTeamId  = winningTeamId THEN 1 ELSE 0 END) AS "Bat First Wins",
    SUM(CASE WHEN secondBatTeamId = winningTeamId THEN 1 ELSE 0 END) AS "Bowl First Wins"
FROM pairs h
JOIN teams t1 ON h.teamA = t1.teamId
JOIN teams t2 ON h.teamB = t2.teamId
WHERE t1.teamType = 'International' 
  AND t2.teamType = 'International'
GROUP BY teamA, teamB
HAVING COUNT(*) >= 5
ORDER BY "Total Matches" DESC
LIMIT 10;
"""
show("Q22: Head-to-head team analysis (last 3 years, 5+ matches)", pd.read_sql_query(query, conn))


# Q23 — Recent player form (last 10 batting performances).
# Last 5 vs last 10 avg, SR trend, 50s, consistency score, form category.

query = """
WITH ranked AS (
    SELECT
        mb.playerId,
        p.playerName,
        mb.matchId,
        mb.runs,
        mb.strikeRate,
        ROW_NUMBER() OVER (
            PARTITION BY mb.playerId
            ORDER BY mb.matchDate DESC, mb.matchId DESC
        ) AS rn
    FROM matchBattings mb
    JOIN players p
        ON mb.playerId = p.playerId
),
recent10 AS (
    SELECT * FROM ranked WHERE rn <= 10
),
stats AS (
    SELECT
        playerId,
        playerName,
        ROUND(AVG(runs), 2)                                      AS avg10,
        ROUND(AVG(CASE WHEN rn <= 5 THEN runs END), 2)          AS avg5,
        ROUND(AVG(strikeRate), 2)                                AS sr_trend,
        SUM(CASE WHEN runs >= 50 THEN 1 ELSE 0 END)             AS fifties,
        ROUND(SQRT(AVG(runs * runs) - AVG(runs) * AVG(runs)), 2) AS consistency_score
    FROM recent10
    GROUP BY playerId, playerName
)
SELECT
    playerName               AS "Player",
    avg5                     AS "Last 5 Avg",
    avg10                    AS "Last 10 Avg",
    sr_trend                 AS "SR Trend",
    fifties                  AS "50s",
    consistency_score        AS "Consistency Score",
    CASE
        WHEN avg5 > avg10 AND fifties >= 3 AND consistency_score < 20 THEN 'Excellent Form'
        WHEN avg5 > avg10 AND fifties >= 2                            THEN 'Good Form'
        WHEN avg5 >= avg10 * 0.8                                     THEN 'Average Form'
        ELSE 'Poor Form'
    END                      AS "Form Category"
FROM stats
WHERE fifties > 1
ORDER BY fifties DESC
LIMIT 15;
"""
show("Q23: Recent player form & momentum", pd.read_sql_query(query, conn))


# Q24 — Best batting partnerships (>= 5 together).
# Avg runs, partnerships > 50, highest, success rate, ranked.

query = """
WITH pair_stats AS (
    SELECT
        mp.batsman1Id,
        mp.batsman2Id,
        p1.playerName AS player1,
        p2.playerName AS player2,
        COUNT(*)      AS partnerships,
        ROUND(AVG(mp.partnershipRuns), 2) AS avg_runs,
        SUM(CASE WHEN mp.partnershipRuns >= 50 THEN 1 ELSE 0 END) AS over_50,
        MAX(mp.partnershipRuns) AS highest
    FROM matchPartnerships mp
    JOIN players p1 ON mp.batsman1Id = p1.playerId
    JOIN players p2 ON mp.batsman2Id = p2.playerId
    GROUP BY mp.batsman1Id, mp.batsman2Id, p1.playerName, p2.playerName
    HAVING COUNT(*) >= 5
)
SELECT
    player1 || ' & ' || player2         AS "Batting Pair",
    partnerships                         AS "Partnerships",
    avg_runs                             AS "Avg Partnership Runs",
    over_50                              AS "Partnerships > 50",
    highest                              AS "Highest Partnership",
    ROUND(over_50 * 100.0 / partnerships, 2) AS "Success Rate %",
    RANK() OVER (ORDER BY avg_runs DESC) AS "Rank"
FROM pair_stats
ORDER BY avg_runs DESC
LIMIT 10;
"""
show("Q24: Best batting partnerships (5+ together)", pd.read_sql_query(query, conn))


# Q25 — Time-series analysis of player performance evolution.
# Quarterly averages, quarter-on-quarter trend, career phase.
# Players with >= 6 quarters AND >= 3 matches per quarter.

query = """
-- Step 1: Calculate averages per player per quarter
WITH quarterly_avg AS (
    SELECT
        playerId,
        quarter,
        ROUND(AVG(runs), 2)       AS avg_runs,
        ROUND(AVG(strikeRate), 2) AS avg_sr,
        COUNT(DISTINCT matchId)   AS match_count
    FROM matchBattings
    WHERE quarter IS NOT NULL
    GROUP BY playerId, quarter
),

-- Step 2: Filter eligible players (>=6 quarters, min 3 matches in each)
eligible AS (
    SELECT playerId
    FROM quarterly_avg
    GROUP BY playerId
    HAVING COUNT(DISTINCT quarter) >= 6
       AND MIN(match_count) >= 3
),

-- Step 3: Dynamically rank the quarters chronologically (1 = oldest, 6 = newest)
ranked_quarters AS (
    SELECT
        playerId,
        avg_runs,
        avg_sr,
        -- ORDER BY DESC means rn=1 is the newest. We will reverse this in the pivot.
        ROW_NUMBER() OVER (PARTITION BY playerId ORDER BY quarter DESC) as rn
    FROM quarterly_avg
    WHERE playerId IN (SELECT playerId FROM eligible)
),

-- Step 4: Pivot the latest 6 quarters into generic columns (Q1 to Q6)
pivoted AS (
    SELECT
        playerId,
        MAX(CASE WHEN rn = 6 THEN avg_runs END) AS runs_q1,
        MAX(CASE WHEN rn = 6 THEN avg_sr END)   AS sr_q1,
        
        MAX(CASE WHEN rn = 5 THEN avg_runs END) AS runs_q2,
        MAX(CASE WHEN rn = 5 THEN avg_sr END)   AS sr_q2,
        
        MAX(CASE WHEN rn = 4 THEN avg_runs END) AS runs_q3,
        MAX(CASE WHEN rn = 4 THEN avg_sr END)   AS sr_q3,
        
        MAX(CASE WHEN rn = 3 THEN avg_runs END) AS runs_q4,
        MAX(CASE WHEN rn = 3 THEN avg_sr END)   AS sr_q4,
        
        MAX(CASE WHEN rn = 2 THEN avg_runs END) AS runs_q5,
        MAX(CASE WHEN rn = 2 THEN avg_sr END)   AS sr_q5,
        
        MAX(CASE WHEN rn = 1 THEN avg_runs END) AS runs_q6,
        MAX(CASE WHEN rn = 1 THEN avg_sr END)   AS sr_q6
    FROM ranked_quarters
    WHERE rn <= 6 -- Only take the 6 most recent quarters
    GROUP BY playerId
)

-- Step 5: Final wide output with Performance arrows
SELECT
    pl.playerName AS "Player Name",

    p.runs_q1 AS "Avg Runs-Q1",
    p.sr_q1   AS "Strike Rate-Q1",

    CASE WHEN p.runs_q2 > p.runs_q1 THEN 'Improving'
         WHEN p.runs_q2 < p.runs_q1 THEN 'Declining'
         ELSE 'Stable' END AS "Performance Q1->Q2",

    p.runs_q2 AS "AVG-Q2",
    p.sr_q2   AS "SR-Q2",

    CASE WHEN p.runs_q3 > p.runs_q2 THEN 'Improving'
         WHEN p.runs_q3 < p.runs_q2 THEN 'Declining'
         ELSE 'Stable' END AS "PERF Q2->Q3",

    p.runs_q3 AS "AVG-Q3",
    p.sr_q3   AS "SR-Q3",

    CASE WHEN p.runs_q4 > p.runs_q3 THEN 'Improving'
         WHEN p.runs_q4 < p.runs_q3 THEN 'Declining'
         ELSE 'Stable' END AS "PERF Q3->Q4",

    p.runs_q4 AS "AVG-Q4",
    p.sr_q4   AS "SR-Q4",

    CASE WHEN p.runs_q5 > p.runs_q4 THEN 'Improving'
         WHEN p.runs_q5 < p.runs_q4 THEN 'Declining'
         ELSE 'Stable' END AS "PERF Q4->Q5",

    p.runs_q5 AS "AVG-Q5",
    p.sr_q5   AS "SR-Q5",

    CASE WHEN p.runs_q6 > p.runs_q5 THEN 'Improving'
         WHEN p.runs_q6 < p.runs_q5 THEN 'Declining'
         ELSE 'Stable' END AS "PERF Q5->Q6",

    p.runs_q6 AS "AVG-Q6",
    p.sr_q6   AS "SR-Q6",

    CASE WHEN p.runs_q6 > p.runs_q1 THEN 'Career Ascending'
         WHEN p.runs_q6 < p.runs_q1 THEN 'Career Declining'
         ELSE 'Career Stable' END AS "Career Phase"

FROM pivoted p
JOIN players pl ON p.playerId = pl.playerId
ORDER BY p.playerId;
"""
show("Q25: Player performance time-series (quarterly)", pd.read_sql_query(query, conn))

conn.close()
print(SEP)
print("All 25 queries complete.")
print(SEP)
