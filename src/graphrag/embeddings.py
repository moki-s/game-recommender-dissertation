"""add a description embedding to every game node, so we can search games by 'vibe'.

what is an embedding? it's a list of numbers (here 384 of them) that captures the MEANING of a
piece of text. the model reads a game's summary and turns it into this list of numbers, in such a
way that summaries about similar things end up with similar numbers. so two games that "feel" alike -
even if their genres are different - end up with embeddings that sit close together. that lets us
later find games by overall vibe, not just by exact genre/theme matching, which is the second
retrieval path that makes this a true hybrid (graph + vector) system.

why a small local model (all-MiniLM-L6-v2)? it runs on our own machine (no api key, no cost, works
offline), it is fast, and it outputs a compact 384-number vector that is plenty for our catalogue.
"""
import sys

sys.path.insert(0, "src/graph")
from connection import get_driver

from sentence_transformers import SentenceTransformer

# the exact small model we use; 384 numbers per embedding, runs locally
MODEL_NAME = "all-MiniLM-L6-v2"
# how many games we handle per batch, just so we can print progress along the way
BATCH_SIZE = 50


def load_games_with_summary(session):
    # ask the graph for every game that actually has a written summary
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
