"""add a description column to games.csv by calling rawg's detail endpoint per game."""

import csv
import os
import sys
import time
import requests

from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
RAWG_API_KEY = os.getenv("RAWG_API_KEY")

# the list endpoint we used in fetch_rawg.py doesn't include descriptions - those only come back from this per-game detail endpoint
DETAIL_URL = "https://api.rawg.io/api/games/{slug}"
# slug is a placeholder we fill in per game with .format() further down

INPUT_PATH = "data/processed/games.csv"
OUTPUT_PATH = "data/processed/games_enriched.csv"

HEADERS = {
    "User-Agent": "persona-game-recommender-dissertation (University of Birmingham)",
    # rawg asks api users to identify their app in this header
}

# a short pause between requests so we don't hammer the api with 40+ calls in a row
SLEEP_SECONDS = 0.5


def load_games():
    with open(INPUT_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # dictreader turns each row into a dictionary using the header row as keys
        return list(reader)
        # turn the reader into a plain list so we can loop over it more than once used LLM help


def fetch_description(slug):
    url = DETAIL_URL.format(slug=slug)
    # build the full address for this one game by filling in its slug
    response = requests.get(url, params={"key": RAWG_API_KEY}, headers=HEADERS)
    # call rawg's detail endpoint for just this game
    response.raise_for_status()
    # stop with a clear error if rawg sent back a failure instead of data
    data = response.json()
    return data.get("description_raw", "")
    # default to an empty string if this particular game has no description at all


def enrich_games(games):
    enriched = []
    # this list will collect every game once its description has been added used slight LLM help
    for i, game in enumerate(games, start=1):
        # enumerate gives us a running count i alongside each game, starting at 1
        print(f"({i}/{len(games)}) fetching description for {game['title']}")
        # progress message so we can see how far through the 500 games we are
        game["description"] = fetch_description(game["slug"])
        # add a new key to this game's dictionary with its fetched description
        enriched.append(game)
        # add the now-enriched game to our results list
        time.sleep(SLEEP_SECONDS)
        # pause briefly before the next request
    return enriched


def save_to_csv(rows):
    fieldnames = list(rows[0].keys())
    # reuse whatever columns the first row has
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        # newline="" is used here to avoid extra blank lines appearing between rows on windows
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    # this block only runs when the file is executed directly, not when imported
    if not RAWG_API_KEY:
        raise SystemExit("RAWG_API_KEY is missing - add it to your .env file")
        # stop early with a clear message rather than letting a confusing error happen later

    games = load_games()
    # read the cleaned games back in from games.csv
    enriched = enrich_games(games)
    # fetch a description for every game, one api call at a time
    save_to_csv(enriched)
    # write the enriched rows out to games_enriched.csv
    print(f"saved {len(enriched)} rows to {OUTPUT_PATH}")
    # confirm how many rows were saved and where to find them
