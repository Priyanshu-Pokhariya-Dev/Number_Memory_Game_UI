from pymongo import MongoClient
from datetime import datetime
import os

MONGODB_URL = os.getenv(
    "MONGODB_URL",
    "mongodb+srv://priyanshu:priyanshu1@project.7uihi2p.mongodb.net/?retryWrites=true&w=majority"
)
DATABASE_NAME = "number_memory_game"

client = MongoClient(MONGODB_URL)
db = client[DATABASE_NAME]
players = db["players"]


def get_player(name: str):
    return players.find_one({"_id": name})


def create_player(name: str):
    players.insert_one({
        "_id": name,
        "score": 0,
        "last_played": datetime.utcnow()
    })


def update_player_score(name: str, score: int):
    player = get_player(name)
    if not player:
        create_player(name)
        player = get_player(name)

    if score > player.get("score", 0):
        players.update_one(
            {"_id": name},
            {"$set": {"score": score, "last_played": datetime.utcnow()}}
        )


def get_leaderboard():
    return list(players.find().sort("score", -1))
