import httpx
from datetime import date
from typing import List, Dict, Any

MLB_BASE = "https://statsapi.mlb.com/api/v1"


async def fetch_today_games() -> List[Dict[str, Any]]:
    today_str = date.today().strftime("%Y-%m-%d")
    url = f"{MLB_BASE}/schedule"
    params = {
        "sportId": 1,
        "hydrate": "linescore,team",
        "date": today_str,
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        print(f"[mlb] Error fetching games: {e}")
        return []

    games = []
    try:
        dates = data.get("dates", [])
        if not dates:
            return []
        for game_data in dates[0].get("games", []):
            games.append(_parse_game(game_data))
    except Exception as e:
        print(f"[mlb] Error parsing games: {e}")
        return []

    return games


def _parse_game(game_data: dict) -> Dict[str, Any]:
    status_obj = game_data.get("status", {})
    status = status_obj.get("detailedState", "Unknown")

    linescore = game_data.get("linescore", {})
    inning = linescore.get("currentInning", 0) or 0
    inning_state = linescore.get("inningState", "") or ""
    if not inning_state and linescore.get("currentInningOrdinal"):
        inning_state = "Mid"

    teams = game_data.get("teams", {})
    away = teams.get("away", {})
    home = teams.get("home", {})

    away_team_info = away.get("team", {})
    home_team_info = home.get("team", {})

    away_team = away_team_info.get("name", "Away")
    home_team = home_team_info.get("name", "Home")

    # Abbreviation: try teamAbbreviation, then abbreviation, then first 3 of name
    away_abbr = (
        away_team_info.get("abbreviation")
        or away_team_info.get("teamAbbreviation")
        or away_team[:3].upper()
    )
    home_abbr = (
        home_team_info.get("abbreviation")
        or home_team_info.get("teamAbbreviation")
        or home_team[:3].upper()
    )

    # Scores
    away_score = away.get("score")
    home_score = home.get("score")
    if away_score is None:
        away_score = linescore.get("teams", {}).get("away", {}).get("runs", 0) or 0
    if home_score is None:
        home_score = linescore.get("teams", {}).get("home", {}).get("runs", 0) or 0
    away_score = int(away_score) if away_score is not None else 0
    home_score = int(home_score) if home_score is not None else 0

    run_diff = abs(home_score - away_score)
    if home_score > away_score:
        leading_team = home_team
    elif away_score > home_score:
        leading_team = away_team
    else:
        leading_team = ""

    # Game time
    game_datetime = game_data.get("gameDate", "")
    game_time = ""
    if game_datetime:
        try:
            from datetime import datetime, timezone, timedelta
            dt = datetime.fromisoformat(game_datetime.replace("Z", "+00:00"))
            pst = timezone(timedelta(hours=-7))  # PDT (UTC-7); change to -8 in winter
            dt_pst = dt.astimezone(pst)
            game_time = dt_pst.strftime("%I:%M %p PST")
        except Exception:
            game_time = game_datetime

    return {
        "game_pk": game_data.get("gamePk"),
        "status": status,
        "inning": inning,
        "inning_state": inning_state,
        "away_team": away_team,
        "away_team_abbr": away_abbr,
        "away_score": away_score,
        "home_team": home_team,
        "home_team_abbr": home_abbr,
        "home_score": home_score,
        "run_diff": run_diff,
        "leading_team": leading_team,
        "game_time": game_time,
    }
