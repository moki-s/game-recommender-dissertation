import csv

from collections import Counter

INPUT_PATH = "data/processed/accessibility.csv"

REQUIRED_COLUMNS = ["game_title", "feature_name", "category", "level", "source"]

VALID_CATEGORIES = {"Motor", "Cognitive", "Vision", "Hearing", "Speech", "General"}
VALID_LEVELS = {"Basic", "Intermediate", "Advanced", "Unclassified"}


def load_rows():
    with open(INPUT_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def find_problems(row):
    problems = []

    for column in REQUIRED_COLUMNS:
        if not row[column].strip():
            problems.append(f"missing {column}")
            # .strip() catches cells that are just spaces, not only truly empty ones

    if row["category"].strip() and row["category"] not in VALID_CATEGORIES:
        problems.append(f"invalid category '{row['category']}'")

    if row["level"].strip() and row["level"] not in VALID_LEVELS:
        problems.append(f"invalid level '{row['level']}'")

    return problems


if __name__ == "__main__":
    rows = load_rows()

    bad_rows = []
    for row in rows:
        problems = find_problems(row)
        if problems:
            bad_rows.append((row, problems))

    if bad_rows:
        print(f"found {len(bad_rows)} row(s) with problems:")
        for row, problems in bad_rows:
            print(f" - {row.get('game_title', '(no title)')}: {', '.join(problems)}")
    else:
        print("no problems found - every row passed all checks")

    print()
    print("=== summary ===")
    print(f"total rows: {len(rows)}")

    distinct_games = {row["game_title"] for row in rows if row["game_title"].strip()}
    print(f"distinct games covered: {len(distinct_games)}")

    category_counts = Counter(row["category"] for row in rows if row["category"].strip())
    print("features per category:")
    for category, count in category_counts.most_common():
        print(f"  {category}: {count}")
