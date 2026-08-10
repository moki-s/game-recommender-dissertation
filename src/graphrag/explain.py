import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b"


def build_facts_text(game_result):
    facts = [f"game title: {game_result['title']}"]

    if game_result.get("matched_motivations"):
        facts.append("player motivations this game matches: " + ", ".join(game_result["matched_motivations"]))

    if game_result.get("won_awards"):
        facts.append("awards this game won: " + "; ".join(game_result["won_awards"]))

    accessibility = game_result.get("accessibility_matches", 0)
    if accessibility > 0:
        facts.append(f"number of the player's required accessibility features this game supports: {accessibility}")

    return "\n".join(facts)

# prompt build
def build_prompt(facts_text):
    return (
        "You are helping explain a video game recommendation to a player. "
        "Using ONLY the facts listed below, write ONE short, friendly sentence explaining why this "
        "game was recommended. Do not invent anything, do not mention any fact that is not listed, "
        "and write only that one sentence.\n\n"
        f"Facts:\n{facts_text}\n\n"
        "Explanation sentence:"
    )


def template_sentence(game_result):
    parts = []
    if game_result.get("matched_motivations"):
        parts.append("it matches your interest in " + ", ".join(game_result["matched_motivations"]))
    if game_result.get("won_awards"):
        parts.append("it won " + game_result["won_awards"][0])
    if game_result.get("accessibility_matches", 0) > 0:
        parts.append(f"it supports {game_result['accessibility_matches']} of your accessibility needs")

    if not parts:
        return f"{game_result['title']} fits your chosen platform and preferences."
    return f"{game_result['title']} was recommended because " + " and ".join(parts) + "."


def explain_recommendation(game_result):
    facts_text = build_facts_text(game_result)
    prompt = build_prompt(facts_text)

    try:
        # ask the local ollama model to phrase the facts - used LLM to optimize
        response = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False,
                  "options": {"temperature": 0, "seed": 42}},
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        return data["response"].strip()
    except Exception:
        return template_sentence(game_result)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    example = {
        "title": "Elden Ring",
        "matched_motivations": ["advancement", "competition"],
        "won_awards": ["The Game Awards 2022 - Game of the Year"],
        "accessibility_matches": 0,
    }

    print("=== facts given to the llm (nothing else is available to it) ===")
    print(build_facts_text(example))
    print()
    print("=== phrased explanation ===")
    print(explain_recommendation(example))
