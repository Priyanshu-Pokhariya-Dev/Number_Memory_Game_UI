from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import random
import os

from database import (
    get_player,
    create_player,
    update_player_score,
    get_leaderboard
)

app = FastAPI()

BASE_DIR = os.path.dirname(__file__)
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

game_sessions = {}


def read_template(file_name: str) -> str:
    with open(os.path.join(TEMPLATES_DIR, file_name), "r", encoding="utf-8") as f:
        return f.read()


def generate_sequence(length: int):
    return [random.randint(0, 100) for _ in range(length)]


@app.get("/", response_class=HTMLResponse)
async def home():
    return read_template("index.html")


@app.post("/start-game")
async def start_game(request: Request):
    try:
        form = await request.form()
        player_name = form.get("player_name", "").strip()

        # Redirect if name is empty
        if not player_name:
            return RedirectResponse("/", status_code=303)

        # Check if player exists in DB, create if not
        try:
            player = get_player(player_name)
            if not player:
                create_player(player_name)
        except Exception as db_error:
            # Return a friendly error if DB fails
            return HTMLResponse(
                f"<h2>Database error: {db_error}</h2>"
                f"<p>Please try again later.</p>", status_code=500
            )

        # Initialize game session
        game_sessions[player_name] = {
            "level": 1,
            "sequence": generate_sequence(1),
            "game_over": False
        }

        # Redirect to game page
        return RedirectResponse(f"/game/{player_name}", status_code=303)

    except Exception as e:
        # Catch any unexpected error
        return HTMLResponse(
            f"<h2>Unexpected server error: {e}</h2>"
            f"<p>Please try again later.</p>", status_code=500
        )



@app.get("/game/{player_name}", response_class=HTMLResponse)
async def game_page(player_name: str):
    if player_name not in game_sessions:
        return RedirectResponse("/", status_code=303)

    session = game_sessions[player_name]
    html = read_template("game.html")

    html = html.replace("{{ player_name }}", player_name)
    html = html.replace("{{ level }}", str(session["level"]))
    html = html.replace("{{ sequence }}", ",".join(map(str, session["sequence"])))
    html = html.replace("{{ game_over }}", str(session["game_over"]).lower())

    return html


@app.post("/submit-answer/{player_name}")
async def submit_answer(player_name: str, request: Request):
    if player_name not in game_sessions:
        return {"error": "Session expired"}

    session = game_sessions[player_name]
    form = await request.form()
    user_input = form.get("user_input", "").strip()

    try:
        user_sequence = [int(x) for x in user_input.split()]
    except ValueError:
        return end_game(player_name, session)

    if user_sequence != session["sequence"]:
        return end_game(player_name, session)

    # Correct answer → next level
    session["level"] += 1
    session["sequence"] = generate_sequence(session["level"])

    update_player_score(player_name, session["level"] - 1)

    return {
        "success": True,
        "level": session["level"],
        "sequence": ",".join(map(str, session["sequence"])),
        "message": f"Correct! Level {session['level']} starting."
    }


def end_game(player_name: str, session: dict):
    session["game_over"] = True
    score = session["level"] - 1
    update_player_score(player_name, score)

    return {
        "success": False,
        "level": score,
        "game_over": True,
        "message": f"Game Over! Final Score: {score} <br> The correct sequence was: {' '.join(map(str, session['sequence']))}"
    }


@app.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard():
    data = get_leaderboard()
    html = read_template("leaderboard.html")

    rows = ""
    for i, p in enumerate(data, 1):
        rows += f"<tr><td>{i}</td><td>{p['_id']}</td><td>{p['score']}</td></tr>"

    return html.replace("{{ leaderboard_rows }}", rows)


@app.get("/play-again/{player_name}")
async def play_again(player_name: str):
    """Allow player to play again."""
    if player_name in game_sessions:
        del game_sessions[player_name]

    game_sessions[player_name] = {
        "level": 1,
        "sequence": generate_sequence(1),
        "game_over": False,
        "message": ""
    }

    return RedirectResponse(url=f"/game/{player_name}", status_code=303)
