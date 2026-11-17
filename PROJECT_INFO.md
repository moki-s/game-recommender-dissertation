# Project Info & Working Notes

Quick reference for continuing work on this project from any machine.

## Repositories

| Remote | URL | Purpose |
|---|---|---|
| `github` | https://github.com/moki-s/game-recommender-dissertation.git | Public mirror / showcase (primary for ongoing work) |
| `origin` | git@git.cs.bham.ac.uk:projects-2025-26/mxs1906.git | University GitLab (dissertation submission record) |

Git identity for commits: `moki-s <mokiviral@gmail.com>`.

Note: the GitLab `main` branch is protected (no force-push), and its tip commit message differs slightly from the local/GitHub history after an amend. Treat **GitHub as the source of truth** for ongoing work; don't pull from GitLab over it.

## Setting up on a new PC

```bash
git clone https://github.com/moki-s/game-recommender-dissertation.git
cd game-recommender-dissertation
git config user.name "moki-s"
git config user.email "mokiviral@gmail.com"

python -m venv venv
venv/Scripts/activate        # Windows
pip install -r requirements.txt
```

Then create a `.env` in the project root (copy `.env.example`) with the Neo4j URI, username and password. RAWG/IGDB API keys are only needed to rebuild the catalogue from scratch — the prepared data is already in `data/processed`.

**Not in the repo (by design):** `.env` (secrets), `venv/`, `data/raw/` (large API dumps), and the private dissertation notes (`report docs/`). Set up the first two fresh on a new machine; the system runs fully from `data/processed` without the raw data.

## Running (full steps in README.md)

1. Start Neo4j; start Ollama and `ollama pull llama3.1:8b`
2. `python -m src.data_pipeline.load_graph` — build the knowledge graph
3. `python -m src.graphrag.embeddings` — build embeddings + vector index (re-run after any graph rebuild)
4. `uvicorn src.api.main:app --reload` → http://127.0.0.1:8000
5. Reproduce the evaluation: `python -m src.evaluation.run_eval`

There is no cloud deployment — the system is local by design (privacy of accessibility data; NFR4 in the dissertation).

## Headline results (for posts, CV, portfolio)

Graph system vs. vector RAG baseline (same catalogue, same embeddings, same LLM), 8 personas × top-5:

- Constraint violations: **0 vs 14** (of 40)
- Motivation match: **92% vs 68%**
- Accessibility coverage (low-vision persona): **5/5 vs 0/5**
- Award-winning recommendations: **78% vs 0%**
- Explanation faithfulness: **7/8** top picks, zero fabricated games
- Retrieval: **~36 ms vs ~60 ms** per persona
- User study (N=9): **89%** agreed a faithful reason made recommendations more trustworthy than a plain list

---

## LinkedIn caption options

### Option 1 — Full story (long)

> 🎮 **I built a game recommender that is structurally incapable of hallucinating — and it earned me my MSc.**
>
> For my MSc Advanced Computer Science dissertation at the University of Birmingham, I designed and built a **persona-based, accessibility-aware game recommendation system using GraphRAG** — and evaluated it head-to-head against a standard vector RAG baseline.
>
> The problem: mainstream recommenders need your play history, so they fail new users completely — and they treat accessibility as an afterthought. Disabled players can't even search game stores by the accessibility features they need.
>
> My approach:
> 🔹 A Neo4j knowledge graph of 500 critically acclaimed PC/PS5 games — genres, themes, awards, age ratings, and accessibility features as first-class, queryable structure
> 🔹 Players described by a short quiz built on Yee's validated motivation model — no history required
> 🔹 One deterministic Cypher query does ALL the ranking; a local LLM (Llama 3.1 via Ollama) is only allowed to phrase facts the graph already produced — it never sees the catalogue, so it literally cannot invent a recommendation
>
> Results vs. the vector RAG baseline (same catalogue, same embeddings, same LLM):
> ✅ 0 platform/age constraint violations — the baseline broke 14 of 40
> ✅ 92% of recommendations matched the player's motivations (vs 68%)
> ✅ Full accessibility coverage for a low-vision persona — the baseline achieved none
> ✅ Faithful explanations, verified claim by claim — and 89% of user-study participants said a genuine reason made them trust a recommendation more than a plain list
>
> My biggest takeaway: **trustworthy AI is an architecture problem, not a model-size problem.** Don't ask an LLM to be reliable — design the system so it doesn't get the chance to fail.
>
> Code and evaluation results: https://github.com/moki-s/game-recommender-dissertation
>
> Grateful to my supervisor Anelia Kurteva for her guidance throughout. 🙏
>
> #GraphRAG #KnowledgeGraphs #Neo4j #RecommenderSystems #Accessibility #LLM #MSc #UniversityOfBirmingham

### Option 2 — Punchy & technical (medium)

> Most LLM apps try to *reduce* hallucination. For my MSc dissertation, I built a recommender where hallucination is **architecturally impossible**.
>
> The trick: a strict split of jobs. A Neo4j knowledge graph of 500 acclaimed games makes every decision — filtering by platform and age, scoring by player motivations, awards and accessibility support — in one deterministic Cypher query. A local LLM (Llama 3.1 8B) only ever sees the facts of games already chosen, and turns them into a one-sentence explanation. It can't invent a game it has never seen.
>
> Head-to-head vs. a vector RAG baseline on identical data: 0 constraint violations vs 14, 92% vs 68% motivation match, full accessibility coverage vs none.
>
> The lesson I'm taking into every AI system I build next: reliability comes from architecture, not model size.
>
> 🔗 https://github.com/moki-s/game-recommender-dissertation
>
> #GraphRAG #Neo4j #KnowledgeGraphs #LLM #RecommenderSystems

### Option 3 — Accessibility-first angle (medium)

> Did you know most game stores can't be searched by accessibility features? Disabled players often rely on word of mouth just to find a game they can physically play.
>
> That gap became my MSc dissertation at the University of Birmingham: the **first accessibility-aware game recommender**, built on a Neo4j knowledge graph and GraphRAG. Accessibility needs aren't an afterthought — they're structured, queryable data the ranking acts on directly. No play history needed: you describe the player, and a validated motivation model does the matching.
>
> For a low-vision test persona, my system recommended five games that all genuinely support the needed features. The standard vector RAG baseline? Zero. And because the LLM only phrases facts the graph has already decided, every explanation is faithful by construction.
>
> Inclusive design and trustworthy AI aren't add-ons — they have to be built into the architecture.
>
> 🔗 https://github.com/moki-s/game-recommender-dissertation
>
> #Accessibility #InclusiveDesign #GraphRAG #Neo4j #GameDev #MSc

### Option 4 — Short & personal

> From gamer to MSc graduate 🎮→🎓
>
> My dissertation: a game recommender that knows nothing about your history, respects your accessibility needs, and explains every pick with reasons it provably didn't make up — powered by a Neo4j knowledge graph + GraphRAG, with the LLM locked out of every decision.
>
> 0 broken constraints. 92% motivation match. Faithful explanations. All running locally.
>
> Code: https://github.com/moki-s/game-recommender-dissertation
>
> #GraphRAG #Neo4j #LLM #MSc #UniversityOfBirmingham
