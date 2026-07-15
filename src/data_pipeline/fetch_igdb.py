"""fetch acclaimed pc and ps5 games from the igdb api and save the raw response."""

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
    # sort id asc matters for paging: without a fixed sort order, igdb could return games in a slightly different order each call, which risks us
    # skipping or repeating games as we move the offset forward


def fetch_games():
    token = get_token()
    headers = {
        "Client-ID": IGDB_CLIENT_ID,
        "Authorization": f"Bearer {token}",
    }

    all_games = []
    offset = 0

    # we can't fetch 1,600+ games in one go since igdb caps each request at 500 results, so instead we ask for one page of 500 at a time 
    while True:
        query = build_query(offset)
        print(f"fetching games {offset} to {offset + LIMIT}...")
        response = requests.post(GAMES_URL, headers=headers, data=query)
        # igdb expects a post request with the apicalypse query as the raw body, unlike rawg which used get requests with url parameters
        response.raise_for_status()
        games = response.json()

        if not games:
            break

        all_games.extend(games)
        # add this batch games onto the end of our running list

        if len(games) < LIMIT:
            break

        offset += LIMIT
        time.sleep(SLEEP_SECONDS)

    return all_games

def save_raw_json(games):
    # to have this list as key so my other files can read this file the same way they read rawg_games.json
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"results": games}, f, indent=2)
    print(f"saved raw response to {OUTPUT_PATH}")


if __name__ == "__main__":
    if not IGDB_CLIENT_ID:
        raise SystemExit("IGDB_CLIENT_ID is missing - add it to your .env file")

    games = fetch_games()
    save_raw_json(games)
    print(f"fetched {len(games)} games in total")
