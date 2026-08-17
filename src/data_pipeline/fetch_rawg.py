import json
import os
import sys
import time
import requests

from dotenv import load_dotenv

# default terminal encoding can't print, so we switch stdout to utf-8 - used help of LLM to fix the error here
sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
RAWG_API_KEY = os.getenv("RAWG_API_KEY")

RAWG_URL = "https://api.rawg.io/api/games"
OUTPUT_PATH = "data/raw/rawg_games.json"

PARAMS = {
    "key": RAWG_API_KEY,
    "metacritic": "85,100",
    "platforms": "4,187",
    "ordering": "-metacritic",
    "page_size": 40,
}

HEADERS = {
    "User-Agent": "persona-game-recommender-dissertation (University of Birmingham)",
}

MAX_GAMES = 500

SLEEP_SECONDS = 1


def fetch_games():
    all_games = []
    url = RAWG_URL
    params = PARAMS
    page_number = 1

    while url and len(all_games) < MAX_GAMES:
        print(f"fetching page {page_number}...")
        response = requests.get(url, params=params, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        all_games.extend(data["results"])

        url = data.get("next")
        params = None
        page_number += 1

        if url:
            time.sleep(SLEEP_SECONDS)

    return all_games[:MAX_GAMES]


def print_games(games):
    for game in games:
        print(f"{game['name']} - metacritic: {game['metacritic']}")


def save_raw_json(games):
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"results": games}, f, indent=2)
    print(f"saved raw response to {OUTPUT_PATH}")


if __name__ == "__main__":
    if not RAWG_API_KEY:
        raise SystemExit("RAWG_API_KEY is missing - add it to your .env file")

    games = fetch_games()
    print_games(games)
    save_raw_json(games)
    print(f"fetched {len(games)} games in total")
