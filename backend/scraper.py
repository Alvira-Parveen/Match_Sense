"""Real HTTP scraper for agent tools.

Priority chain for each tool:
  1. football-data.org  (requires FOOTBALL_DATA_KEY env var — free account)
  2. API-Football       (requires API_FOOTBALL_KEY env var — also free tier)
  3. TheSportsDB        (free, no key needed)
  4. Static data.py    (always available — never crashes)

All network calls use httpx with a 6-second timeout and in-memory TTL cache
so the app stays well within free-tier rate limits even without a CDN.
"""
from __future__ import annotations

import os
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple

try:
    import httpx
    _HTTPX_OK = True
except ImportError:
    _HTTPX_OK = False

from data import TEAMS_BY_CODE, VENUES, KICKOFFS, h2h as static_h2h

log = logging.getLogger(__name__)

# ── credentials ──────────────────────────────────────────────────────────────
_FD_KEY  = os.environ.get("FOOTBALL_DATA_KEY", "").strip()   # football-data.org
_AF_KEY  = os.environ.get("API_FOOTBALL_KEY",  "").strip()   # api-football.com

_FD_BASE = "https://api.football-data.org/v4"
_AF_BASE = "https://v3.football.api-sports.io"
_TSDB    = "https://www.thesportsdb.com/api/v1/json/3"

_TIMEOUT = 6.0   # seconds

# ── in-memory TTL cache (1-hour for scraped data) ────────────────────────────
_SCRAPE_CACHE: Dict[str, Tuple[object, datetime]] = {}
_CACHE_TTL_S  = 3600  # 1 hour


def _cache_get(key: str) -> Optional[object]:
    entry = _SCRAPE_CACHE.get(key)
    if entry:
        val, ts = entry
        if (datetime.now(timezone.utc) - ts).total_seconds() < _CACHE_TTL_S:
            return val
    return None


def _cache_set(key: str, val: object) -> None:
    _SCRAPE_CACHE[key] = (val, datetime.now(timezone.utc))


# ── football-data.org helpers ─────────────────────────────────────────────────

def _fd_headers() -> Dict[str, str]:
    return {"X-Auth-Token": _FD_KEY} if _FD_KEY else {}


def _fd_get(path: str) -> Optional[dict]:
    """Synchronous GET against football-data.org.  Returns parsed JSON or None."""
    if not _HTTPX_OK:
        return None
    try:
        with httpx.Client(timeout=_TIMEOUT) as c:
            r = c.get(f"{_FD_BASE}{path}", headers=_fd_headers())
            if r.status_code == 200:
                return r.json()
            log.debug("fd.org %s → %s", path, r.status_code)
    except Exception as e:
        log.debug("fd.org request failed: %s", e)
    return None


def _af_get(path: str, params: dict = None) -> Optional[dict]:
    """Synchronous GET against api-football.com.  Returns parsed JSON or None."""
    if not _AF_KEY or not _HTTPX_OK:
        return None
    try:
        with httpx.Client(timeout=_TIMEOUT) as c:
            r = c.get(
                f"{_AF_BASE}{path}",
                headers={"x-apisports-key": _AF_KEY},
                params=params or {},
            )
            if r.status_code == 200:
                return r.json()
            log.debug("api-football %s → %s", path, r.status_code)
    except Exception as e:
        log.debug("api-football request failed: %s", e)
    return None


def _tsdb_get(path: str, params: dict = None) -> Optional[dict]:
    """Synchronous GET against TheSportsDB (free, no key)."""
    if not _HTTPX_OK:
        return None
    try:
        with httpx.Client(timeout=_TIMEOUT) as c:
            r = c.get(f"{_TSDB}/{path}", params=params or {})
            if r.status_code == 200:
                return r.json()
            log.debug("tsdb %s → %s", path, r.status_code)
    except Exception as e:
        log.debug("tsdb request failed: %s", e)
    return None


# ── team-name → TSDB team lookup ──────────────────────────────────────────────
_TSDB_ID_CACHE: Dict[str, Optional[str]] = {}


def _tsdb_team_id(team_name: str) -> Optional[str]:
    if team_name in _TSDB_ID_CACHE:
        return _TSDB_ID_CACHE[team_name]
    j = _tsdb_get("searchteams.php", {"t": team_name})
    tid = None
    if j and j.get("teams"):
        # prefer international-football entries
        for t in j["teams"]:
            if "international" in (t.get("strSport") or "").lower() or \
               "football" in (t.get("strSport") or "").lower():
                tid = t.get("idTeam")
                break
        if not tid:
            tid = j["teams"][0].get("idTeam")
    _TSDB_ID_CACHE[team_name] = tid
    return tid


# ── form helpers ──────────────────────────────────────────────────────────────

def _form_from_results(results: List[str]) -> str:
    """Convert a list like ['W','D','L','W','W'] → 'WDLWW' (max 5)."""
    return "".join(results[-5:]) if results else "WDWDW"


def _form_score(form_str: str) -> float:
    pts = {"W": 3, "D": 1, "L": 0}
    total = sum(pts.get(c, 0) for c in form_str)
    return round(total / (3 * max(1, len(form_str))), 3)


def _fetch_form_fd(team_name: str, code: str) -> Optional[str]:
    """Try football-data.org for the team's last 5 results."""
    # We need the FD team id — look it up from competition participants
    ckey = f"fd:form:{code}"
    cached = _cache_get(ckey)
    if cached is not None:
        return cached  # type: ignore

    # Try WC 2026 competition
    j = _fd_get("/competitions/WC/standings?season=2026")
    if not j:
        j = _fd_get("/competitions/WC/teams?season=2026")
    if not j:
        return None

    # Extract team id
    team_id = None
    for section in j.get("standings", [j]):
        for entry in (section.get("table") if isinstance(section, dict) else [section]):
            t = (entry.get("team") or {}) if isinstance(entry, dict) else {}
            if code.lower() in (t.get("tla") or "").lower() or \
               team_name.lower() in (t.get("name") or "").lower():
                team_id = t.get("id")
                break
        if team_id:
            break

    if not team_id:
        return None

    mj = _fd_get(f"/teams/{team_id}/matches?status=FINISHED&limit=5")
    if not mj or not mj.get("matches"):
        return None

    results = []
    for m in mj["matches"]:
        score = m.get("score", {})
        ft = score.get("fullTime", {})
        ht_id = (m.get("homeTeam") or {}).get("id")
        at_id = (m.get("awayTeam") or {}).get("id")
        hw, aw = ft.get("home", 0) or 0, ft.get("away", 0) or 0
        if team_id == ht_id:
            results.append("W" if hw > aw else ("D" if hw == aw else "L"))
        else:
            results.append("W" if aw > hw else ("D" if aw == hw else "L"))
    form = _form_from_results(results)
    _cache_set(ckey, form)
    return form


def _fetch_form_af(team_name: str, code: str) -> Optional[str]:
    """Try api-football.com for recent form."""
    ckey = f"af:form:{code}"
    cached = _cache_get(ckey)
    if cached is not None:
        return cached  # type: ignore

    # search for team id
    tj = _af_get("/teams", {"search": team_name})
    if not tj or not tj.get("response"):
        return None
    team_id = tj["response"][0]["team"]["id"]

    mj = _af_get("/fixtures", {"team": team_id, "last": 5})
    if not mj or not mj.get("response"):
        return None

    results = []
    for fix in mj["response"]:
        goals = fix.get("goals", {})
        teams = fix.get("teams", {})
        is_home = teams.get("home", {}).get("id") == team_id
        hw, aw = goals.get("home", 0) or 0, goals.get("away", 0) or 0
        if is_home:
            results.append("W" if hw > aw else ("D" if hw == aw else "L"))
        else:
            results.append("W" if aw > hw else ("D" if aw == hw else "L"))
    form = _form_from_results(results)
    _cache_set(ckey, form)
    return form


def _fetch_form_tsdb(team_name: str, code: str) -> Optional[str]:
    """Try TheSportsDB free tier for recent results."""
    ckey = f"tsdb:form:{code}"
    cached = _cache_get(ckey)
    if cached is not None:
        return cached  # type: ignore

    tid = _tsdb_team_id(team_name)
    if not tid:
        return None

    j = _tsdb_get(f"eventslast.php?id={tid}")
    if not j or not j.get("results"):
        return None

    results = []
    for ev in j["results"][-5:]:
        ht_id  = ev.get("idHomeTeam")
        hw_str = ev.get("intHomeScore") or "0"
        aw_str = ev.get("intAwayScore") or "0"
        try:
            hw, aw = int(hw_str), int(aw_str)
        except ValueError:
            continue
        is_home = ht_id == tid
        if is_home:
            results.append("W" if hw > aw else ("D" if hw == aw else "L"))
        else:
            results.append("W" if aw > hw else ("D" if aw == hw else "L"))
    if not results:
        return None
    form = _form_from_results(results)
    _cache_set(ckey, form)
    return form


def _resolve_form(team_name: str, code: str, fallback_form: str) -> str:
    """Try all providers in order, fall back to static."""
    for fn in (_fetch_form_fd, _fetch_form_af, _fetch_form_tsdb):
        try:
            form = fn(team_name, code)
            if form:
                log.info("form for %s fetched via %s: %s", code, fn.__name__, form)
                return form
        except Exception as exc:
            log.debug("%s failed for %s: %s", fn.__name__, code, exc)
    log.debug("form for %s: using static fallback %s", code, fallback_form)
    return fallback_form


# ── Public tool functions (same signature as agent.py originals) ──────────────

def tool_fetch_fixture(match_id: str, home: str, away: str) -> Dict:
    """Fetch fixture metadata. Tries live APIs; falls back to static data."""
    ckey = f"fixture:{match_id}"
    cached = _cache_get(ckey)
    if cached is not None:
        return cached  # type: ignore

    home_team = TEAMS_BY_CODE[home]
    away_team = TEAMS_BY_CODE[away]

    result = {
        "tool": "fetch_fixture",
        "match_id": match_id,
        "venue": VENUES.get(match_id, "TBD"),
        "kickoff": KICKOFFS.get(match_id, "TBD"),
        "home": home_team["name"],
        "away": away_team["name"],
        "source": "static",
    }

    # Try football-data.org for live kickoff/venue
    if _FD_KEY:
        try:
            j = _fd_get("/competitions/WC/matches?season=2026&stage=ROUND_OF_16")
            if j and j.get("matches"):
                h_name = home_team["name"].lower()
                a_name = away_team["name"].lower()
                for m in j["matches"]:
                    ht = (m.get("homeTeam") or {}).get("name", "").lower()
                    at = (m.get("awayTeam") or {}).get("name", "").lower()
                    if h_name in ht or a_name in at:
                        venue_info = m.get("venue") or {}
                        utc_dt    = m.get("utcDate") or ""
                        if utc_dt:
                            result["kickoff"] = utc_dt
                        if venue_info:
                            result["venue"] = venue_info if isinstance(venue_info, str) else VENUES.get(match_id, "TBD")
                        result["source"] = "football-data.org"
                        break
        except Exception as e:
            log.debug("fixture fd fetch failed: %s", e)

    _cache_set(ckey, result)
    return result


def tool_form_and_h2h(home: str, away: str) -> Dict:
    """Fetch recent form for both teams. Falls back gracefully to static."""
    ckey = f"form:{home}:{away}"
    cached = _cache_get(ckey)
    if cached is not None:
        return cached  # type: ignore

    home_team = TEAMS_BY_CODE[home]
    away_team = TEAMS_BY_CODE[away]

    home_form = _resolve_form(home_team["name"], home, home_team["form"])
    away_form = _resolve_form(away_team["name"], away, away_team["form"])

    result = {
        "tool": "form_and_h2h",
        "home_form": home_form,
        "away_form": away_form,
        "head_to_head": static_h2h(home, away),
        "source": "live" if home_form != home_team["form"] else "static",
    }
    _cache_set(ckey, result)
    return result


def tool_injury_report(home: str, away: str) -> Dict:
    """Fetch injury / squad news. Falls back to static squad data."""
    ckey = f"injury:{home}:{away}"
    cached = _cache_get(ckey)
    if cached is not None:
        return cached  # type: ignore

    home_team = TEAMS_BY_CODE[home]
    away_team = TEAMS_BY_CODE[away]

    home_injuries: List[str] = list(home_team.get("injuries", []))
    away_injuries: List[str] = list(away_team.get("injuries", []))
    source = "static"

    # Try TheSportsDB for latest injuries (no key needed)
    for code, team, injuries_list in [
        (home, home_team, home_injuries),
        (away, away_team, away_injuries),
    ]:
        try:
            tid = _tsdb_team_id(team["name"])
            if tid:
                j = _tsdb_get(f"eventsnextleague.php?id={tid}")
                # TSDB doesn't have injury feeds natively; use as availability proxy
                # Only update if live data disagrees significantly with static
                pass  # placeholder for richer API integration
        except Exception as e:
            log.debug("injury fetch failed for %s: %s", code, e)

    result = {
        "tool": "injury_report",
        "home_injuries": home_injuries,
        "away_injuries": away_injuries,
        "home_star": home_team["star"],
        "away_star": away_team["star"],
        "source": source,
    }
    _cache_set(ckey, result)
    return result


def clear_cache() -> None:
    """Called by scheduler to force fresh data on next request."""
    _SCRAPE_CACHE.clear()
    log.info("scraper cache cleared")
