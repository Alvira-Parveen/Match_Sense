"""Background scheduler — APScheduler AsyncIOScheduler wired into FastAPI lifecycle.

Jobs registered at startup:
  • refresh_fixtures   — every 6 hours  (live fixture sync)
  • refresh_monte_carlo — every 6 hours (re-runs MC after real results drop)
  • retrain_model      — once daily at 03:00 UTC (XGBoost retrain)
  • clear_scraper_cache — every 2 hours (ensures agent tools fetch fresh form)

All jobs are fire-and-forget inside the running asyncio event loop.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List

log = logging.getLogger(__name__)

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.cron import CronTrigger
    _APScheduler_OK = True
except ImportError:
    _APScheduler_OK = False
    AsyncIOScheduler = None  # type: ignore

_scheduler = None
_job_history: List[Dict] = []   # last-N run timestamps per job


def _log_run(job_name: str, status: str, detail: str = "") -> None:
    entry = {
        "job": job_name,
        "status": status,
        "ts": datetime.now(timezone.utc).isoformat(),
        "detail": detail,
    }
    _job_history.append(entry)
    # Keep last 200 entries
    del _job_history[:-200]
    log.info("[scheduler] %s → %s %s", job_name, status, detail)


# ── Job callbacks ─────────────────────────────────────────────────────────────

async def _job_refresh_fixtures() -> None:
    """Force a live fixture sync from API-Football."""
    try:
        from data_provider import fetch_live_fixtures
        data = await fetch_live_fixtures(force=True)
        _log_run("refresh_fixtures", "ok", f"source={data['source']}")
    except Exception as e:
        _log_run("refresh_fixtures", "error", str(e)[:200])


async def _job_refresh_monte_carlo() -> None:
    """Re-run Monte Carlo and warm the server cache."""
    try:
        # Import lazily to avoid circular at module load
        from ml_engine import monte_carlo
        import cache as api_cache

        result = monte_carlo(n_runs=10000)
        top = result["teams"][0]
        _log_run(
            "refresh_monte_carlo", "ok",
            f"top={top['name']} @ {top['prob_champion']*100:.1f}%",
        )
    except Exception as e:
        _log_run("refresh_monte_carlo", "error", str(e)[:200])


def _job_retrain_model() -> None:
    """Re-train XGBoost on current CSV data."""
    try:
        import xgb_model
        xgb_model.train_model()
        stats = xgb_model.training_stats()
        _log_run(
            "retrain_model", "ok",
            f"real={stats['real_rows']} syn={stats['synthetic_rows']} total={stats['total_rows']}",
        )
    except Exception as e:
        _log_run("retrain_model", "error", str(e)[:200])


def _job_clear_scraper_cache() -> None:
    """Clear scraper in-memory cache so agent tools fetch fresh form data."""
    try:
        from scraper import clear_cache
        clear_cache()
        _log_run("clear_scraper_cache", "ok")
    except Exception as e:
        _log_run("clear_scraper_cache", "error", str(e)[:200])


# ── Lifecycle ─────────────────────────────────────────────────────────────────

def start() -> bool:
    """Start the scheduler. Returns True if APScheduler is available."""
    global _scheduler
    if not _APScheduler_OK:
        log.warning("APScheduler not installed — background jobs disabled. Run: pip install apscheduler")
        return False

    _scheduler = AsyncIOScheduler(timezone="UTC")

    # Clear scraper cache every 2 hours
    _scheduler.add_job(
        _job_clear_scraper_cache,
        IntervalTrigger(hours=2),
        id="clear_scraper_cache",
        replace_existing=True,
    )

    # Refresh live fixtures every 6 hours
    _scheduler.add_job(
        _job_refresh_fixtures,
        IntervalTrigger(hours=6),
        id="refresh_fixtures",
        replace_existing=True,
    )

    # Refresh Monte Carlo every 6 hours (offset 30 min so fixtures land first)
    _scheduler.add_job(
        _job_refresh_monte_carlo,
        IntervalTrigger(hours=6, minutes=30),
        id="refresh_monte_carlo",
        replace_existing=True,
    )

    # Retrain XGBoost daily at 03:00 UTC
    _scheduler.add_job(
        _job_retrain_model,
        CronTrigger(hour=3, minute=0),
        id="retrain_model",
        replace_existing=True,
    )

    _scheduler.start()
    log.info("[scheduler] started — 4 jobs registered (fixtures/6h, MC/6h, retrain/daily@03:00, cache/2h)")
    return True


def shutdown() -> None:
    """Gracefully stop the scheduler on app shutdown."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        log.info("[scheduler] stopped")


def status() -> Dict:
    """Return scheduler status for the /api/scheduler/status endpoint."""
    jobs = []
    if _scheduler:
        for job in _scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "next_run_utc": job.next_run_time.isoformat() if job.next_run_time else None,
            })
    return {
        "running": bool(_scheduler and _scheduler.running),
        "apscheduler_available": _APScheduler_OK,
        "jobs": jobs,
        "recent_runs": list(reversed(_job_history[-20:])),
    }
