import csv
import sys

sys.path.insert(0, "src/graph")
sys.path.insert(0, "src/baseline")
sys.path.insert(0, "src/evaluation")
from connection import get_driver
from queries import recommend_games
from vector_rag import recommend_baseline
from personas import PERSONAS

OUTPUT_CSV = "data/processed/eval_results.csv"
TOP_N = 5
VIBE_WEIGHT = 5.0


def persona_to_text(persona):
    # turn a persona into the free-text query the baseline embeds join the motivation names into a sentence and add the vibe if there is one
    # used LLM
    motivations = list(persona["motivation_weights"].keys())
    text = "I enjoy games about " + ", ".join(motivations)
    if persona["vibe_text"]:
        text = text + ". " + persona["vibe_text"]
    return text


def drop_nulls(values):
    return [v for v in values if v is not None]


def fetch_facts(titles):
    # this is to look up the true facts about each game in one query such as platforms, age rating, awards won, and the accessibility features it supports
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (g:Game) WHERE g.title IN $titles "
            "OPTIONAL MATCH (g)-[:AVAILABLE_ON]->(p:Platform) "
            "OPTIONAL MATCH (g)-[:RATED]->(a:AgeRating) "
            "OPTIONAL MATCH (g)-[:WON]->(w:Award) "
            "OPTIONAL MATCH (g)-[:SUPPORTS]->(f:AccessibilityFeature) "
            "RETURN g.title AS title, collect(DISTINCT p.name) AS platforms, min(a.age) AS min_age, "
            "collect(DISTINCT w.name) AS won_awards, "
            "collect(DISTINCT f.name) AS acc_names, collect(DISTINCT f.category) AS acc_categories",
            titles=titles,
        )
        facts = {}
        for record in result:
            facts[record["title"]] = {
                "platforms": record["platforms"],
                "age": record["min_age"],
                "won_awards": drop_nulls(record["won_awards"]),
                "acc_names": drop_nulls(record["acc_names"]),
                "acc_categories": drop_nulls(record["acc_categories"]),
            }
    driver.close()
    return facts


def count_accessibility(persona, title, facts):
    info = facts.get(title, {"acc_names": [], "acc_categories": []})
    supported = set(info["acc_names"]) | set(info["acc_categories"])
    return sum(1 for need in persona["required_accessibility"] if need in supported)


def check_platform(persona, title, facts):
    info = facts.get(title, {"platforms": []})
    return persona["platform"] in info["platforms"]


def check_age(persona, title, facts):
    if persona["max_age_rating"] is None:
        return True
    age = facts.get(title, {"age": None})["age"]
    return age is not None and age <= persona["max_age_rating"]


def run():
    rows = []

    for persona in PERSONAS:
        # graph system
        graph_results = recommend_games(
            platform=persona["platform"],
            motivation_weights=persona["motivation_weights"],
            required_accessibility=persona["required_accessibility"],
            max_age_rating=persona["max_age_rating"],
            limit=TOP_N,
            vibe_text=persona["vibe_text"],
            vibe_weight=VIBE_WEIGHT if persona["vibe_text"] else 0.0,
        )

        preference_text = persona_to_text(persona)
        baseline_results = recommend_baseline(preference_text, limit=TOP_N, explain=False)

        all_titles = [g["title"] for g in graph_results] + [b["title"] for b in baseline_results]
        facts = fetch_facts(all_titles)

        for rank, g in enumerate(graph_results, start=1):
            award = g["won_awards"][0] if g.get("won_awards") else "none"
            rows.append({
                "persona": persona["name"],
                "system": "graph",
                "rank": rank,
                "game_title": g["title"],
                "score": round(g["score"], 3),
                "matched_motivations": "; ".join(g.get("matched_motivations", [])) or "none",
                "award": award,
                "accessibility_matches": g.get("accessibility_matches", 0),
                "on_correct_platform": check_platform(persona, g["title"], facts),
                "within_age_limit": check_age(persona, g["title"], facts),
            })

        for rank, b in enumerate(baseline_results, start=1):
            info = facts.get(b["title"], {"won_awards": []})
            baseline_award = info["won_awards"][0] if info["won_awards"] else "none"
            rows.append({
                "persona": persona["name"],
                "system": "baseline",
                "rank": rank,
                "game_title": b["title"],
                "score": round(b["score"], 3),
                "matched_motivations": "none",
                "award": baseline_award,
                "accessibility_matches": count_accessibility(persona, b["title"], facts),
                "on_correct_platform": check_platform(persona, b["title"], facts),
                "within_age_limit": check_age(persona, b["title"], facts),
            })

    fieldnames = ["persona", "system", "rank", "game_title", "score", "matched_motivations",
                  "award", "accessibility_matches", "on_correct_platform", "within_age_limit"]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} rows to {OUTPUT_CSV}\n")
    for system in ["graph", "baseline"]:
        subset = [r for r in rows if r["system"] == system]
        bad_platform = sum(1 for r in subset if not r["on_correct_platform"])
        bad_age = sum(1 for r in subset if not r["within_age_limit"])
        print(f"{system:9s}: {len(subset)} recommendations, "
              f"{bad_platform} off-platform, {bad_age} over-age")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    run()
