import csv
import re
import unicodedata

ROMAN_NUMERALS = {
    "ii": "2", "iii": "3", "iv": "4", "v": "5",
    "vi": "6", "vii": "7", "viii": "8", "ix": "9", "x": "10",
}

EDITION_WORDS = {
    "goty", "definitive", "enhanced", "complete", "legendary", "remastered", "edition",
}

EDITION_PHRASES = ["game of the year", "directors cut", "editors choice"]


def strip_accents(text):
    decomposed = unicodedata.normalize("NFKD", text)
    # in order to keep only the characters that are not combining accent marks, leaving the plain letters and used LLM help for this
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def normalise_title(title):
    title = title.lower()
    title = strip_accents(title)

    title = re.sub(r"\(\d{4}\)", " ", title)

    title = re.sub(r"[^\w\s]", "", title)

    for phrase in EDITION_PHRASES:
        title = title.replace(phrase, " ")

    words = []
    for word in title.split():
        if word in EDITION_WORDS:
            continue
        words.append(ROMAN_NUMERALS.get(word, word))

    return " ".join(words).strip()


def add_normalised_column(input_path, output_path, title_column):
    with open(input_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys())

    # here we add a normalised_title to every row, based on whichever column holds the title in this file - used LLM help for this
    for row in rows:
        row["normalised_title"] = normalise_title(row[title_column])

    fieldnames.append("normalised_title")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return rows


if __name__ == "__main__":
    catalogue = add_normalised_column(
        "data/processed/games_merged.csv",
        "data/processed/games_merged_normalised.csv",
        "title",
    )
    awards = add_normalised_column(
        "data/processed/awards.csv",
        "data/processed/awards_normalised.csv",
        "game_title",
    )
    accessibility = add_normalised_column(
        "data/processed/accessibility.csv",
        "data/processed/accessibility_normalised.csv",
        "game_title",
    )

    award_titles_raw = {r["game_title"].lower() for r in awards}
    access_titles_raw = {r["game_title"].lower() for r in accessibility}
    before_awards = sum(1 for g in catalogue if g["title"].lower() in award_titles_raw)
    before_access = sum(1 for g in catalogue if g["title"].lower() in access_titles_raw)

    award_titles_norm = {r["normalised_title"] for r in awards}
    access_titles_norm = {r["normalised_title"] for r in accessibility}
    after_awards = sum(1 for g in catalogue if g["normalised_title"] in award_titles_norm)
    after_access = sum(1 for g in catalogue if g["normalised_title"] in access_titles_norm)

    print("=== match report (catalogue games matched) ===")
    print(f"awards:        before {before_awards}  ->  after {after_awards}")
    print(f"accessibility: before {before_access}  ->  after {after_access}")
    print()

    print("=== 10 example titles before -> after ===")
    shown = 0
    for g in catalogue:
        if g["title"].lower() != g["normalised_title"] and shown < 10:
            print(f"  {g['title']}  ->  {g['normalised_title']}")
            shown += 1
