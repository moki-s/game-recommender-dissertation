import sys

sys.path.insert(0, "src/graph")
from queries import recommend_games

# ive hardcoded these three personas are deliberately for testing later 
PERSONAS = [
    {
        "name": "Explorer",
        "platform": "PC",
        "motivation_weights": {"discovery": 2.0, "role-playing": 2.0},
        "required_accessibility": [],
        "max_age_rating": None,
    },
    {
        "name": "Competitor",
        "platform": "PlayStation 5",
        "motivation_weights": {"competition": 2.0, "advancement": 2.0},
        "required_accessibility": [],
        "max_age_rating": None,
    },
    {
        "name": "Low-vision player",
        "platform": "PC",
        "motivation_weights": {"advancement": 2.0, "role-playing": 1.0},
        "required_accessibility": ["Screen reader with adjustable voice and speed"],
        "max_age_rating": None,
    },
]


def join_with_and(items):
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def build_reason(rec):
    # build a plain english 'because' line purely from the matched motivations and any award - used slight LLM help
    parts = []
    if rec["matched_motivations"]:
        parts.append("it matches your interest in " + join_with_and(rec["matched_motivations"]))
    if rec["won_awards"]:
        parts.append("it won " + rec["won_awards"][0])
    if not parts:
        return "because it fits your chosen platform and needs"
    return "because " + " and ".join(parts)


def run_persona(persona):
    print("=" * 70)
    print(f"PERSONA: {persona['name']}  (platform: {persona['platform']})")
    if persona["required_accessibility"]:
        print(f"  requires accessibility: {', '.join(persona['required_accessibility'])}")
    print("=" * 70)
    results = recommend_games(
        platform=persona["platform"],
        motivation_weights=persona["motivation_weights"],
        required_accessibility=persona["required_accessibility"],
        max_age_rating=persona["max_age_rating"],
        played_titles=[],
        limit=3,
    )

    if not results:
        print("  no games matched this persona's requirements.\n")
        return

    for i, rec in enumerate(results, start=1):
        print(f"{i}. {rec['title']}  (metacritic {rec['metacritic']}, our score {rec['score']})")
        print(f"   {build_reason(rec)}")
        print()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for persona in PERSONAS:
        run_persona(persona)
