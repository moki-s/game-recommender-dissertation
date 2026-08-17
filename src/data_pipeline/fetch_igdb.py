import json
import os
import sys
import time
import requests

from dotenv import load_dotenv

from igdb_auth import get_token

sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
IGDB_CLIENT_ID = os.getenv("IGDB_CLIENT_ID")

GAMES_URL = "https://api.igdb.com/v4/games"
OUTPUT_PATH = "data/raw/igdb_games.json"

PLATFORM_IDS = "6,167"

MIN_TOTAL_RATING = 85

FIELDS = (
    "name, first_release_date, summary, genres.name, themes.name, "
    "game_modes.name, platforms.name, age_ratings.rating_category, "
    "age_ratings.organization, involved_companies.company.name"
)

LIMIT = 500

SLEEP_SECONDS = 0.3

def build_query(offset):
    
    # used LLM help to understand as igdb uses its own small query language called "apicalypse" instead of normal url parameters

    return (
        f"fields {FIELDS};"
        f"where total_rating >= {MIN_TOTAL_RATING} & platforms = ({PLATFORM_IDS});"
        f"sort id asc;"
        f"limit {LIMIT};"
        f"offset {offset};"
    )


def fetch_games():
    token = get_token()
    headers = {
        "Client-ID": IGDB_CLIENT_ID,
        "Authorization": f"Bearer {token}",
    }

    all_games = []
    offset = 0

    while True:
        query = build_query(offset)
        print(f"fetching games {offset} to {offset + LIMIT}...")
        response = requests.post(GAMES_URL, headers=headers, data=query)
        response.raise_for_status()
        games = response.json()

        if not games:
            break

        all_games.extend(games)

        if len(games) < LIMIT:
            break

        offset += LIMIT
        time.sleep(SLEEP_SECONDS)

    return all_games

def save_raw_json(games):
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"results": games}, f, indent=2)
    print(f"saved raw response to {OUTPUT_PATH}")


if __name__ == "__main__":
    if not IGDB_CLIENT_ID:
        raise SystemExit("IGDB_CLIENT_ID is missing - add it to your .env file")

    games = fetch_games()
    save_raw_json(games)
    print(f"fetched {len(games)} games in total")
