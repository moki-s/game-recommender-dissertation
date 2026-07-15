"""read the raw rawg json and save a tidy csv with just the fields we need."""

import csv
import json

INPUT_PATH = "data/raw/rawg_games.json"
# the raw file we read from
OUTPUT_PATH = "data/processed/games.csv"
# the file we write to


PLATFORMS_WE_WANT = {"PC", "PlayStation 5"}


def load_raw_games():
    with open(INPUT_PATH, encoding="utf-8") as f:
        data = json.load(f)
        # turn the file text into a python dictionary we can work with
    return data["results"]
    # the actual list of games is stored under the results key


def clean_game(game):
    released = game.get("released")
    # .get() returns none instead of crashing if the field is missing used LLM for help
    release_year = released[:4] if released else ""
    # take just the first 4 characters from a date like 2023-08-03 for eg

    # metacritic should always be present since we filtered for it when fetching
    metacritic = game.get("metacritic", "")
    if metacritic is None:
        metacritic = ""
        # here we are just checking if key value is null or not

    platform_names = [p["platform"]["name"] for p in game.get("platforms", [])]
    # pull just the name out of every platform entry - 
    our_platforms = [name for name in platform_names if name in PLATFORMS_WE_WANT]
    # keep only the platform names that are pc or playstation 5

    genre_names = [g["name"] for g in game.get("genres", [])]
    # pull just the name out of every genre entry

    # esrb_rating is sometimes null (common for older/indie games), so we store it as unknown instead of crashing or leaving it blank used slight LLM help because it was throwing error
    esrb = game.get("esrb_rating")
    esrb_name = esrb["name"] if esrb else "unknown"

    return {
        # keep the slug so later scripts can look this exact game up again 
        "slug": game.get("slug", ""),
        "title": game.get("name", "unknown"),
        # rawg calls this field name, but we rename it to title in our own csv
        "release_year": release_year,
        "metacritic": metacritic,
        "platforms": "; ".join(our_platforms),
        # join the list into one string like PC; PlayStation 5 since csv cells hold text, not lists
        "genres": "; ".join(genre_names),
        "esrb_rating": esrb_name,
    }
    # this dictionary becomes one row in the final csv - used LLM help for this bit


def save_to_csv(rows):
    fieldnames = ["slug", "title", "release_year", "metacritic", "platforms", "genres", "esrb_rating"]
    # the column headers, in the order we want them to appear in the csv
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        # newline="" avoids extra blank lines appearing between rows on windows
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        # a dictwriter matches each row's dictionary keys to the right column
        writer.writeheader()
        # write the column names as the first line of the file
        writer.writerows(rows)
        # write every cleaned game as its own row


if __name__ == "__main__":
    # this block only runs when the file is executed directly, not when imported
    games = load_raw_games()
    # read the raw list of games from the json file
    rows = [clean_game(game) for game in games]
    # clean every game into a tidy dictionary, one per row
    save_to_csv(rows)
    # write all the cleaned rows out to the csv file
    print(f"saved {len(rows)} rows to {OUTPUT_PATH}")
    # confirm how many rows were saved and where to find them
