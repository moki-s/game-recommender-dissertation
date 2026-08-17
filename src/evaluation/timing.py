import csv
import sys
import time

sys.path.insert(0, "src/graph")
sys.path.insert(0, "src/baseline")
sys.path.insert(0, "src/graphrag")
sys.path.insert(0, "src/evaluation")
from queries import recommend_games
from vector_rag import recommend_baseline
from explain import explain_recommendation
from run_eval import persona_to_text
from personas import PERSONAS

OUTPUT_CSV = "data/processed/timing_results.csv"
REPEATS = 5


def graph_retrieval(persona):
    # the graph system's retrieval - used LLm for help
    return recommend_games(
        platform=persona["platform"],
        motivation_weights=persona["motivation_weights"],
        required_accessibility=persona["required_accessibility"],
        max_age_rating=persona["max_age_rating"],
        limit=5,
        vibe_text=persona["vibe_text"],
        vibe_weight=5.0 if persona["vibe_text"] else 0.0,
    )


def average_seconds(function, repeats):
    start = time.perf_counter()
    for _ in range(repeats):
        function()
    return (time.perf_counter() - start) / repeats


def run():
    warm = PERSONAS[0]
    graph_retrieval(warm)
    recommend_baseline(persona_to_text(warm), limit=5, explain=False)

    rows = []
    print(f"{'persona':28s}{'graph (ms)':>14s}{'baseline (ms)':>16s}")
    for persona in PERSONAS:
        text = persona_to_text(persona)
        graph_ms = average_seconds(lambda: graph_retrieval(persona), REPEATS) * 1000
        baseline_ms = average_seconds(lambda: recommend_baseline(text, limit=5, explain=False), REPEATS) * 1000
        rows.append({"persona": persona["name"],
                     "graph_retrieval_ms": round(graph_ms, 1),
                     "baseline_retrieval_ms": round(baseline_ms, 1)})
        print(f"{persona['name']:28s}{graph_ms:>14.1f}{baseline_ms:>16.1f}")

    # time one explanation per persona (top pick) to show the llm cost
    explanation_times = []
    for persona in PERSONAS:
        top = graph_retrieval(persona)
        if not top:
            continue
        start = time.perf_counter()
        explain_recommendation(top[0])
        explanation_times.append(time.perf_counter() - start)

    # averages for the report - used LLM to optimize
    graph_avg = sum(r["graph_retrieval_ms"] for r in rows) / len(rows)
    baseline_avg = sum(r["baseline_retrieval_ms"] for r in rows) / len(rows)
    explanation_avg = (sum(explanation_times) / len(explanation_times)) * 1000

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["persona", "graph_retrieval_ms", "baseline_retrieval_ms"])
        writer.writeheader()
        writer.writerows(rows)

    print()
    print(f"average graph retrieval:    {graph_avg:8.1f} ms")
    print(f"average baseline retrieval: {baseline_avg:8.1f} ms")
    print(f"average explanation (llm):  {explanation_avg:8.1f} ms  (both systems share this step)")
    print()
    print("note: retrieval is fast in both systems; the llm explanation dominates the total time, and")
    print("it is the same model for both, so the systems are comparable in speed. a full request also")
    print("runs one explanation per recommended game (five here).")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    run()
