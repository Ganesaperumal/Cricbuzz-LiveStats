import shutil
import os
import glob
import json

# 1. Define your source and destination paths
source_file = '/path/to/source/folder/filename.ext'
destination_folder = '/path/to/destination/folder/'

def copy_my_file(src, dest):
    try:
        if os.path.exists(dest+src.split("/")[-1]):
            print(f"Exist: The file '{src.split("_")[-1]}' already exist.")
            return
        if not os.path.exists(src):
            print(f"Error: The source file '{src}' does not exist.")
            return
        shutil.copy2(src, dest)
        print(f"Success! File successfully copied to '{dest+src.split("_")[-1]}'")

    except PermissionError:
        print("Error: You don't have permission to write to the destination folder.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def SeriesMatchesFiles():
    idList = [9638,8402,10587,10102,9237,8393,11253,9325,9596,8404]
    for seriesId in idList:
        source_file = f"utils/json/0_filters/loaded/4_series/matches/series_matches_{seriesId}.json"
        destination_folder = "utils/json/4_series/matches/"
        copy_my_file(source_file, destination_folder)

def quarterAnalysisMatchesFiles():
    idList = [100337,100348,100366,100290,100292,100301,115059,115095,118853,130129,130146,130168,117413,117416,117440,138974,139129,139478]
    for matchId in idList:
        source_file = f"utils/json/0_filters/loaded/6_scorecards/match_scorecard_{matchId}.json"
        destination_folder = "utils/json/6_scorecards/"
        copy_my_file(source_file, destination_folder)

def get_scorecard_urls():
    extracted_urls = []
    
    # Path to your scorecard JSON files
    file_pattern = 'utils/json/6_scorecards/*.json'
    
    for json_file in glob.glob(file_pattern):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Safely grab the weburl from within appindex
            appindex = data.get('appindex', {})
            weburl = appindex.get('weburl')
            
            if weburl:
                extracted_urls.append(weburl)
                
        except json.JSONDecodeError:
            print(f"Skipping {json_file}: Invalid JSON format.")
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            
    print(f"Successfully extracted {len(extracted_urls)} URLs.")
    
    # Print the first few URLs as a quick sanity check
    print("\nSample URLs:")
    for url in extracted_urls:
        print(f" - {url}")

def main():
    # SeriesMatchesFiles()
    # quarterAnalysisMatchesFiles()
    get_scorecard_urls()
    exit()


if __name__ == "__main__":
    main()






