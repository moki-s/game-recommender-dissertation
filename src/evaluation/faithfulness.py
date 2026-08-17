import csv
import sys

sys.path.insert(0, "src/graph")
sys.path.insert(0, "src/graphrag")
sys.path.insert(0, "src/evaluation")
from queries import recommend_games
from explain import explain_recommendation, build_facts_text
from personas import PERSONAS

OUTPUT_CSV = "data/processed/faithfulness_results.csv"
VIBE_WEIGHT = 5.0

# the ten motivation names so we can spot a motivation the sentence names that the game did not match
ALL_MOTIVATIONS = ["advancement", "competition", "customization", "discovery", "escapism",
                   "mechanics", "relationship", "role-playing", "socializing", "teamwork"]
AWARD_WORDS = ["award", "won", "winner", "game of the year"]
ACCESS_WORDS = ["accessib"]


def norm(text):
    return text.lower().replace("-", " ")


def unsupported_claims(game, explanation):
    # return a list of claims in the sentence that were not in the facts the model was given - used LLM help
    text = norm(explanation)
    facts = norm(build_facts_text(game))
    claims = []

    for motivation in ALL_MOTIVATIONS:
        if norm(motivation) in text and norm(motivation) not in facts:
            claims.append(f"names '{motivation}', which was not in the facts")

    if not game.get("won_awards") and any(word in text for word in AWARD_WORDS):
        claims.append("mentions an award, but the game won none")

    if game.get("accessibility_matches", 0) == 0 and any(word in text for word in ACCESS_WORDS):
        claims.append("mentions accessibility, but no needs were matched")

    return claims


def run():
    rows = []
    faithful = 0

    for persona in PERSONAS:
        # in order to get the graph system's top recommendation for this persona
        results = recommend_games(
            platform=persona["platform"],
            motivation_weights=persona["motivation_weights"],
            required_accessibility=persona["required_accessibility"],
            max_age_rating=persona["max_age_rating"],
            limit=1,
            vibe_text=persona["vibe_text"],
            vibe_weight=VIBE_WEIGHT if persona["vibe_text"] else 0.0,
        )
        if not results:
            continue
        game = results[0]

        explanation = explain_recommendation(game)
        claims = unsupported_claims(game, explanation)
        if not claims:
            faithful += 1

        motivations = ", ".join(game.get("matched_motivations", [])) or "none"
        award = game["won_awards"][0] if game.get("won_awards") else "none"
        access = game.get("accessibility_matches", 0)

        print("=" * 78)
        print(f"{persona['name']}  ->  {game['title']}")
        print(f"  facts given:  motivations = {motivations}")
        print(f"                award       = {award}")
        print(f"                accessibility matches = {access}")
        print(f"  explanation:  {explanation}")
        if claims:
            print("  FLAG - possible unsupported claim(s):")
            for claim in claims:
                print(f"           - {claim}")
        else:
            print("  faithful - every claim matches a fact given")
        print()

        rows.append({
            "persona": persona["name"],
            "game_title": game["title"],
            "matched_motivations": motivations,
            "award": award,
            "accessibility_matches": access,
            "explanation": explanation,
            "faithful": not claims,
            "flags": "; ".join(claims),
        })

    # saving the pairs here so the report can show the evidence - LLM help
    fieldnames = ["persona", "game_title", "matched_motivations", "award",
                  "accessibility_matches", "explanation", "faithful", "flags"]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("=" * 78)
    print(f"auto-screen: {faithful} / {len(rows)} top recommendations stated only supported facts")
    print("(read each pair above by eye to confirm - a keyword flag can misfire on ordinary wording)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    run()
