"""Data Agent: agentic-style tool-calling for match intelligence.

Runs three tools (live-fixtures, form/H2H scraper, injury feed) via
the LangChain agent layer, then passes the aggregated structured brief
to an LLM to produce a plain-language summary suitable for TTS narration
and low-vision users.
"""
from __future__ import annotations
from typing import Dict, List
from datetime import datetime, timezone
import os
import uuid
import logging

from data import TEAMS_BY_CODE, VENUES, KICKOFFS, h2h
from ml_engine import predict_match
from scraper import (
    tool_fetch_fixture,
    tool_form_and_h2h,
    tool_injury_report,
)

log = logging.getLogger(__name__)




def gather_match_brief(match_id: str, home: str, away: str) -> Dict:
    """Run the 3 tools via LangChain and assemble a structured brief."""
    from lc_agent import run_agent, langchain_available, tool_names
    agent_out = run_agent(match_id, home, away)
    prediction = predict_match(home, away)

    return {
        "match_id": match_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fixture": agent_out["fixture"],
        "form_and_h2h": agent_out["form_and_h2h"],
        "injuries": agent_out["injuries"],
        "prediction": prediction,
        "agent": {
            "engine": agent_out.get("engine"),
            "langchain_available": langchain_available(),
            "tools": tool_names(),
        },
        "tool_calls": [
            {"id": str(uuid.uuid4())[:8], "tool": "fetch_fixture", "status": "ok",
             "ts": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4())[:8], "tool": "form_and_h2h", "status": "ok",
             "ts": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4())[:8], "tool": "injury_report", "status": "ok",
             "ts": datetime.now(timezone.utc).isoformat()},
        ],
    }


# --- Plain-language summariser (Claude Sonnet 4.5) ---------------------------
_FALLBACK_TEMPLATE = (
    "In the {round_name} clash, {home} face {away} at {venue}. "
    "Model favours {favourite} with a {fav_pct}% win probability, expecting a "
    "{xg_home}-{xg_away} scoreline. {home} arrive on {home_form} form, {away} on "
    "{away_form}. Head-to-head record stands at {a_wins}W-{draws}D-{b_wins}L in "
    "favour of {home}. Key men: {home_star} for {home}, {away_star} for {away}. "
    "{injury_note}"
)


def _fallback_summary(brief: Dict) -> str:
    p = brief["prediction"]
    home_name = brief["fixture"]["home"]
    away_name = brief["fixture"]["away"]
    fav = home_name if p["prob_home"] >= p["prob_away"] else away_name
    fav_pct = int(round(max(p["prob_home"], p["prob_away"]) * 100))
    form = brief["form_and_h2h"]
    inj = brief["injuries"]
    total_inj = len(inj["home_injuries"]) + len(inj["away_injuries"])
    injury_note = (
        f"Injury concerns include {', '.join(inj['home_injuries'] + inj['away_injuries'])}."
        if total_inj else "Both squads are near full strength."
    )
    round_map = {"R16": "Round of 16", "QF": "Quarter-final", "SF": "Semi-final", "F": "Final"}
    return _FALLBACK_TEMPLATE.format(
        round_name=round_map.get(brief["match_id"].split("-")[0], "knockout"),
        home=home_name, away=away_name,
        venue=brief["fixture"]["venue"],
        favourite=fav, fav_pct=fav_pct,
        xg_home=p["xg_home"], xg_away=p["xg_away"],
        home_form=form["home_form"], away_form=form["away_form"],
        a_wins=form["head_to_head"]["a_wins"], draws=form["head_to_head"]["draws"],
        b_wins=form["head_to_head"]["b_wins"],
        home_star=inj["home_star"], away_star=inj["away_star"],
        injury_note=injury_note,
    )


async def _llm_direct(system_msg: str, prompt: str, key: str) -> str:
    """Direct OpenAI-compatible API call — works with Google Gemini or OpenAI keys.

    Detects the key type:
      - sk-...          → OpenAI  (api.openai.com)
      - AIza...         → Gemini  (generativelanguage.googleapis.com OpenAI compat)
      - anything else   → tries OpenAI endpoint
    """
    import httpx
    if key.startswith("AIza"):
        url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        model = "gemini-2.0-flash"
    else:
        url = "https://api.openai.com/v1/chat/completions"
        model = "gpt-4o-mini"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 200,
        "temperature": 0.7,
    }
    async with httpx.AsyncClient(timeout=15.0) as c:
        r = await c.post(url, json=payload, headers={"Authorization": f"Bearer {key}"})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()


async def summarise_brief(brief: Dict) -> str:
    """Generate a TTS-friendly match preview.

    Chain: direct OpenAI-compatible API → template fallback.
    """
    key = os.environ.get("LLM_API_KEY", "").strip()
    if not key:
        return _fallback_summary(brief)

    system_msg = (
        "You are MatchSense, a football analytics narrator. Produce a warm, "
        "confident, 3-4 sentence spoken-word match preview for a World Cup 2026 "
        "knockout tie. Use natural sentences (no bullet points, no markdown, no "
        "emojis). Mention: (1) which side the model favours and the win %, "
        "(2) expected goals scoreline, (3) recent form and one head-to-head note, "
        "(4) one key player or injury note. Keep it under 90 words. This will be "
        "read aloud for low-vision fans so avoid jargon and abbreviations."
    )

    p = brief["prediction"]
    prompt = (
        f"Match: {brief['fixture']['home']} vs {brief['fixture']['away']} at {brief['fixture']['venue']}.\n"
        f"Model probabilities: home {int(p['prob_home']*100)}%, draw {int(p['prob_draw']*100)}%, away {int(p['prob_away']*100)}%.\n"
        f"Expected goals: {p['xg_home']} - {p['xg_away']}.\n"
        f"Form: home {brief['form_and_h2h']['home_form']}, away {brief['form_and_h2h']['away_form']}.\n"
        f"H2H: {brief['form_and_h2h']['head_to_head']}.\n"
        f"Home star: {brief['injuries']['home_star']}. Away star: {brief['injuries']['away_star']}.\n"
        f"Injuries: home {brief['injuries']['home_injuries']}, away {brief['injuries']['away_injuries']}.\n"
        "Write the preview now."
    )

    # try: direct OpenAI-compatible API (Gemini or OpenAI key)
    try:
        text = await _llm_direct(system_msg, prompt, key)
        if text:
            return text
    except Exception as e:
        log.warning("LLM summary failed, using template: %s", e)

    return _fallback_summary(brief)



LANG_NAMES = {"en": "English", "es": "Spanish", "pt": "Portuguese", "fr": "French"}


async def translate_summary(text: str, lang: str) -> str:
    """Translate an English brief to es/pt/fr. Returns original on failure."""
    lang = (lang or "en").lower()
    if lang == "en" or lang not in LANG_NAMES:
        return text
    key = os.environ.get("LLM_API_KEY", "").strip()
    if not key:
        return text

    system_msg = (
        f"You are a professional sports translator. Translate the following "
        f"English match preview into natural, spoken-word {LANG_NAMES[lang]}. "
        "Keep it under 90 words. Return ONLY the translation — no preamble."
    )

    # try: direct API
    try:
        out = await _llm_direct(system_msg, text, key)
        return out or text
    except Exception as e:
        log.warning("translation failed: %s", e)
    return text


# --- Agent activity log (in-memory ring buffer + MongoDB persistence) --------
_AGENT_LOG: List[Dict] = []
_MONGO_COLL = None  # set at startup by server.py


def bind_mongo(collection) -> None:
    """Called once from server startup to enable MongoDB log persistence."""
    global _MONGO_COLL
    _MONGO_COLL = collection


def log_event(level: str, tool: str, message: str) -> None:
    event = {
        "id": str(uuid.uuid4()),
        "ts": datetime.now(timezone.utc).isoformat(),
        "level": level, "tool": tool, "message": message,
    }
    _AGENT_LOG.append(event)
    del _AGENT_LOG[:-60]
    if _MONGO_COLL is not None:
        import asyncio
        async def _insert_log():
            try:
                await _MONGO_COLL.insert_one(dict(event))
            except Exception as ex:
                # Silently log warning, database logging is optional fallback
                log.warning(f"Async mongo log insert failed: {ex}")
        try:
            asyncio.create_task(_insert_log())
        except Exception as e:
            log.warning(f"Failed to spawn async mongo log task: {e}")


def recent_logs() -> List[Dict]:
    return list(reversed(_AGENT_LOG[-40:]))
