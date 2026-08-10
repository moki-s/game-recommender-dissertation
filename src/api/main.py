import os
import sys

sys.path.insert(0, "src/graph")
sys.path.insert(0, "src/recommender")
sys.path.insert(0, "src/graphrag")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from quiz import QUESTIONS, score_answers
from queries import recommend_games
from explain import explain_recommendation

app = FastAPI(title="Persona Game Recommender")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = "frontend"


@app.get("/")
def serve_home():
    # in order to serve the single web page - used LLM help
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"message": "api is running. the frontend page is added in the next step."})


@app.get("/quiz")
def get_quiz():
    return {"questions": QUESTIONS}


@app.post("/recommend")
def recommend(request: dict):
    platform = request.get("platform")
    answers = request.get("answers", [])
    required_accessibility = request.get("required_accessibility", [])
    max_age_rating = request.get("max_age_rating")
    played_titles = request.get("played_titles", [])
    vibe_text = request.get("vibe_text")
    vibe_weight = 3.0 if vibe_text else 0.0

    motivation_weights = score_answers(answers)

    results = recommend_games(
        platform=platform,
        motivation_weights=motivation_weights,
        required_accessibility=required_accessibility,
        max_age_rating=max_age_rating,
        played_titles=played_titles,
        limit=5,
        vibe_text=vibe_text,
        vibe_weight=vibe_weight,
    )

    for game in results:
        game["explanation"] = explain_recommendation(game)

    return {"weights": motivation_weights, "recommendations": results}


# this is to serve the frontend folder's other files as static assets under /static
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")