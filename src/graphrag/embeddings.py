import sys

sys.path.insert(0, "src/graph")
from connection import get_driver

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 50


def load_games_with_summary(session):
    # ask the graph for every game that actually has a written summary - used LLM to learn and write
    result = session.run(
        "MATCH (g:Game) WHERE g.summary <> '' RETURN g.slug AS slug, g.summary AS summary"
    )
    return [(record["slug"], record["summary"]) for record in result]


def store_embedding(session, slug, vector):
    session.run(
        "MATCH (g:Game {slug: $slug}) SET g.embedding = $vector",
        slug=slug, vector=vector,
    )


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    print("loading the embedding model (the first run downloads it)...")
    model = SentenceTransformer(MODEL_NAME)

    driver = get_driver()
    with driver.session() as session:
        games = load_games_with_summary(session)
        print(f"embedding {len(games)} games that have a summary...")

        for start in range(0, len(games), BATCH_SIZE):
            batch = games[start:start + BATCH_SIZE]
            summaries = [summary for slug, summary in batch]

            vectors = model.encode(summaries)

            for (slug, summary), vector in zip(batch, vectors):
                store_embedding(session, slug, vector.tolist())

            done = min(start + BATCH_SIZE, len(games))
            print(f"  embedded {done}/{len(games)} games")

    driver.close()
    print("done.")
