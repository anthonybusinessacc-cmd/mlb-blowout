import os
import re
import httpx
from typing import List, Dict, Any

KALSHI_BASE = "https://trading-api.kalshi.com/trade-api/v2"


def _get_headers() -> dict:
    api_key = os.environ.get("KALSHI_API_KEY", "")
    if api_key:
        return {"Authorization": f"Bearer {api_key}"}
    return {}


def _parse_market_type(title: str) -> str:
    t = title.lower()
    if "moneyline" in t:
        return "moneyline"
    if "run line" in t or "runline" in t or "run-line" in t:
        return "runline"
    if "total" in t or "over" in t or "under" in t:
        return "total"
    return "other"


def _extract_teams(ticker: str, title: str) -> List[str]:
    """Extract team abbreviations from ticker like MLB-NYY-BOS or from title."""
    teams = []
    # Try ticker pattern: MLB-TEAM1-TEAM2
    ticker_match = re.findall(r"MLB-([A-Z]{2,5})-([A-Z]{2,5})", ticker)
    if ticker_match:
        teams = list(ticker_match[0])
        return teams

    # Try to find abbreviations in ticker (3 uppercase letters)
    abbr_matches = re.findall(r"\b([A-Z]{2,5})\b", ticker)
    # Filter out generic words
    skip = {"MLB", "WIN", "THE", "RUN", "LINE", "OVER", "UNDER", "YES", "NO"}
    filtered = [a for a in abbr_matches if a not in skip]
    if len(filtered) >= 2:
        return filtered[:2]

    # Fallback: try title
    title_abbr = re.findall(r"\b([A-Z]{2,5})\b", title)
    filtered_title = [a for a in title_abbr if a not in skip]
    if len(filtered_title) >= 2:
        return filtered_title[:2]

    return teams


def _parse_market(m: dict) -> Dict[str, Any]:
    ticker = m.get("ticker", "")
    title = m.get("title", "") or m.get("subtitle", "") or ticker

    yes_bid = float(m.get("yes_bid", 0) or 0)
    yes_ask = float(m.get("yes_ask", 0) or 0)
    no_bid = float(m.get("no_bid", 0) or 0)
    no_ask = float(m.get("no_ask", 0) or 0)

    # Convert cents to decimal if values > 1
    for val in [yes_bid, yes_ask, no_bid, no_ask]:
        if val > 1:
            yes_bid /= 100
            yes_ask /= 100
            no_bid /= 100
            no_ask /= 100
            break

    volume = int(m.get("volume", 0) or 0)

    return {
        "ticker": ticker,
        "title": title,
        "market_type": _parse_market_type(title),
        "yes_bid": round(yes_bid, 4),
        "no_bid": round(no_bid, 4),
        "yes_ask": round(yes_ask, 4),
        "no_ask": round(no_ask, 4),
        "volume": volume,
        "game_pk": None,
        "teams": _extract_teams(ticker, title),
        "is_shifted": False,
    }


async def fetch_mlb_markets() -> List[Dict[str, Any]]:
    headers = _get_headers()
    markets = []

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Primary attempt: markets endpoint
            resp = await client.get(
                f"{KALSHI_BASE}/markets",
                params={"status": "open", "series_ticker": "MLB"},
                headers=headers,
            )
            if resp.status_code in (401, 403):
                print(f"[kalshi] Auth error ({resp.status_code}), returning empty markets")
                return []
            if resp.status_code == 200:
                data = resp.json()
                raw_markets = data.get("markets", [])
                if raw_markets:
                    markets = [_parse_market(m) for m in raw_markets]

            # If empty, try events endpoint
            if not markets:
                resp2 = await client.get(
                    f"{KALSHI_BASE}/events",
                    params={"series_ticker": "MLB"},
                    headers=headers,
                )
                if resp2.status_code == 200:
                    data2 = resp2.json()
                    events = data2.get("events", [])
                    for event in events:
                        for m in event.get("markets", []):
                            markets.append(_parse_market(m))

    except Exception as e:
        print(f"[kalshi] Error fetching markets: {e}")
        return []

    return markets


def match_markets_to_games(games: list, markets: list) -> list:
    """Match markets to games by team abbreviation, and flag shifted markets."""
    for market in markets:
        teams = market.get("teams", [])
        if len(teams) < 2:
            continue
        t1 = teams[0].upper()
        t2 = teams[1].upper()

        for game in games:
            away_abbr = (game.get("away_team_abbr") or "").upper()
            home_abbr = (game.get("home_team_abbr") or "").upper()
            away_name = (game.get("away_team") or "").upper()
            home_name = (game.get("home_team") or "").upper()

            def matches(token: str) -> bool:
                return (
                    token == away_abbr
                    or token == home_abbr
                    or token in away_name
                    or token in home_name
                )

            if matches(t1) and matches(t2):
                market["game_pk"] = game["game_pk"]
                run_diff = game.get("run_diff", 0)
                mtype = market.get("market_type", "other")
                if mtype == "runline" and run_diff >= 5:
                    market["is_shifted"] = True
                elif mtype == "moneyline" and run_diff >= 7:
                    market["is_shifted"] = True
                break

    return markets
