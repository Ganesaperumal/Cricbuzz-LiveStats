import os
import time
import requests
import json
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("X_RAPIDAPI_KEY", "YOUR_RAPIDAPI_KEY_HERE") 

BASE_URL = "https://cricbuzz-cricket.p.rapidapi.com/"
BASE_FOLDER = os.path.expanduser("utils/json") 

def fetch_and_save_json(api_url, folder_path, file_name, params=None, overwrite=False):
    """Fetches data from the API and saves it as a JSON file, creating folders if needed."""
    full_url = BASE_URL + api_url
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
    }
    
    # Ensure the target directory exists
    full_folder_path = os.path.join(BASE_FOLDER, folder_path)
    os.makedirs(full_folder_path, exist_ok=True)
    file_path = os.path.join(full_folder_path, file_name)
    
    if not overwrite and os.path.exists(file_path):
        print(f"Skipped! File already exists: {file_name}")
        return
    
    try:
        response = requests.get(full_url, headers=headers, params=params)
        response.raise_for_status() 
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(response.json(), f, indent=4)
        print(f"Success: Saved {file_name} to {full_folder_path}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {file_name}: {e}")

def venues():
    target_folder = "1_venues"
    if input("Do you want to fetch all venues? (y/n): ").lower() == 'y':
        idList = [87, 40, 35, 66, 20, 26, 152]
    else:
        raw_input = input("Enter venue id(s) (e.g., 1, 2, 34): ")
        idList = [x.strip() for x in raw_input.split(',') if x.strip()]
    
    for venue_id in idList:
        api_url = f"venues/v1/{venue_id}"
        filename = f"venue_{venue_id}.json"
        fetch_and_save_json(api_url, target_folder, filename)
        time.sleep(1)

def teams():
    target_folder = "2_teams"
    if input("Do you want to fetch all teams (international & league)? (y/n): ").lower() == 'y':
        typeList = ['international', 'league']
    else:
        raw_type = input("Enter team type(s) separated by comma (e.g., international, league, women): ")
        typeList = [x.strip() for x in raw_type.split(',') if x.strip()]
    
    for team_type in typeList:
        api_url = f"teams/v1/{team_type}"
        filename = f"teams_list_{team_type}.json"
        fetch_and_save_json(api_url, target_folder, filename)
        time.sleep(1)

def players():
    target_folder = "3_players"
    if input("Do you want to fetch all team players? (y/n): ").lower() == 'y':
        idList = ['2'] 
    else:
        raw_id = input("Enter team id(s) separated by comma (e.g., 2, 3, 4): ")
        idList = [x.strip() for x in raw_id.split(',') if x.strip()]
    
    for team_id in idList:
        api_url = f"teams/v1/{team_id}/players"
        filename = f"team_players_{team_id}.json"
        fetch_and_save_json(api_url, target_folder, filename)
        time.sleep(1)

def series_list():
    target_folder = "4_series/lists"
    if input("Do you want to fetch all series list? (y/n): ").lower() == 'y':
        typeList = ['international', 'league']
    else:
        raw_type = input("Enter series type(s) separated by comma: ")
        typeList = [x.strip() for x in raw_type.split(',') if x.strip()]

    if input("Do you want to fetch all years list? (y/n): ").lower() == 'y':
        yearList = ['2024']
    else:
        raw_year = input("Enter year(s) separated by comma (e.g., 2023, 2024): ")
        yearList = [x.strip() for x in raw_year.split(',') if x.strip()]
    
    for s_type in typeList:
       for year in yearList:   
            api_url = f"series/v1/archives/{s_type}"
            querystring = {"year": year}
            filename = f"series_list_{year}_{s_type}.json"
            fetch_and_save_json(api_url, target_folder, filename, params=querystring)
            time.sleep(1)

def series_matches():
    target_folder = "4_series/matches"
    if input("Do you want to fetch all series matches? (y/n): ").lower() == 'y':
        idList = [7607,7175,8071]
    else:
        raw_id = input("Enter series id(s) separated by comma (e.g., 3641, 10201): ")
        idList = [x.strip() for x in raw_id.split(',') if x.strip()]
    
    for series_id in idList:
        api_url = f"series/v1/{series_id}"
        filename = f"series_matches_{series_id}.json"
        fetch_and_save_json(api_url, target_folder, filename)
        time.sleep(1)

def series_venues():    
    target_folder = "4_series/venues"
    if input("Do you want to fetch all series venues? (y/n): ").lower() == 'y':
        idList = [7607,7175,8071]
    else:
        raw_id = input("Enter series id(s) separated by comma (e.g., 6732, 3961): ")
        idList = [x.strip() for x in raw_id.split(',') if x.strip()]
    
    for series_id in idList:
        api_url = f"series/v1/{series_id}/venues"
        filename = f"series_venues_{series_id}.json"
        fetch_and_save_json(api_url, target_folder, filename)
        time.sleep(1)

def matches_list():
    if input("Do you want to fetch recent matches? (y/n): ").lower() == 'y':
        fetch_and_save_json(
            api_url="matches/v1/recent",
            folder_path="5_matches/lists",
            file_name="matches_list_recent.json",
            overwrite=True 
        )

def matches_info():
    target_folder = "5_matches/info"
    if input("Do you want to fetch all matches info? (y/n): ").lower() == 'y':
        idList = [87878]
    else:
        raw_id = input("Enter match id(s) separated by comma (e.g., 41881, 130146): ")
        idList = [x.strip() for x in raw_id.split(',') if x.strip()]
    
    for match_id in idList:
        print(match_id)
        api_url = f"mcenter/v1/{match_id}"
        filename = f"match_info_{match_id}.json"
        fetch_and_save_json(api_url, target_folder, filename)
        time.sleep(1)

def scorecards():
    target_folder = "6_scorecards"
    if input("Do you want to fetch all matches scorecards? (y/n): ").lower() == 'y':
        idList = [91805]
    else:
        raw_id = input("Enter match id(s) separated by comma (e.g., 40381, 85106): ")
        idList = [x.strip() for x in raw_id.split(',') if x.strip()]
    
    for match_id in idList:
        api_url = f"mcenter/v1/{match_id}/hscard"
        filename = f"match_scorecard_{match_id}.json"
        fetch_and_save_json(api_url, target_folder, filename)
        time.sleep(1)

def highest_scores():
    target_folder = "7_records/highest_scores"
    match_type_map = {'1': 'test', '2': 'odi', '3': 't20'}

    if input("Do you want to fetch default highest scores (test, odi, t20)? (y/n): ").lower() == 'y':
        idList = ['1', '2', '3']
    else:
        raw_id = input("Enter match type id(s) (1 for test, 2 for odi, 3 for t20). Press Enter to skip and fetch overall: ")
        if not raw_id.strip():
            idList = [None]
        else:
            idList = [x.strip() for x in raw_id.split(',') if x.strip()]
    
    for match_type_id in idList:
        api_url = "stats/v1/topstats/0"
        querystring = {"statsType": "highestScore"}
        
        if match_type_id is None:
            filename = "stats_highestScore_all.json"
        else:
            if match_type_id not in match_type_map:
                print(f"Skipping invalid match type ID: {match_type_id}")
                continue
            match_type_str = match_type_map[match_type_id]
            querystring["matchType"] = match_type_id
            filename = f"stats_highestScore_{match_type_str}.json"
        
        fetch_and_save_json(api_url, target_folder, filename, params=querystring)
        time.sleep(1)

def stats_batting_records():
    target_folder = "7_records/battings"
    match_type_map = {'1': 'test', '2': 'odi', '3': 't20'}

    if input("Fetch default batting stats (mostRuns, highestScore, highestAvg, highestSr, mostHundreds, mostFifties)? (y/n): ").lower() == 'y':
        stats_types = ['mostRuns', 'highestScore', 'highestAvg', 'highestSr', 'mostHundreds', 'mostFifties']
    else:
        raw_stats = input("Enter stats type(s) separated by comma: ")
        stats_types = [x.strip() for x in raw_stats.split(',') if x.strip()]

    raw_teams = input("Enter team id(s) separated by comma (Press Enter to skip): ")
    team_ids = [None] if not raw_teams.strip() else [x.strip() for x in raw_teams.split(',') if x.strip()]

    raw_years = input("Enter year(s) separated by comma (Press Enter to skip): ")
    years = [None] if not raw_years.strip() else [x.strip() for x in raw_years.split(',') if x.strip()]

    raw_match_types = input("Enter match type id(s) (1=test, 2=odi, 3=t20). Press Enter to skip/overall: ")
    match_types = [None] if not raw_match_types.strip() else [x.strip() for x in raw_match_types.split(',') if x.strip()]

    for stats_type in stats_types:
        for team_id in team_ids:
            for year in years:
                for match_type in match_types:
                    api_url = "stats/v1/topstats/0"
                    querystring = {"statsType": stats_type}
                    filename_parts = [f"stats_{stats_type}"]

                    if team_id:
                        querystring["team"] = team_id
                        filename_parts.append(team_id)
                    if year:
                        querystring["year"] = year
                        filename_parts.append(year)
                    if match_type:
                        if match_type in match_type_map:
                            querystring["matchType"] = match_type
                            filename_parts.append(match_type_map[match_type])
                        else:
                            continue
                    else:
                        filename_parts.append("all")

                    filename = "_".join(filename_parts) + ".json"
                    fetch_and_save_json(api_url, target_folder, filename, params=querystring)
                    time.sleep(1)

def stats_bowling_records():
    target_folder = "7_records/bowling"
    match_type_map = {'1': 'test', '2': 'odi', '3': 't20'}

    if input("Fetch default bowling stats (mostWickets, lowestAvg, bestBowlingInnings, mostFiveWickets, lowestEcon, lowestSr)? (y/n): ").lower() == 'y':
        stats_types = ['mostWickets', 'lowestAvg', 'bestBowlingInnings', 'mostFiveWickets', 'lowestEcon', 'lowestSr']
    else:
        raw_stats = input("Enter stats type(s) separated by comma: ")
        stats_types = [x.strip() for x in raw_stats.split(',') if x.strip()]

    raw_teams = input("Enter team id(s) separated by comma (Press Enter to skip): ")
    team_ids = [None] if not raw_teams.strip() else [x.strip() for x in raw_teams.split(',') if x.strip()]

    raw_years = input("Enter year(s) separated by comma (Press Enter to skip): ")
    years = [None] if not raw_years.strip() else [x.strip() for x in raw_years.split(',') if x.strip()]

    raw_match_types = input("Enter match type id(s) (1=test, 2=odi, 3=t20). Press Enter to skip/overall: ")
    match_types = [None] if not raw_match_types.strip() else [x.strip() for x in raw_match_types.split(',') if x.strip()]

    for stats_type in stats_types:
        for team_id in team_ids:
            for year in years:
                for match_type in match_types:
                    api_url = "stats/v1/topstats/0"
                    querystring = {"statsType": stats_type}
                    filename_parts = [f"stats_{stats_type}"]

                    if team_id:
                        querystring["team"] = team_id
                        filename_parts.append(team_id)
                    if year:
                        querystring["year"] = year
                        filename_parts.append(year)
                    if match_type:
                        if match_type in match_type_map:
                            querystring["matchType"] = match_type
                            filename_parts.append(match_type_map[match_type])
                        else:
                            continue
                    else:
                        filename_parts.append("all")

                    filename = "_".join(filename_parts) + ".json"
                    fetch_and_save_json(api_url, target_folder, filename, params=querystring)
                    time.sleep(1)

def batting_careers():
    target_folder = "8_careers/battings"
    if input("Do you want to fetch default batting careers? (y/n): ").lower() == 'y':
        idList = [14565, ]
    else:
        raw_id = input("Enter player id(s) separated by comma (e.g., 8733, 1413): ")
        idList = [x.strip() for x in raw_id.split(',') if x.strip()]
    
    for player_id in idList:
        api_url = f"stats/v1/player/{player_id}/batting"
        filename = f"player_batting_{player_id}.json"
        fetch_and_save_json(api_url, target_folder, filename)
        time.sleep(1)

def bowling_careers():
    target_folder = "8_careers/bowlings"
    if input("Do you want to fetch default bowling careers? (y/n): ").lower() == 'y':
        idList = [38, 101, 29, 27, 240, 8989]
    else:
        raw_id = input("Enter player id(s) separated by comma (e.g., 8733, 1593): ")
        idList = [x.strip() for x in raw_id.split(',') if x.strip()]
    
    for player_id in idList:
        api_url = f"stats/v1/player/{player_id}/bowling"
        filename = f"player_bowling_{player_id}.json"
        fetch_and_save_json(api_url, target_folder, filename)
        time.sleep(1)

def stats_filter():
    target_folder = "0_utilities"
    if input("Do you want to fetch the stats filter utility? (y/n): ").lower() == 'y':
        api_url = "stats/v1/topstats"
        filename = "stats_filter.json"
        fetch_and_save_json(api_url, target_folder, filename)
        time.sleep(1)
    else:
        print("Skipping stats filter.")

if __name__ == "__main__":
    while True:
        print("\n=== Cricbuzz API Data Fetcher ===")
        print("0. EXIT")
        print("1. Venues (1_venues)")
        print("2. Teams (2_teams)")
        print("3. Players (3_players)")
        print("4. Series List (4_series/list)")
        print("5. Series Matches (4_series/matches)")
        print("6. Series Venues (4_series/venues)")
        print("7. Matches List - Recent (5_matches/list)")
        print("8. Matches Info (5_matches/info)")
        print("9. Scorecards (6_scorecards)")
        print("10. Highest Scores (7_records/highest_scores)")
        print("11. Batting Records (7_records/batting)")
        print("12. Bowling Records (8_records/bowling)")
        print("13. Batting Careers (8_careers/batting)")
        print("14. Bowling Careers (8_careers/bowling)")
        print("15. Stats Filter Utility (0_utilities)")
        
        choice = input("\nEnter your choice (1-16): ").strip()
        
        if choice == '0': 
            print("Exiting. Happy data hunting!")
            break
        elif choice == '1': venues()    
        elif choice == '2': teams()
        elif choice == '3': players()
        elif choice == '4': series_list()
        elif choice == '5': series_matches()
        elif choice == '6': series_venues()
        elif choice == '7': matches_list()
        elif choice == '8': matches_info()
        elif choice == '9': scorecards()
        elif choice == '10': highest_scores()
        elif choice == '11': stats_batting_records()
        elif choice == '12': stats_bowling_records()
        elif choice == '13': batting_careers()
        elif choice == '14': bowling_careers()
        elif choice == '15': stats_filter()
        else:
            print("Invalid choice, please try again.")
