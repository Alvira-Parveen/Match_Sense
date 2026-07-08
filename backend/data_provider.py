"""Data-source abstraction. Swappable between mock and live API-Football.

`DATA_PROVIDER=mock` (default) — uses the bundled realistic dataset in data.py.
`DATA_PROVIDER=api_football` — hits api-sports.io using API_FOOTBALL_KEY.

Live adapter is currently STUBBED: when enabled without a valid key the server
falls back to mock automatically (never crashes the app).
"""
from __future__ import annotations
import os
import logging
from typing import Dict, List, Optional

import requests
from data import TEAMS, TEAMS_BY_CODE, BRACKET_STRUCTURE, VENUES, KICKOFFS, h2h
import cache

log = logging.getLogger(__name__)

_PROVIDER = os.environ.get("DATA_PROVIDER", "api_football").lower()
_API_KEY = os.environ.get("API_FOOTBALL_KEY", "").strip()

if _PROVIDER == "api_football" and not _API_KEY:
    log.warning(
        "DATA_PROVIDER=api_football but API_FOOTBALL_KEY is not set — "
        "falling back to mock data. Add API_FOOTBALL_KEY to your .env file."
    )
_WC_LEAGUE_ID = 1        # API-Football league id for the FIFA World Cup
_WC_SEASON = 2026
_LIVE_FIXTURES_TTL = 12 * 60 * 60   # 12 hours — burns ~2 API calls/day


def provider_name() -> str:
    if _PROVIDER == "api_football" and _API_KEY:
        return "api_football"
    return "mock"


def get_teams() -> List[Dict]:
    if provider_name() == "api_football":
        try:
            return _api_football_teams()
        except Exception as e:
            log.warning(f"api_football teams failed, falling back to mock: {e}")
    return TEAMS


def get_team(code: str) -> Optional[Dict]:
    for t in get_teams():
        if t["code"] == code:
            return t
    return TEAMS_BY_CODE.get(code)


def get_bracket_structure() -> Dict:
    return BRACKET_STRUCTURE


def get_h2h(a: str, b: str) -> Dict:
    return h2h(a, b)


def get_venue(match_id: str) -> str:
    return VENUES.get(match_id, "TBD")


def get_kickoff(match_id: str) -> str:
    return KICKOFFS.get(match_id, "TBD")


# ------- api-football live adapter (stub, safe fallback) ---------------------
_API_HOST = "https://v3.football.api-sports.io"


def _api_football_teams() -> List[Dict]:
    """Fetch team info from api-football. Endpoint returns lots — we normalise a
    subset. If anything fails, caller falls back to mock."""
    if not _API_KEY:
        raise RuntimeError("API_FOOTBALL_KEY not set")
    headers = {"x-apisports-key": _API_KEY}
    out: List[Dict] = []
    for mock in TEAMS:  # use codes we already know
        # api-football uses `code` (2/3 letter). We look up by the same code for demo.
        try:
            r = requests.get(
                f"{_API_HOST}/teams",
                params={"code": mock["code"], "season": 2026},
                headers=headers,
                timeout=6,
            )
            j = r.json()
            api_team = (j.get("response") or [{}])[0].get("team") or {}
            enriched = {**mock}
            # only override safe fields
            if api_team.get("name"):
                enriched["name"] = api_team["name"]
            out.append(enriched)
        except Exception:
            out.append(mock)
    return out


# --- Live R16 fixture sync (cached 12h → ~2 API calls / day) ----------------
async def fetch_live_fixtures(force: bool = False) -> Dict:
    """Fetch R16 fixtures from API-Football with MongoDB caching.

    Returns:
        {
          "source": "api_football" | "cache" | "mock",
          "last_synced": ISO string or None,
          "fixtures": [ {home, away, kickoff_utc, venue, status} ],
        }
    """
    c = cache.instance()
    cache_key = "af:r16-fixtures"

    if not force and c is not None:
        cached = await c.get(cache_key)
        if cached is not None:
            last = await c.last_sync(cache_key)
            return {"source": "cache", "last_synced": last, "fixtures": cached}

    if not _API_KEY:
        return {"source": "mock", "last_synced": None, "fixtures": _mock_fixtures()}

    try:
        headers = {"x-apisports-key": _API_KEY}
        r = requests.get(
            f"{_API_HOST}/fixtures",
            params={"league": _WC_LEAGUE_ID, "season": _WC_SEASON, "round": "Round of 16"},
            headers=headers,
            timeout=8,
        )
        j = r.json()
        fixtures = []
        for item in j.get("response", []):
            teams = item.get("teams", {}) or {}
            fixture = item.get("fixture", {}) or {}
            venue = (fixture.get("venue") or {}).get("name") or ""
            fixtures.append({
                "home": (teams.get("home") or {}).get("name"),
                "away": (teams.get("away") or {}).get("name"),
                "kickoff_utc": fixture.get("date"),
                "venue": venue,
                "status": (fixture.get("status") or {}).get("short"),
            })
        # Empty response is a valid signal (WC 2026 draw not yet in API); fall back to mock
        if not fixtures:
            fixtures = _mock_fixtures()
            src = "mock"
        else:
            src = "api_football"

        if c is not None:
            await c.set(cache_key, fixtures, _LIVE_FIXTURES_TTL)
        last = await c.last_sync(cache_key) if c else None
        return {"source": src, "last_synced": last, "fixtures": fixtures}
    except Exception as e:
        log.warning(f"live fixtures fetch failed: {e}")
        return {"source": "mock", "last_synced": None, "fixtures": _mock_fixtures()}


def _mock_fixtures() -> List[Dict]:
    """Fallback: derive fixtures from the bundled bracket."""
    out = []
    for m in BRACKET_STRUCTURE["R16"]:
        h, a = TEAMS_BY_CODE[m["home"]]["name"], TEAMS_BY_CODE[m["away"]]["name"]
        out.append({
            "home": h, "away": a,
            "kickoff_utc": KICKOFFS.get(m["id"]),
            "venue": VENUES.get(m["id"]),
            "status": "NS",
        })
    return out
