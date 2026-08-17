import csv
import json

INPUT_PATH = "data/raw/rawg_games.json"
OUTPUT_PATH = "data/processed/games.csv"


PLATFORMS_WE_WANT = {"PC", "PlayStation 5"}


def load_raw_games():
    with open(INPUT_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["results"]


def clean_game(game):
    released = game.get("released")
    # .get() returns none instead of crashing if the field is missing used LLM for help
    release_year = released[:4] if released else ""
    metacritic = game.get("metacritic", "")
    if metacritic is None:
        metacritic = ""

    platform_names = [p["platform"]["name"] for p in game.get("platforms", [])]
    our_platforms = [name for name in platform_names if name in PLATFORMS_WE_WANT]

    genre_names = [g["name"] for g in game.get("genres", [])]
    esrb = game.get("esrb_rating")
    esrb_name = esrb["name"] if esrb else "unknown"

    return {
        "slug": game.get("slug", ""),
        "title": game.get("name", "unknown"),
        "release_year": release_year,
        "metacritic": metacritic,
        "platforms": "; ".join(our_platforms),
        "genres": "; ".join(genre_names),
        "esrb_rating": esrb_name,
    }


def save_to_csv(rows):
    fieldnames = ["slug", "title", "release_year", "metacritic", "platforms", "genres", "esrb_rating"]
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    games = load_raw_games()
    rows = [clean_game(game) for game in games]
    save_to_csv(rows)
    print(f"saved {len(rows)} rows to {OUTPUT_PATH}")