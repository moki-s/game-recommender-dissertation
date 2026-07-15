"""merge rawg and igdb game data into one file by matching titles across both."""

import csv
import re
# re (regular expressions) lets us strip punctuation out of titles - used LLM for help

RAWG_PATH = "data/processed/games_enriched.csv"
IGDB_PATH = "data/processed/games_igdb.csv"
MERGED_PATH = "data/processed/games_merged.csv"
UNMATCHED_PATH = "data/processed/unmatched.csv"

# common edition wording that gets added to re-releases but doesn't change what the underlying game is
EDITION_WORDS = [
    "game of the year edition",
    "goty edition",
    "definitive edition",
    "enhanced edition",
    "complete edition",
    "ultimate edition",
    "gold edition",
    "legendary edition",
    "special edition",
    "deluxe edition",
    "anniversary edition",
    "directors cut",
    "extended edition",
    "remastered",
    "remaster",
    "hd edition",
    "update",
    "collection",
]


def normalise_title(title):
    title = title.lower()
    # lowercase first so "Half-Life" and "half-life" are treated as equal

    title = re.sub(r"[^\w\s]", "", title)
    # \w means "word character" (letters/numbers/underscore)
    # \s means whitespace, so this removes everything else - colons, apostrophes, hyphens - turning "Baldur's Gate III" into "baldurs gate iii" - used LLM for help

    for word in EDITION_WORDS:
        title = title.replace(word, "")

    title = re.sub(r"\s+", " ", title).strip()

    return title


def make_key(title, year):
    return (normalise_title(title), str(year).strip())


def load_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_igdb_lookup(igdb_rows):
    lookup = {}
    for row in igdb_rows:
        key = make_key(row["title"], row["release_year"])
        if key not in lookup:
            lookup[key] = row
    return lookup


def merge_games(rawg_rows, igdb_lookup):
    merged_rows = []
    unmatched_rawg = []
    matched_keys = set()

    for rawg_row in rawg_rows:
        key = make_key(rawg_row["title"], rawg_row["release_year"])
        igdb_row = igdb_lookup.get(key)
        #used LLM for help
        merged_row = dict(rawg_row)

        if igdb_row:
            merged_row["themes"] = igdb_row["themes"]
            merged_row["game_modes"] = igdb_row["game_modes"]
            merged_row["pegi_rating"] = igdb_row["pegi_rating"]
            matched_keys.add(key)
        else:
            # no igdb match, so we still keep the game but leave these blank
            merged_row["themes"] = ""
            merged_row["game_modes"] = ""
            merged_row["pegi_rating"] = ""
            unmatched_rawg.append(rawg_row)

        merged_rows.append(merged_row)

    return merged_rows, unmatched_rawg, matched_keys


def save_merged_csv(rows):
    fieldnames = list(rows[0].keys())
    # reuse whatever columns the first row has (rawg's columns plus our 3 new ones)
    with open(MERGED_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save_unmatched_csv(unmatched_rawg):
    # just title and release_year - enough information to go look the game
    # up by hand and see why it didn't match
    rows = [{"title": r["title"], "release_year": r["release_year"]} for r in unmatched_rawg]
    with open(UNMATCHED_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "release_year"])
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    rawg_rows = load_csv(RAWG_PATH)
    igdb_rows = load_csv(IGDB_PATH)

    igdb_lookup = build_igdb_lookup(igdb_rows)
    merged_rows, unmatched_rawg, matched_keys = merge_games(rawg_rows, igdb_lookup)

    save_merged_csv(merged_rows)
    save_unmatched_csv(unmatched_rawg)

    matched_count = len(rawg_rows) - len(unmatched_rawg)

    # count how many igdb rows' keys were never claimed by any rawg game
    igdb_unmatched_count = 0
    for row in igdb_rows:
        key = make_key(row["title"], row["release_year"])
        if key not in matched_keys:
            igdb_unmatched_count += 1

    print(f"{matched_count} rawg games matched an igdb game")
    print(f"{len(unmatched_rawg)} rawg games had no igdb match (see {UNMATCHED_PATH})")
    print(f"{igdb_unmatched_count} igdb games had no rawg match")
