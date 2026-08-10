from connection import get_driver

# ive implemented the whole recommendation as one cypher query and it is written as a series of WITH stages so each step hands its results to the next - used LLM help for understanding cypher
RECOMMEND_QUERY = """
MATCH (g:Game)-[:AVAILABLE_ON]->(:Platform {name: $platform})

// filtering by age
MATCH (g)-[:RATED]->(rating:AgeRating)

WHERE
    // excluding games the user has already played
    NOT g.title IN $played_titles

    AND ($max_age IS NULL OR rating.age <= $max_age)


OPTIONAL MATCH (g)-[:HAS_GENRE|HAS_THEME|HAS_MODE]->()<-[:SATISFIED_BY]-(m:Motivation)
WHERE m.name IN keys($motivation_weights)
WITH g, collect(DISTINCT m.name) AS matched_motivations

OPTIONAL MATCH (g)-[:WON]->(won:Award)
WITH g, matched_motivations,
     collect(DISTINCT won.name + " " + toString(won.year) + " - " + won.category) AS won_awards

OPTIONAL MATCH (g)-[:NOMINATED_FOR]->(nom:Award)
WITH g, matched_motivations, won_awards, count(DISTINCT nom) AS nominated_count

WITH g, matched_motivations, won_awards, nominated_count,
     // a requested need can be a specific feature name OR a whole category like "Vision" (from the ui)
     size([need IN $required_accessibility WHERE
           EXISTS { MATCH (g)-[:SUPPORTS]->(f:AccessibilityFeature)
                    WHERE f.name = need OR f.category = need }]) AS accessibility_matches

WITH g, matched_motivations, won_awards, accessibility_matches,
     reduce(total = 0.0, name IN matched_motivations | total + $motivation_weights[name]) AS motivation_score,
     (CASE WHEN size(won_awards) > 0 THEN 2 ELSE 0 END) +
     (CASE WHEN nominated_count > 0 THEN 1 ELSE 0 END) AS award_bonus

// final score = motivations + award bonus + accessibility bonus - used LLM help here as i was slightly new to this
WITH g, matched_motivations, won_awards, accessibility_matches,
     motivation_score + award_bonus + (accessibility_matches * 3) +
     (CASE WHEN $vibe_vector IS NULL THEN 0.0
           ELSE $vibe_weight * coalesce(vector.similarity.cosine(g.embedding, $vibe_vector), 0.0)
      END) AS score
RETURN g.title AS title,
       g.metacritic AS metacritic,
       score,
       matched_motivations,
       won_awards,
       accessibility_matches
ORDER BY score DESC, accessibility_matches DESC, g.metacritic DESC
LIMIT $limit
"""


def recommend_games(platform, motivation_weights, required_accessibility=None,
                    max_age_rating=None, played_titles=None, limit=3,
                    vibe_text=None, vibe_weight=0.0):
    # safe default values - used LLM here for optimization
    if required_accessibility is None:
        required_accessibility = []
    if played_titles is None:
        played_titles = []

    vibe_vector = None
    if vibe_text and vibe_weight > 0:
        vibe_vector = get_model().encode(vibe_text).tolist()
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            RECOMMEND_QUERY,
            platform=platform,
            motivation_weights=motivation_weights,
            required_accessibility=required_accessibility,
            max_age=max_age_rating,
            played_titles=played_titles,
            limit=limit,
            vibe_vector=vibe_vector,
            vibe_weight=vibe_weight,
        )

        # done here to get simple list of results back
        recommendations = []
        for record in result:
            recommendations.append({
                "title": record["title"],
                "metacritic": record["metacritic"],
                "score": record["score"],
                "matched_motivations": record["matched_motivations"],
                "won_awards": record["won_awards"],
                "accessibility_matches": record["accessibility_matches"],
            })

    driver.close()
    return recommendations


VECTOR_INDEX_NAME = "game_embedding"

_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def create_vector_index():
    driver = get_driver()
    with driver.session() as session:
        session.run(
            """
            CREATE VECTOR INDEX game_embedding IF NOT EXISTS
            FOR (g:Game) ON (g.embedding)
            OPTIONS { indexConfig: {
                `vector.dimensions`: 384,
                `vector.similarity_function`: 'cosine'
            }}
            """
        )
    driver.close()
    print("vector index is ready")


def find_similar_by_text(text, limit=5):
    query_vector = get_model().encode(text).tolist()

    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            """
            CALL db.index.vector.queryNodes($index_name, $limit, $vector)
            YIELD node, score
            RETURN node.title AS title, score
            ORDER BY score DESC
            """,
            index_name=VECTOR_INDEX_NAME, limit=limit, vector=query_vector,
        )
        # this is done in order to turn the rows into a simple list of {title, score} dicts
        matches = [{"title": record["title"], "score": record["score"]} for record in result]
    driver.close()
    return matches


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    example_weights = {"advancement": 2.0, "competition": 2.0, "discovery": 1.0}

    results = recommend_games(
        platform="PC",
        motivation_weights=example_weights,
        required_accessibility=[],
        max_age_rating=None,
        played_titles=[],
        limit=5,
    )

    print("top recommendations for the example persona:\n")
    for i, rec in enumerate(results, start=1):
        print(f"{i}. {rec['title']}  (score {rec['score']}, metacritic {rec['metacritic']})")
        print(f"   matched motivations: {rec['matched_motivations']}")
        if rec["won_awards"]:
            print(f"   awards won: {rec['won_awards']}")
        print()
