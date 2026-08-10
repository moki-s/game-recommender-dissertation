import csv
import sys

sys.path.insert(0, "src/evaluation")
from personas import PERSONAS

RESULTS_CSV = "data/processed/eval_results.csv"


def load_rows():
    with open(RESULTS_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

# 4 metrics are defined below- used LLm to optimize
def constraint_violations(rows):
    print("=== 1. CONSTRAINT VIOLATIONS (lower is better; graph should be 0) ===")
    print(f"{'system':10s}{'off-platform':>14s}{'over-age':>10s}{'total bad':>12s}")
    for system in ["graph", "baseline"]:
        subset = [r for r in rows if r["system"] == system]
        off_platform = sum(1 for r in subset if r["on_correct_platform"] == "False")
        over_age = sum(1 for r in subset if r["within_age_limit"] == "False")
        print(f"{system:10s}{off_platform:>14d}{over_age:>10d}{off_platform + over_age:>12d}")
    print()


def accessibility_coverage(rows):
    need_personas = [p["name"] for p in PERSONAS if p["required_accessibility"]]
    print("=== 2. ACCESSIBILITY COVERAGE (personas with a stated need) ===")
    print(f"personas with a need: {', '.join(need_personas) if need_personas else 'none'}")
    print(f"{'system':10s}{'games supporting need':>24s}{'out of':>10s}")
    for system in ["graph", "baseline"]:
        subset = [r for r in rows if r["system"] == system and r["persona"] in need_personas]
        supported = sum(1 for r in subset if int(r["accessibility_matches"]) > 0)
        print(f"{system:10s}{supported:>24d}{len(subset):>10d}")
    print()


def overlap(rows):
    print("=== 3. OVERLAP between graph and baseline (per persona) ===")
    print(f"{'persona':28s}{'shared games':>14s}")
    total_shared = 0
    total_possible = 0
    for persona in PERSONAS:
        name = persona["name"]
        graph_titles = {r["game_title"] for r in rows if r["persona"] == name and r["system"] == "graph"}
        base_titles = {r["game_title"] for r in rows if r["persona"] == name and r["system"] == "baseline"}
        shared = len(graph_titles & base_titles)
        possible = min(len(graph_titles), len(base_titles))
        total_shared += shared
        total_possible += possible
        print(f"{name:28s}{shared:>7d} / {possible}")
    print(f"{'OVERALL':28s}{total_shared:>7d} / {total_possible}")
    print()


def award_presence(rows):
    print("=== 4. AWARD PRESENCE (recommended games that won a major award) ===")
    print(f"{'system':10s}{'award-winning':>16s}{'out of':>10s}{'share':>9s}")
    for system in ["graph", "baseline"]:
        subset = [r for r in rows if r["system"] == system]
        with_award = sum(1 for r in subset if r["award"] != "none")
        share = with_award / len(subset) if subset else 0
        print(f"{system:10s}{with_award:>16d}{len(subset):>10d}{share:>8.0%}")
    print()


def run():
    rows = load_rows()
    print(f"loaded {len(rows)} rows from {RESULTS_CSV}\n")
    constraint_violations(rows)
    accessibility_coverage(rows)
    overlap(rows)
    award_presence(rows)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    run()
