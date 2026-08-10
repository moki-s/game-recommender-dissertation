import sys

import requests

sys.path.insert(0, "src/graph")
sys.path.insert(0, "src/recommender")
from connection import get_driver
from queries import find_similar_by_text
from quiz import QUESTIONS

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b"


def answers_to_text(answers):
    # turn the quiz answer choices into a short natural sentence describing what the player likes - used LLM help
    liked = []
    for question_index, option_index in enumerate(answers):
        option = QUESTIONS[question_index]["options"][option_index]
        if option["weights"]:
            liked.append(option["text"].lower())

    if not liked:
        return "good games in general"
    return "I enjoy games where: " + "; ".join(liked)


def fetch_summaries(titles):
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (g:Game) WHERE g.title IN $titles RETURN g.title AS title, g.summary AS summary",
            titles=titles,
        )
        summaries = {record["title"]: record["summary"] for record in result}
    driver.close()
    return summaries


def explain_from_description(preference_text, title, summary):
    prompt = (
        "A player described what they enjoy in games. Using ONLY the game description below, write "
        "ONE short, friendly sentence explaining why this game might suit them. Do not invent facts "
        "beyond the description.\n\n"
        f"Player's preferences: {preference_text}\n\n"
        f"Game: {title}\n"
        f"Description: {summary}\n\n"
        "Explanation sentence:"
    )
    #used LLM help to debug and optimize
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["response"].strip()
    except Exception:
        return f"{title} was retrieved as one of the closest matches to your described preferences."


def recommend_baseline(preference_text, limit=5, explain=True):
    matches = find_similar_by_text(preference_text, limit)

    summaries = fetch_summaries([match["title"] for match in matches])

    results = []
    for match in matches:
        summary = summaries.get(match["title"], "")
        explanation = explain_from_description(preference_text, match["title"], summary) if explain else ""
        results.append({
            "title": match["title"],
            "score": match["score"],
            "explanation": explanation,
        })
    return results


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    preference = "a relaxing story-rich adventure about exploring a beautiful world"
    print(f"preference text: {preference}\n")

    for i, game in enumerate(recommend_baseline(preference, limit=5), start=1):
        print(f"{i}. {game['title']}  (similarity {round(game['score'], 3)})")
        print(f"   {game['explanation']}")
        print()
