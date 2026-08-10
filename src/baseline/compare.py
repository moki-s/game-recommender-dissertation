import sys

sys.path.insert(0, "src/graph")
sys.path.insert(0, "src/graphrag")
sys.path.insert(0, "src/baseline")
from connection import get_driver
from queries import recommend_games
from explain import explain_recommendation
from vector_rag import recommend_baseline, explain_from_description, fetch_summaries  # the baseline

# these are the 3 fixed personas
PERSONAS = [
    {
        "name": "Explorer",
        "platform": "PC",
        "motivation_weights": {"discovery": 2.0, "role-playing": 2.0},
        "required_accessibility": [],
        "max_age_rating": None,
        "preference_text": "I enjoy games about discovery and role-playing - exploring open worlds and inhabiting a character with a rich story",
    },
    {
        "name": "Competitor",
        "platform": "PlayStation 5",
        "motivation_weights": {"competition": 2.0, "advancement": 2.0},
        "required_accessibility": [],
        "max_age_rating": None,
        "preference_text": "I enjoy competitive games about advancement - competing against other players and building up power and progress",
    },
    {
        "name": "Low-vision player",
        "platform": "PC",
        "motivation_weights": {"advancement": 2.0, "role-playing": 1.0},
        "required_accessibility": ["Vision"],
        "max_age_rating": None,
        "preference_text": "I enjoy role-playing games about advancement and character progression, and I need good vision accessibility support",
    },
]


def platforms_for(titles):
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (g:Game)-[:AVAILABLE_ON]->(p:Platform) WHERE g.title IN $titles "
            "RETURN g.title AS title, collect(p.name) AS platforms",
            titles=titles,
        )
        platforms = {record["title"]: record["platforms"] for record in result}
    driver.close()
    return platforms

#used LLM help 
def run_comparison():
    for persona in PERSONAS:
        print("=" * 80)
        print(f"PERSONA: {persona['name']}   (wants platform: {persona['platform']})")
        print("=" * 80)

        graph_results = recommend_games(
            platform=persona["platform"],
            motivation_weights=persona["motivation_weights"],
            required_accessibility=persona["required_accessibility"],
            max_age_rating=persona["max_age_rating"],
            limit=5,
        )
        print("\n[ GRAPH SYSTEM - top 5 ]")
        for i, g in enumerate(graph_results, start=1):
            print(f"  {i}. {g['title']}  (score {g['score']}, acc {g['accessibility_matches']})")
        if graph_results:
            print("  why #1:", explain_recommendation(graph_results[0]))

        baseline_results = recommend_baseline(persona["preference_text"], limit=5, explain=False)
        base_platforms = platforms_for([b["title"] for b in baseline_results])
        print("\n[ VECTOR-RAG BASELINE - top 5 ]")
        for i, b in enumerate(baseline_results, start=1):
            plats = base_platforms.get(b["title"], [])
            flag = "" if persona["platform"] in plats else f"   [NOT on {persona['platform']}]"
            print(f"  {i}. {b['title']}  (similarity {round(b['score'], 3)}){flag}")
        if baseline_results:
            top = baseline_results[0]
            top_summary = fetch_summaries([top["title"]]).get(top["title"], "")
            print("  why #1:", explain_from_description(persona["preference_text"], top["title"], top_summary))

        print()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    run_comparison()
