"""fetch acclaimed pc and ps5 games from the rawg api and save the raw response."""

import json
import os
import sys
import time
import requests

from dotenv import load_dotenv


# some game names contain characters (accents, cyrillic, etc) that windows'
# default terminal encoding can't print, so we switch stdout to utf-8 - used help of LLM to fix the error here
sys.stdout.reconfigure(encoding="utf-8")

# rawg needs a key and identification, so both come from .env
load_dotenv()
RAWG_API_KEY = os.getenv("RAWG_API_KEY")

RAWG_URL = "https://api.rawg.io/api/games"
OUTPUT_PATH = "data/raw/rawg_games.json"

# from the rawg docs i got the platform ids : 4 = pc, 187 = playstation 5
PARAMS = {
    "key": RAWG_API_KEY,
    "metacritic": "85,100",
    # my req here was to only return games with a metacritic score in this range
    "platforms": "4,187",
    # only to return games available on pc or ps5
    "ordering": "-metacritic",
    # sorted in descending so it is easier to spot the best
    "page_size": 40,
}

HEADERS = {
    "User-Agent": "persona-game-recommender-dissertation (University of Birmingham)",
}

MAX_GAMES = 500

# a short pause between page requests so we don't hammer the api
SLEEP_SECONDS = 1


def fetch_games():
    all_games = []
    # this list will collect every game we fetch, across all pages
    url = RAWG_URL
    params = PARAMS
    # the filters to send with the request which is only needed on the very first call
    page_number = 1
    # just for the progress to know waht is going on

    # rawg gives back 40 games per page plus a next url for the next page.
    # we follow next until either it runs out or we hit our target count.
    while url and len(all_games) < MAX_GAMES:
        print(f"fetching page {page_number}...")
        response = requests.get(url, params=params, headers=HEADERS)
        response.raise_for_status()
        # stop with a clear error if rawg sent back a failure instead of data
        data = response.json()
        # turn the response text into a python dictionary

        all_games.extend(data["results"])
        # add this page's games onto the end of our running list

        # the next url already has all our filters baked in, so after the first request we stop passing params to avoid sending them twice
        url = data.get("next")
        params = None
        page_number += 1
        # move the counter on for the next loop's progress message

        if url:
            time.sleep(SLEEP_SECONDS)
            # this is to only pause if we're about to make another request

    return all_games[:MAX_GAMES]


def print_games(games):
    for game in games:
        # loop through every game we fetched to print information req
        print(f"{game['name']} - metacritic: {game['metacritic']}")


def save_raw_json(games):
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"results": games}, f, indent=2)
        # write the games out as formatted json so it is readable used LLM for help
    print(f"saved raw response to {OUTPUT_PATH}")


if __name__ == "__main__":
    # this block only runs when the file is executed directly, not when imported
    if not RAWG_API_KEY:
        raise SystemExit("RAWG_API_KEY is missing - add it to your .env file")
        # stop early with a clear message 

    games = fetch_games()
    # run the whole fetch process and get the final list of games back
    print_games(games)
    # show every game and its score in the terminal
    save_raw_json(games)
    # write the raw results to disk
    print(f"fetched {len(games)} games in total")
    # final summary so we know exactly how many games we ended up with
