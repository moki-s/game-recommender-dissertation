"""read the raw igdb json and save a tidy csv with just the fields we need."""

import csv
import json

from datetime import datetime, timezone

INPUT_PATH = "data/raw/igdb_games.json"
OUTPUT_PATH = "data/processed/games_igdb.csv"

PLATFORMS_WE_WANT = {"PC (Microsoft Windows)", "PlayStation 5"}

PEGI_ORGANIZATION_ID = 2

PEGI_RATING_CATEGORIES = {
    8: "3",
    9: "7",
    10: "12",
    11: "16",
    12: "18",
}


def load_raw_games():
    with open(INPUT_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["results"]


def get_release_year(game):
    timestamp = game.get("first_release_date")
    if not timestamp:
        return ""
    release_date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    # convert the timestamp into a real date, treating it as utc
    return str(release_date.year)


def get_platforms(game):
    platform_names = [p["name"] for p in game.get("platforms", [])]
    # pull just the name out of every platform entry
    our_platforms = [name for name in platform_names if name in PLATFORMS_WE_WANT]
    # keep only pc / ps5, dropping any other platforms the game also happens to be on
    return "; ".join(our_platforms)


def get_pegi_rating(game):
    # age_ratings is a list because a game can have ratings from several we only want the pegi one
    for age_rating in game.get("age_ratings", []):
        if age_rating.get("organization") == PEGI_ORGANIZATION_ID:
            category_id = age_rating.get("rating_category")
            return PEGI_RATING_CATEGORIES.get(category_id, "unknown")
    return "unknown"
    # no pegi entry was found in the list at all

#used LLM for debugging code error
def clean_game(game):
    genre_names = [g["name"] for g in game.get("genres", [])]
    theme_names = [t["name"] for t in game.get("themes", [])]
    # themes is often missing entirely for a game, so .get() with a default empty list avoids crashing when we try to loop over it
    mode_names = [m["name"] for m in game.get("game_modes", [])]

    return {
        "title": game.get("name", "unknown"),
        "release_year": get_release_year(game),
        "summary": game.get("summary", ""),
        # some games simply have no summary written on igdb, so we can store it as a blank
        "genres": "; ".join(genre_names),
        "themes": "; ".join(theme_names),
        "game_modes": "; ".join(mode_names),
        "platforms": get_platforms(game),
        "pegi_rating": get_pegi_rating(game),
    }


def save_to_csv(rows):
    fieldnames = [
        "title", "release_year", "summary", "genres",
        "themes", "game_modes", "platforms", "pegi_rating",
    ]
    # the column headers in the order we want them to appear in the csv
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    games = load_raw_games()
    rows = [clean_game(game) for game in games]
    save_to_csv(rows)
    print(f"saved {len(rows)} rows to {OUTPUT_PATH}")
