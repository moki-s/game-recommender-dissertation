"""find catalogue games that don't yet appear in the awards seed - your hand-check worklist."""

import csv
import sys

from merge_sources import normalise_title

CATALOGUE_PATH = "data/processed/games_merged.csv"
AWARDS_SEED_PATH = "data/processed/awards_seed.csv"
OUTPUT_PATH = "data/processed/awards_todo.csv"

# our kaggle awards_seed only covers the game awards ceremonies from 2014 to 2019 checked by looking at the actual file's min/max year
EARLIEST_COVERED_YEAR = 2014
LATEST_COVERED_YEAR = 2019

sys.stdout.reconfigure(encoding="utf-8")


def load_catalogue_rows():
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_seed_titles():
    with open(AWARDS_SEED_PATH, encoding="utf-8") as f:
        return [row["game_title"] for row in csv.DictReader(f)]


def released_in_covered_range(row):
    year = row["release_year"]
    if not year:
        return False
        # if we don't even know the release year, we can't tell if it falls inside the range the awards seed covers, so we leave it out - used LLM help
    return EARLIEST_COVERED_YEAR <= int(year) <= LATEST_COVERED_YEAR


if __name__ == "__main__":
    catalogue_rows = load_catalogue_rows()
    seed_titles = load_seed_titles()

    normalised_seed_titles = {normalise_title(t) for t in seed_titles}
    # a set of every title already covered in the seed, so checking membership below is a quick lookup instead of a slow title-by-title comparison

    todo_titles = [
        row["title"] for row in catalogue_rows
        if released_in_covered_range(row)
        and normalise_title(row["title"]) not in normalised_seed_titles
    ]

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["game_title"])
        writer.writeheader()
        for title in todo_titles:
            writer.writerow({"game_title": title})

    print(f"{len(todo_titles)} games (released {EARLIEST_COVERED_YEAR}-{LATEST_COVERED_YEAR}) still need checking by hand")
    print(f"saved worklist to {OUTPUT_PATH}")
    for title in todo_titles:
        print(f" - {title}")
