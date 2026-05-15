import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from database import (
    add_notification,
    get_settings,
    get_today_notifications,
    has_notified,
    init_db,
    update_settings,
)
from kalshi import fetch_mlb_markets, match_markets_to_games
from mlb import fetch_today_games

# ---------------------------------------------------------------------------
# Module-level cache
# ---------------------------------------------------------------------------
_cache_lock = asyncio.Lock()
_games_cache: List[Dict[str, Any]] = []
_markets_cache: List[Dict[str, Any]] = []

POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "60"))


# ---------------------------------------------------------------------------
# Twilio helper
# ---------------------------------------------------------------------------
def send_sms(to_number: str, message: str):
    try:
        from twilio.rest import Client

        account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
        from_number = os.environ.get("TWILIO_FROM_NUMBER", "")

        if not account_sid or not auth_token or not from_number:
            print("[twilio] Missing credentials, skipping SMS")
            return

        client = Client(account_sid, auth_token)
        client.messages.create(body=message, from_=from_number, to=to_number)
        print(f"[twilio] SMS sent to {to_number}: {message}")
    except Exception as e:
        print(f"[twilio] Error sending SMS: {e}")


# ---------------------------------------------------------------------------
# Background polling task
# ---------------------------------------------------------------------------
async def poll_loop():
    global _games_cache, _markets_cache

    while True:
        try:
            games = await fetch_today_games()
            markets = await fetch_mlb_markets()

            # Match markets to games
            if markets and games:
                markets = match_markets_to_games(games, markets)

            async with _cache_lock:
                _games_cache = games
                _markets_cache = markets

            # Blowout detection + SMS
            settings = get_settings()
            threshold = settings.get("threshold", 5)
            sms_enabled = settings.get("sms_enabled", False)
            phone_number = settings.get("phone_number", "")

            for game in games:
                status = game.get("status", "")
                run_diff = game.get("run_diff", 0)
                game_pk = str(game.get("game_pk", ""))
                is_active = "progress" in status.lower() or "final" in status.lower()

                if is_active and run_diff >= threshold and not has_notified(game_pk):
                    away = game.get("away_team", "Away")
                    home = game.get("home_team", "Home")
                    away_score = game.get("away_score", 0)
                    home_score = game.get("home_score", 0)
                    leading = game.get("leading_team", "")
                    inning = game.get("inning", 0)
                    inning_state = game.get("inning_state", "")

                    msg = (
                        f"BLOWOUT ALERT: {away} {away_score} - {home} {home_score} "
                        f"({inning_state} {inning}). {leading} leads by {run_diff}."
                    )
                    add_notification(game_pk, msg)

                    if sms_enabled and phone_number:
                        send_sms(phone_number, msg)
                    else:
                        print(f"[poll] Blowout detected (SMS disabled): {msg}")

        except Exception as e:
            print(f"[poll] Unhandled error in poll_loop: {e}")

        await asyncio.sleep(POLL_INTERVAL)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task = asyncio.create_task(poll_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="MLB Blowout Tracker", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/games")
async def get_games():
    async with _cache_lock:
        games = list(_games_cache)
        markets = list(_markets_cache)

    # Attach matching kalshi markets to each game
    markets_by_game: Dict[int, List[Dict]] = {}
    for m in markets:
        gk = m.get("game_pk")
        if gk is not None:
            markets_by_game.setdefault(gk, []).append(m)

    result = []
    for game in games:
        g = dict(game)
        g["kalshi_markets"] = markets_by_game.get(g.get("game_pk"), [])
        result.append(g)

    return result


@app.get("/blowouts")
async def get_blowouts():
    settings = get_settings()
    threshold = settings.get("threshold", 5)

    async with _cache_lock:
        games = list(_games_cache)
        markets = list(_markets_cache)

    markets_by_game: Dict[int, List[Dict]] = {}
    for m in markets:
        gk = m.get("game_pk")
        if gk is not None:
            markets_by_game.setdefault(gk, []).append(m)

    result = []
    for game in games:
        status = game.get("status", "")
        run_diff = game.get("run_diff", 0)
        is_active = "progress" in status.lower() or "final" in status.lower()
        if is_active and run_diff >= threshold:
            g = dict(game)
            g["kalshi_markets"] = markets_by_game.get(g.get("game_pk"), [])
            result.append(g)

    result.sort(key=lambda g: g["run_diff"], reverse=True)
    return result


@app.get("/settings")
async def get_settings_endpoint():
    return get_settings()


@app.post("/settings")
async def update_settings_endpoint(data: dict):
    allowed = {"threshold", "phone_number", "sms_enabled"}
    filtered = {k: v for k, v in data.items() if k in allowed}
    if not filtered:
        raise HTTPException(status_code=400, detail="No valid settings fields provided")
    update_settings(filtered)
    return get_settings()


@app.get("/notifications")
async def get_notifications():
    return get_today_notifications()
