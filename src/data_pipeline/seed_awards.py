import csv

INPUT_PATH = "data/raw/kaggle_game_awards.csv"
OUTPUT_PATH = "data/processed/awards_seed.csv"

AWARD_NAME = "The Game Awards"


def load_kaggle_rows():
    with open(INPUT_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))

# used LLM help to understand
def preview_kaggle_data(rows):
    print("kaggle column names:", list(rows[0].keys()))
    print()
    print("first 3 rows:")
    for row in rows[:3]:
        print(row)
    print()

# used LLM help to understand
def reshape_row(kaggle_row):
    result = "won" if kaggle_row["winner"] == "1" else "nominated"

    return {
        "game_title": kaggle_row["nominee"],
        "award_name": AWARD_NAME,
        "year": kaggle_row["year"],
        "category": kaggle_row["category"],
        "result": result,
    }


def save_seed_csv(rows):
    fieldnames = ["game_title", "award_name", "year", "category", "result"]
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    kaggle_rows = load_kaggle_rows()
    preview_kaggle_data(kaggle_rows)

    seed_rows = [reshape_row(row) for row in kaggle_rows]
    save_seed_csv(seed_rows)

    distinct_games = {row["game_title"] for row in seed_rows}

    print(f"{len(seed_rows)} award rows produced")
    print(f"{len(distinct_games)} distinct games covered")
    print(f"saved seed to {OUTPUT_PATH}")
