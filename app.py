from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import random
import os
import database as db_logic

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

game_sessions = {}

def read_template(file_name: str) -> str:
    path = os.path.join(BASE_DIR, "templates", file_name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def calculate_marks(level):
    """Marks logic: Level 11 reached (10 completed) = 55 marks"""
    completed = level - 1
    return (completed * (completed + 1)) // 2 if completed > 0 else 0

@app.get("/", response_class=HTMLResponse)
async def home():
    return read_template("index.html")

@app.get("/name-input", response_class=HTMLResponse)
async def name_input():
    return read_template("name.html")

@app.post("/start-game")
async def start_game(request: Request):
    form = await request.form()
    player_name = form.get("player_name", "").strip()
    if not player_name: return RedirectResponse("/name-input", status_code=303)
    
    # Check/Create player in Atlas
    if not db_logic.get_player(player_name):
        db_logic.create_player(player_name)

    game_sessions[player_name] = {"level": 1, "sequence": [random.randint(0, 99)]}
    return RedirectResponse(f"/game/{player_name}", status_code=303)

@app.get("/game/{player_name}", response_class=HTMLResponse)
async def game_page(player_name: str):
    if player_name not in game_sessions: return RedirectResponse("/", status_code=303)
    session = game_sessions[player_name]
    html = read_template("game.html")
    return html.replace("{{ player_name }}", player_name).replace("{{ level }}", str(session["level"])).replace("{{ sequence }}", ",".join(map(str, session["sequence"])))

@app.post("/submit-answer/{player_name}")
async def submit_answer(player_name: str, request: Request):
    session = game_sessions.get(player_name)
    form = await request.form()
    user_input = form.get("user_input", "").strip()
    
    try:
        user_seq = [int(x) for x in user_input.split()]
    except:
        user_seq = []

    if user_seq == session["sequence"]:
        session["level"] += 1
        session["sequence"] = [random.randint(0, 99) for _ in range(session["level"])]
        return {"success": True, "level": session["level"], "sequence": ",".join(map(str, session["sequence"]))}
    else:
        final_marks = calculate_marks(session["level"])
        db_logic.update_player_score(player_name, final_marks) # UPDATE ATLAS DB
        return {"success": False, "score": final_marks, "correct": " ".join(map(str, session["sequence"])), "user": user_input}

@app.get("/leaderboard", response_class=HTMLResponse)
async def show_leaderboard():
    players_data = db_logic.get_leaderboard()
    rows = ""
    for i, p in enumerate(players_data):
        # Use p['_id'] for name and p['score'] for marks as per your schema
        rows += f"<tr><td>{i+1}</td><td>{p['_id']}</td><td>{p['score']}</td></tr>"
    
    html = read_template("leaderboard.html")
    return html.replace("{{ leaderboard_rows }}", rows)

# SECRET ADMIN ROUTE TO REMOVE "SHOE"
@app.get("/delete-player/{name}")
async def remove_user(name: str):
    db_logic.delete_player(name)
    return {"status": "success", "message": f"Removed {name} from Atlas DB"}