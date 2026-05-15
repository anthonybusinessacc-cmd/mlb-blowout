# MLB Blowout Tracker

A full-stack web app that monitors live MLB games, detects blowouts (large run differentials), sends SMS alerts via Twilio, and displays matched Kalshi prediction market data alongside each game.

---

## Overview

- **Backend**: FastAPI (Python) polls the MLB Stats API every 60 seconds, detects blowout conditions, fires Twilio SMS alerts, and caches Kalshi market data.
- **Frontend**: React + Vite single-page app that refreshes every 30 seconds, showing live scores, blowout badges, Kalshi market prices, and notification history.
- **Storage**: SQLite (no external database required).

---

## Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose
- A [Twilio](https://www.twilio.com/) account (for SMS alerts)
- A [Kalshi](https://www.kalshi.com/) account with API access (optional — app works without it)

---

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd mlb-blowout
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials (see sections below).

### 3. Start the app

```bash
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs (Swagger): http://localhost:8000/docs

---

## Getting Twilio Credentials

1. Sign up at [console.twilio.com](https://console.twilio.com)
2. From the Console Dashboard, copy your **Account SID** and **Auth Token**
3. Go to **Phone Numbers → Manage → Buy a Number** to get a Twilio number
4. Fill in your `.env`:
   ```
   TWILIO_ACCOUNT_SID=ACxxxxx...
   TWILIO_AUTH_TOKEN=your_token
   TWILIO_FROM_NUMBER=+15551234567
   ```
5. Set `phone_number` in the app's Settings tab to your personal number (must be verified in Twilio trial accounts)

---

## Getting a Kalshi API Key

1. Log in at [kalshi.com](https://www.kalshi.com)
2. Go to **Account → Settings → API**
3. Generate an API key and copy it
4. Fill in your `.env`:
   ```
   KALSHI_API_KEY=your_key_here
   ```

Kalshi market data is best-effort — the app functions normally if the API is unavailable or the key is missing.

---

## Settings

| Setting | Description |
|---|---|
| **Run Differential Threshold** | Minimum run lead to trigger a blowout alert (default: 5). |
| **SMS Phone Number** | Your mobile number to receive alerts. Include country code (+1 for US). |
| **Enable SMS Notifications** | Toggle SMS on/off without clearing your number. |

Settings are saved in SQLite and persist across restarts.

---

## How Kalshi Market Matching Works

The backend fetches all open MLB markets from the Kalshi API and attempts to match each market to a live game using team abbreviations extracted from the market ticker (e.g., `MLB-NYY-BOS` → `NYY`, `BOS`). Matching is case-insensitive and checks both abbreviation and full team name.

Once matched, markets are flagged as **Shifted** if:
- **Run line markets**: run differential ≥ 5
- **Moneyline markets**: run differential ≥ 7

Shifted markets indicate that blowout conditions may have materially moved the market away from its opening price, signaling potential value.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/games` | All today's games with scores and matched Kalshi markets |
| GET | `/blowouts` | Only games meeting the blowout threshold |
| GET | `/settings` | Current settings |
| POST | `/settings` | Update settings (JSON body) |
| GET | `/notifications` | Today's SMS notification log |

---

## Development (without Docker)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api/*` to `http://localhost:8000`.
