# Persona-Based Game Recommendation System using GraphRAG

A persona-based, **accessibility-aware** and **explainable** recommender for critically acclaimed PC and PlayStation 5 games — built on a Neo4j knowledge graph with a GraphRAG explanation pipeline, and evaluated against a vanilla vector RAG baseline.

Developed as my MSc Advanced Computer Science dissertation project at the University of Birmingham.

## The idea

Mainstream game recommenders need your play history — so they fail new and privacy-conscious players completely (the cold-start problem). And they treat accessibility as an afterthought: game stores can't even be searched by the accessibility features a disabled player needs.

This system addresses both at once:

- **A player is a persona, not a history.** A short quiz built on Yee's validated model of gaming motivations, plus accessibility needs, an optional age limit and an optional free-text mood.
- **A knowledge graph makes the decision.** 500 acclaimed games (Metacritic ≥ 85 or a major award) are encoded in Neo4j with their genres, themes, modes, platforms, age ratings, awards and accessibility features. A single deterministic Cypher query enforces the hard constraints (platform, age) and scores the soft preferences (motivations, awards, accessibility).
- **The LLM can only phrase, never choose.** A local language model (Llama 3.1 8B via Ollama) turns the graph's facts for each recommended game into a sentence. It never sees the catalogue and never selects or reorders games — so it is structurally unable to hallucinate a recommendation.

The central design principle: **trustworthy recommendation is achieved by architecture, not model size.**

### The persona bridge

There is deliberately no direct edge between a game and a motivation. Motivations connect to the genres, themes and modes that satisfy them via a `SATISFIED_BY` relationship, so a game reaches a motivation only through its own attributes — and the path itself *is* the explanation for the match.

## Results vs. a fair vector RAG baseline

The baseline shares the same catalogue, the same embedding model (all-MiniLM-L6-v2) and the same LLM — the only variable is the retrieval method. Evaluated over 8 fixed personas × top-5 recommendations each:

| Metric | Graph system | Vector RAG baseline |
|---|---|---|
| Platform/age constraint violations (of 40) | **0** | 14 |
| Recommendations matching a motivation | **37/40 (92%)** | 27/40 (68%) |
| Accessibility coverage, low-vision persona (of 5) | **5** | 0 |
| Award-winning recommendations | **78%** | 0% |
| Explanation faithfulness (top pick per persona) | **7/8** | n/a |
| Retrieval time per persona | **~36 ms** | ~60 ms |

A small anonymous user study (N = 9) supported the trust claim: 89% agreed that seeing a faithful reason made a recommendation more trustworthy than a plain list.

## Repository layout

```
src/data_pipeline   Builds the catalogue: fetches from RAWG & IGDB, cleans, merges,
                    normalises titles, enriches descriptions, seeds awards &
                    accessibility data, and loads the Neo4j knowledge graph
src/graph           Database connection and the deterministic recommendation query
src/graphrag        Embedding/vector-index builder and the LLM explanation layer
src/recommender     Quiz scoring and a command-line runner
src/baseline        The vanilla vector RAG baseline and a comparison harness
src/evaluation      Evaluation personas, metrics, faithfulness check, timing, runner
src/api             FastAPI app serving the web interface and recommendation endpoint
frontend            Single-page web UI (plain HTML + vanilla JavaScript)
data/processed      Prepared catalogue, awards, accessibility and evaluation results
```

## Tech stack

Python · Neo4j (Cypher + vector index) · sentence-transformers (all-MiniLM-L6-v2, 384-d embeddings) · Ollama (llama3.1:8b) · FastAPI · plain HTML/JS. Everything runs locally — no accounts, no personal data.

## Running it

Prerequisites: Python 3, a running Neo4j database, and Ollama serving `llama3.1:8b`. RAWG/IGDB API keys are only needed to rebuild the catalogue from scratch — the prepared data is included under `data/processed`.

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create a .env in the project root with your Neo4j settings
#    (see .env.example; add RAWG/IGDB keys only to rebuild the catalogue)

# 3. Start Neo4j, and pull the model
ollama pull llama3.1:8b

# 4. Build the knowledge graph from the prepared data
python -m src.data_pipeline.load_graph

# 5. Build the embeddings and vector index (re-run after any graph rebuild)
python -m src.graphrag.embeddings

# 6. Start the web app, then open http://127.0.0.1:8000
uvicorn src.api.main:app --reload

# Reproduce the evaluation
python -m src.evaluation.run_eval
```

To rebuild the catalogue from RAWG and IGDB instead of the included data, run the `src/data_pipeline` scripts in order (fetch, clean, merge, normalise, enrich, seed) before step 4.

## Author

Mokshith Sanga — MSc Advanced Computer Science, University of Birmingham.
Supervised by Anelia Kurteva.
