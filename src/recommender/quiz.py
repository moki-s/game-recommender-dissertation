QUESTIONS = [
    {
        "prompt": "When you make progress in a game, what feels most rewarding?",
        "options": [
            {"text": "Becoming powerful and strong", "weights": {"advancement": 2.0}},
            {"text": "Acquiring rare, hard-to-get items", "weights": {"advancement": 2.0}},
            {"text": "Optimizing your character or build as much as possible", "weights": {"mechanics": 2.0}},
        ],
    },
    {
        "prompt": "How do you feel about competing against other players?",
        "options": [
            {"text": "I love competing and winning against others", "weights": {"competition": 2.0}},
            {"text": "It's fun now and then", "weights": {"competition": 1.0}},
            {"text": "I'd rather not play competitively", "weights": {}},
        ],
    },
    {
        "prompt": "How do you most like to play with other people?",
        "options": [
            {"text": "Chatting and socialising with other players", "weights": {"socializing": 2.0}},
            {"text": "Grouping up to achieve things as a team", "weights": {"teamwork": 2.0}},
            {"text": "I usually prefer to play alone", "weights": {}},
        ],
    },
    {
        "prompt": "How important are lasting connections in games (guilds, friends)?",
        "options": [
            {"text": "Very - being part of a guild and keeping in touch matters to me", "weights": {"relationship": 2.0}},
            {"text": "Somewhat important", "weights": {"relationship": 1.0}},
            {"text": "Not important to me", "weights": {}},
        ],
    },
    {
        "prompt": "How do you feel about exploring a game's world?",
        "options": [
            {"text": "I explore every corner just for the sake of exploring", "weights": {"discovery": 2.0}},
            {"text": "I love learning its stories and lore", "weights": {"discovery": 2.0}},
            {"text": "Exploring isn't really my thing", "weights": {}},
        ],
    },
    {
        "prompt": "What pulls you into a game most?",
        "options": [
            {"text": "Role-playing a character with their own backstory", "weights": {"role-playing": 2.0}},
            {"text": "Feeling immersed and escaping into the world", "weights": {"escapism": 2.0}},
            {"text": "I focus on the gameplay, not the world", "weights": {}},
        ],
    },
    {
        "prompt": "How much do you enjoy customising things (characters, gear, spaces)?",
        "options": [
            {"text": "A lot - personalising things is part of the fun", "weights": {"customization": 2.0}},
            {"text": "A little", "weights": {"customization": 1.0}},
            {"text": "Not important to me", "weights": {}},
        ],
    },
]

# after answering, add up weights from every chosen option into a single motivation_weights dict - used LLM help here
def score_answers(answers):
    weights = {}
    for question_index, option_index in enumerate(answers):
        # option_index is None when the user skipped that question (they described a vibe instead) - ignore it
        if option_index is None:
            continue
        chosen_option = QUESTIONS[question_index]["options"][option_index]
        for motivation, weight in chosen_option["weights"].items():
            weights[motivation] = weights.get(motivation, 0.0) + weight
    return weights


def run_quiz():
    print("answer each question by typing the number of the option that fits you best.\n")
    answers = []
    for question in QUESTIONS:
        print(question["prompt"])
        for i, option in enumerate(question["options"], start=1):
            print(f"  {i}. {option['text']}")

        while True:
            choice = input("your choice: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(question["options"]):
                answers.append(int(choice) - 1)
                break
            print(f"  please type a number between 1 and {len(question['options'])}")
        print()

    return score_answers(answers)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    weights = run_quiz()
    print("your motivation weights:")
    print(weights)
