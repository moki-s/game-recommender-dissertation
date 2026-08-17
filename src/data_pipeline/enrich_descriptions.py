import csv
import os
import sys
import time
import requests

from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
RAWG_API_KEY = os.getenv("RAWG_API_KEY")

DETAIL_URL = "https://api.rawg.io/api/games/{slug}"

INPUT_PATH = "data/processed/games.csv"
OUTPUT_PATH = "data/processed/games_enriched.csv"

HEADERS = {
    "User-Agent": "persona-game-recommender-dissertation (University of Birmingham)",
}

SLEEP_SECONDS = 0.5


def load_games():
    with open(INPUT_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)
        # turn the reader into a plain list so we can loop over it more than once used LLM help


def fetch_description(slug):
    url = DETAIL_URL.format(slug=slug)
    response = requests.get(url, params={"key": RAWG_API_KEY}, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    return data.get("description_raw", "")


def enrich_games(games):
    enriched = []
    # this list will collect every game once its description has been added used slight LLM help
    for i, game in enumerate(games, start=1):
        print(f"({i}/{len(games)}) fetching description for {game['title']}")
        game["description"] = fetch_description(game["slug"])
        enriched.append(game)
        time.sleep(SLEEP_SECONDS)
    return enriched


def save_to_csv(rows):
    fieldnames = list(rows[0].keys())
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    if not RAWG_API_KEY:
        raise SystemExit("RAWG_API_KEY is missing - add it to your .env file")

    games = load_games()
    enriched = enrich_games(games)
    save_to_csv(enriched)
    print(f"saved {len(enriched)} rows to {OUTPUT_PATH}")
