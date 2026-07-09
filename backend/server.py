"""MatchSense — FastAPI backend serving agent, ensemble, Monte-Carlo & TTS layers."""
from __future__ import annotations
from fastapi import FastAPI, APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import os
import logging
import uuid
import json
import asyncio

# load env before any downstream imports
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from data import TEAMS, TEAMS_BY_CODE, BRACKET_STRUCTURE
from ml_engine import predict_match, monte_carlo, expected_bracket
from agent import (
    gather_match_brief, summarise_brief, translate_summary,
    recent_logs, log_event, bind_mongo,
)
from tts_service import synthesize_speech_base64
import xgb_model
from data_provider import provider_name, fetch_live_fixtures
import cache as api_cache
import scheduler as bg_scheduler

# ---- Mongo -----------------------------------------------------------------
mongo_url = os.environ["MONGO_URL"]
db_name = os.environ["DB_NAME"]
client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=2000)
db = client[db_name]

# ---- App -------------------------------------------------------------------
app = FastAPI(title="MatchSense API")
api = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("matchsense")


# ---- Simple in-memory cache for expensive endpoints ------------------------
_CACHE: dict = {}


# ---- Models ----------------------------------------------------------------
class FavoritePayload(BaseModel):
    session_id: str = Field(..., min_length=1)
    team_code: str = Field(..., min_length=2, max_length=4)


class ResultPayload(BaseModel):
    match_id: str = Field(..., min_length=1, max_length=8)
    winner_code: str = Field(..., min_length=2, max_length=4)


async def _load_results() -> dict:
    """Load all admin-marked actual results from Mongo, falling back to local JSON on failure."""
    out = {}
    try:
        docs = await asyncio.wait_for(
            db.actual_results.find({}, {"_id": 0}).to_list(100),
            timeout=2.0
        )
        for doc in docs:
            out[doc["match_id"]] = doc["winner_code"]
        return out
    except Exception as e:
        logger.warning(f"MongoDB connection failed, falling back to local actual_results.json: {e}")
    
    # Local JSON fallback
    json_path = os.path.join(os.path.dirname(__file__), "actual_results.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as f:
                return json.load(f)
        except Exception as je:
            logger.warning(f"Failed to read local actual_results.json: {je}")
    return out


def _require_admin(x_admin_key: str | None):
    expected = os.environ.get("ADMIN_KEY")
    if not expected or x_admin_key != expected:
        raise HTTPException(401, "Invalid admin key")


# ---- Routes ----------------------------------------------------------------
@api.get("/")
async def root():
    from lc_agent import langchain_available, tool_names, llm_routed_enabled
    return {
        "message": "MatchSense API",
        "version": "1.3.0",
        "tournament": "FIFA World Cup 2026 — Knockout",
        "data_provider": provider_name(),
        "xgb_ready": xgb_model.is_ready(),
        "shap_ready": xgb_model.shap_ready(),
        "langchain_ready": langchain_available(),
        "langchain_llm_routed": llm_routed_enabled(),
        "langchain_tools": tool_names(),
        "xgb_feature_importance": xgb_model.feature_importance(),
    }


@api.get("/teams")
async def get_teams():
    return {"teams": TEAMS}


@api.get("/bracket")
async def get_bracket():
    """Full bracket with model-predicted advancement (favourite path).

    Any admin-marked actual results are frozen — those matches carry `is_actual: true`."""
    results = await _load_results()
    log_event("INFO", "bracket-builder", f"Assembling bracket ({len(results)} actual results frozen)")
    data = expected_bracket(results=results)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "structure": BRACKET_STRUCTURE,
        "matches": data["matches"],
        "predicted_champion": data["champion"],
        "predicted_third_place": data.get("third_place"),
        "actual_results": results,
    }


@api.get("/predict/{match_id}")
async def api_predict(match_id: str):
    match = _find_match(match_id)
    if not match:
        raise HTTPException(404, f"Match {match_id} not found")
    log_event("INFO", "ensemble", f"Ensemble prediction requested for {match_id}")
    pred = predict_match(match["home"], match["away"])
    return {
        "match_id": match_id,
        "home_team": TEAMS_BY_CODE[match["home"]],
        "away_team": TEAMS_BY_CODE[match["away"]],
        "prediction": pred,
    }


@api.get("/simulate")
async def api_simulate(runs: int = 10000):
    runs = max(1000, min(50000, runs))
    results = await _load_results()
    results_key = "-".join(f"{k}:{v}" for k, v in sorted(results.items())) if results else "clean"
    cache_key = f"mc-{runs}-{results_key}"
    if cache_key in _CACHE:
        return _CACHE[cache_key]
    log_event("INFO", "monte-carlo", f"Running Monte Carlo with {runs} iterations, {len(results)} frozen matches")
    result = monte_carlo(n_runs=runs, results=results)
    _CACHE[cache_key] = result
    log_event("INFO", "monte-carlo", f"Simulation complete — top champion pick: {result['teams'][0]['name']} @ {result['teams'][0]['prob_champion']*100:.1f}%")
    return result


@api.get("/match-brief/{match_id}")
async def api_match_brief(match_id: str):
    match = _find_match(match_id)
    if not match:
        raise HTTPException(404, f"Match {match_id} not found")

    log_event("INFO", "agent", f"Data agent gathering brief for {match_id}")
    brief = gather_match_brief(match_id, match["home"], match["away"])
    log_event("INFO", "agent", "Tools returned OK — invoking Claude Sonnet 4.5 for narration")
    summary = await summarise_brief(brief)
    brief["summary"] = summary
    log_event("INFO", "agent", f"Brief ready for {match_id} ({len(summary)} chars)")
    return brief


# language → best-fit OpenAI TTS voice
_LANG_VOICE = {"en": "nova", "es": "onyx", "pt": "shimmer", "fr": "echo"}


@api.get("/audio-summary/{match_id}")
async def api_audio_summary(match_id: str, voice: str | None = None, lang: str = "en"):
    match = _find_match(match_id)
    if not match:
        raise HTTPException(404, f"Match {match_id} not found")

    lang = (lang or "en").lower()
    if lang not in ("en", "es", "pt", "fr"):
        lang = "en"
    if not voice:
        voice = _LANG_VOICE.get(lang, "nova")

    cache_key = f"audio-{match_id}-{voice}-{lang}"
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    log_event("INFO", "tts", f"Generating audio briefing for {match_id} (voice={voice}, lang={lang})")
    brief = gather_match_brief(match_id, match["home"], match["away"])
    summary_en = await summarise_brief(brief)
    summary = await translate_summary(summary_en, lang) if lang != "en" else summary_en
    audio_b64 = await synthesize_speech_base64(summary, voice=voice)

    payload = {
        "match_id": match_id,
        "voice": voice,
        "lang": lang,
        "summary_text": summary,
        "summary_text_en": summary_en,
        "audio_base64": audio_b64,
        "audio_available": audio_b64 is not None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    if audio_b64:
        _CACHE[cache_key] = payload
    log_event("INFO", "tts", "Audio generated" if audio_b64 else "TTS unavailable, returning text-only")
    return payload


@api.get("/team/{code}")
async def api_team(code: str):
    """Full team detail — profile, form, injuries, championship prob, path."""
    team = TEAMS_BY_CODE.get(code.upper())
    if not team:
        raise HTTPException(404, f"Team {code} not found")

    # championship probabilities (from cached MC or fresh 5k run)
    sim = _CACHE.get("mc-10000") or _CACHE.get("mc-5000")
    if not sim:
        sim = monte_carlo(n_runs=5000)
        _CACHE["mc-5000"] = sim
    team_sim = next((t for t in sim["teams"] if t["code"] == code.upper()), None)

    # Predicted path from expected bracket
    bracket = _CACHE.get("bracket")
    if not bracket:
        eb = expected_bracket()
        bracket = {"matches": eb["matches"], "predicted_champion": eb["champion"]}
        _CACHE["bracket"] = bracket
    path = []
    winner_of = {m["id"]: m.get("predicted_winner") for m in bracket["matches"]}
    for m in bracket["matches"]:
        if m.get("home") == code.upper() or m.get("away") == code.upper():
            path.append({
                "match_id": m["id"],
                "round": m["round"],
                "home": m.get("home"),
                "away": m.get("away"),
                "predicted_winner": m.get("predicted_winner"),
                "prediction": m.get("prediction"),
            })

    return {
        "team": team,
        "championship": team_sim,
        "predicted_path": path,
        "advances_to_champion": bracket["predicted_champion"] == code.upper(),
    }


@api.get("/agent-logs")
async def api_agent_logs():
    return {"logs": recent_logs()}


@api.get("/scheduler/status")
async def api_scheduler_status():
    """Background job schedule — next run times and recent history."""
    return bg_scheduler.status()


# ---- Live sync (cached API-Football fixtures) ------------------------------
@api.get("/live/fixtures")
async def api_live_fixtures():
    """Cached R16 fixtures from API-Football. TTL 12h → ~2 API calls / day."""
    data = await fetch_live_fixtures(force=False)
    log_event("INFO", "live-sync", f"Fixtures served from {data['source']}")
    return data


@api.post("/admin/live/refresh")
async def api_live_refresh(x_admin_key: str = Header(default=None)):
    """Force a live re-sync from API-Football, bypassing the cache."""
    _require_admin(x_admin_key)
    data = await fetch_live_fixtures(force=True)
    log_event("INFO", "live-sync", f"Manual refresh → source={data['source']}")
    return data


# ---- Admin: mark real results & freeze downstream predictions --------------


@api.get("/admin/results")
async def admin_list_results(x_admin_key: str = Header(default=None)):
    _require_admin(x_admin_key)
    try:
        docs = await asyncio.wait_for(
            db.actual_results.find({}, {"_id": 0}).to_list(100),
            timeout=2.0
        )
    except Exception as e:
        logger.warning(f"Admin list actual results from MongoDB failed: {e}")
        # fallback to local file
        docs = []
        json_path = os.path.join(os.path.dirname(__file__), "actual_results.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r") as f:
                    local_data = json.load(f)
                    docs = [{"match_id": k, "winner_code": v} for k, v in local_data.items()]
            except Exception:
                pass
    return {"results": docs}


@api.post("/admin/results")
async def admin_set_result(payload: ResultPayload, x_admin_key: str = Header(default=None)):
    _require_admin(x_admin_key)
    match = _find_match(payload.match_id)
    if not match:
        raise HTTPException(404, f"Unknown match_id: {payload.match_id}")
    if payload.winner_code not in TEAMS_BY_CODE:
        raise HTTPException(400, f"Unknown team code: {payload.winner_code}")
    if payload.match_id.startswith("R16") and payload.winner_code not in (match["home"], match["away"]):
        raise HTTPException(400, "Winner must be one of the two teams in the fixture")
    doc = {
        "match_id": payload.match_id,
        "winner_code": payload.winner_code,
        "marked_at": datetime.now(timezone.utc).isoformat(),
    }
    # Save to MongoDB
    db_success = False
    try:
        await asyncio.wait_for(
            db.actual_results.update_one({"match_id": payload.match_id}, {"$set": doc}, upsert=True),
            timeout=2.0
        )
        db_success = True
    except Exception as e:
        logger.warning(f"Failed to record result to MongoDB: {e}")

    # Backup to local JSON
    json_path = os.path.join(os.path.dirname(__file__), "actual_results.json")
    try:
        data = {}
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                data = json.load(f)
        data[payload.match_id] = payload.winner_code
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as je:
        logger.warning(f"Failed to update local actual_results.json: {je}")

    # invalidate caches
    _CACHE.clear()
    log_event("INFO", "admin", f"Result recorded: {payload.match_id} → {payload.winner_code}")
    return {"ok": True, "result": doc}


@api.delete("/admin/results/{match_id}")
async def admin_delete_result(match_id: str, x_admin_key: str = Header(default=None)):
    _require_admin(x_admin_key)
    # Delete from MongoDB
    deleted_count = 0
    try:
        r = await asyncio.wait_for(
            db.actual_results.delete_one({"match_id": match_id}),
            timeout=2.0
        )
        deleted_count = r.deleted_count
    except Exception as e:
        logger.warning(f"Failed to delete result from MongoDB: {e}")

    # Delete from local JSON
    json_path = os.path.join(os.path.dirname(__file__), "actual_results.json")
    try:
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                data = json.load(f)
            if match_id in data:
                del data[match_id]
                with open(json_path, "w") as f:
                    json.dump(data, f, indent=2)
                deleted_count = 1
    except Exception as je:
        logger.warning(f"Failed to delete local actual_results.json entry: {je}")

    _CACHE.clear()
    log_event("INFO", "admin", f"Result cleared: {match_id}")
    return {"ok": True, "deleted": deleted_count}


@api.get("/replay")
async def api_replay():
    """Explainability replay — for every historical match in historical_matches.csv,
    run the XGB model pre-match and score it with the Brier metric against the
    actual result. Returns overall accuracy, average Brier, and best/worst calls."""
    import csv as _csv
    from pathlib import Path
    import xgb_model as _xgb

    path = Path(__file__).parent / "historical_matches.csv"
    if not path.exists() or not _xgb.is_ready():
        raise HTTPException(503, "Historical CSV or model unavailable")

    rows = []
    with open(path, newline="") as f:
        for r in _csv.DictReader(f):
            rows.append(r)

    results = []
    correct = 0
    brier_total = 0.0
    for r in rows:
        features = {
            "elo_diff": float(r["home_elo"]) - float(r["away_elo"]),
            "form_diff": float(r["home_form"]) - float(r["away_form"]),
            "h2h_ratio": 0.0,
            "attack_diff": float(r["attack_diff"]),
            "defense_diff": float(r["defense_diff"]),
            "injury_delta": int(r["injury_delta"]),
        }
        probs = _xgb.predict_proba(features)
        actual = int(r["result"])  # 0=away 1=draw 2=home
        pred_class = max((probs["prob_away"], 0), (probs["prob_draw"], 1), (probs["prob_home"], 2))[1]
        if pred_class == actual:
            correct += 1
        # Brier for multiclass: sum of squared errors across 3 classes
        target = [1.0 if actual == c else 0.0 for c in (0, 1, 2)]
        pred_v = [probs["prob_away"], probs["prob_draw"], probs["prob_home"]]
        brier = sum((t - p) ** 2 for t, p in zip(target, pred_v))
        brier_total += brier
        results.append({
            "home": r["home"], "away": r["away"],
            "actual": ["away_win", "draw", "home_win"][actual],
            "predicted": ["away_win", "draw", "home_win"][pred_class],
            "prob_home": round(probs["prob_home"], 3),
            "prob_draw": round(probs["prob_draw"], 3),
            "prob_away": round(probs["prob_away"], 3),
            "brier": round(brier, 4),
            "hit": pred_class == actual,
        })

    results.sort(key=lambda x: x["brier"])
    best = results[:5]
    worst = list(reversed(results[-5:]))
    return {
        "n_matches": len(results),
        "accuracy": round(correct / max(1, len(results)), 4),
        "avg_brier": round(brier_total / max(1, len(results)), 4),
        "best_calls": best,
        "worst_calls": worst,
        "all_calls": results,
    }


@api.post("/favorites")
async def set_favorite(payload: FavoritePayload):
    if payload.team_code not in TEAMS_BY_CODE:
        raise HTTPException(400, "Unknown team code")
    doc = {
        "id": str(uuid.uuid4()),
        "session_id": payload.session_id,
        "team_code": payload.team_code,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        await asyncio.wait_for(
            db.favorites.update_one(
                {"session_id": payload.session_id},
                {"$set": doc},
                upsert=True,
            ),
            timeout=2.0
        )
    except Exception as e:
        logger.warning(f"Failed to write favorite to MongoDB: {e}")
    return {"ok": True, "team": TEAMS_BY_CODE[payload.team_code]}


@api.get("/favorites/{session_id}")
async def get_favorite(session_id: str):
    try:
        doc = await asyncio.wait_for(
            db.favorites.find_one({"session_id": session_id}, {"_id": 0}),
            timeout=2.0
        )
        if not doc:
            return {"team": None}
        return {"team": TEAMS_BY_CODE.get(doc["team_code"])}
    except Exception as e:
        logger.warning(f"Failed to read favorite from MongoDB: {e}")
        return {"team": None}


# ---- helpers ---------------------------------------------------------------
def _find_match(match_id: str):
    """Look up a fixture across the bracket. For QF/SF/F, use the currently
    predicted feeders."""
    for m in BRACKET_STRUCTURE["R16"]:
        if m["id"] == match_id:
            return m

    # For QF/SF/F we resolve via the expected bracket
    if "bracket" not in _CACHE:
        _CACHE["bracket"] = None  # placeholder to avoid recursion
        eb = expected_bracket()
        _CACHE["bracket"] = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "structure": BRACKET_STRUCTURE,
            "matches": eb["matches"],
            "predicted_champion": eb["champion"],
        }
    for m in _CACHE["bracket"]["matches"]:
        if m["id"] == match_id:
            return m
    return None


# ---- wire up ---------------------------------------------------------------
app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=False,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _on_startup():
    bind_mongo(db.agent_logs)
    api_cache.bind(db.api_cache)
    try:
        xgb_model.train_model()
        log_event("INFO", "xgb", f"XGBoost model trained · features: {list(xgb_model.feature_importance().keys())}")
    except Exception as e:
        log_event("ERROR", "xgb", f"XGBoost training failed: {e}")
    bg_scheduler.start()
    log_event("INFO", "system", f"MatchSense agent online — data_provider={provider_name()}, 16 teams loaded")


@app.on_event("shutdown")
async def _on_shutdown():
    bg_scheduler.shutdown()
    client.close()
