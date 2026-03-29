"""
ADHD Second Brain — FastAPI Backend Entry Point

Central brain of the system. All interfaces (Swift app, OpenClaw, Dashboard)
are thin clients that call this backend via REST on port 8420.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings

# ── Route imports ───────────────────────────────────────────────────
from api.health import router as health_router
from api.screen import router as screen_router
from api.chat import router as chat_router
from api.whoop import auth_router as whoop_auth_router, data_router as whoop_data_router
from api.insights import router as insights_router
from api.interventions import router as interventions_router
from api.evaluation import router as evaluation_router
from api.notch import router as notch_router
from api.google_auth import router as google_auth_router
from api.brain_dump import router as brain_dump_router
from api.vent import router as vent_router

from sqlalchemy import text
from db.database import engine, Base
from services.memory_service import memory_service

try:
    from services.mlx_inference import mlx_inference
except ImportError:
    mlx_inference = None

try:
    from services.setfit_service import setfit_classifier
    logging.getLogger("adhd-brain").info("SetFit emotion classifier loaded at startup")
except Exception as e:
    logging.getLogger("adhd-brain").error(f"Failed to load SetFit classifier: {e}")

settings = get_settings()

# ── Logging ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("adhd-brain")


# ── Background Tasks ───────────────────────────────────────────────
async def _model_cleanup_loop():
    """Periodically check if LLM should be unloaded to free memory."""
    while True:
        try:
            if mlx_inference:
                mlx_inference.maybe_unload_if_idle()
        except Exception as e:
            logger.warning(f"Model cleanup error: {e}")
        await asyncio.sleep(30)


async def _daily_snapshot_loop():
    """Save daily snapshot at 23:55 local time, and backfill yesterday on startup."""
    from services.snapshot_service import SnapshotService
    snapshots = SnapshotService()

    # Backfill yesterday if missing (covers cases where backend was down at midnight)
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    try:
        if not await snapshots.has_snapshot(yesterday):
            logger.info(f"Backfilling missing snapshot for {yesterday}")
            await snapshots.save_daily_snapshot(yesterday)
    except Exception as e:
        logger.warning(f"Failed to backfill yesterday's snapshot: {e}")

    snapshot_saved_today = False
    while True:
        try:
            now = datetime.now()
            # Save at 23:55 or later if not already saved today
            if now.hour == 23 and now.minute >= 55 and not snapshot_saved_today:
                await snapshots.save_daily_snapshot()
                snapshot_saved_today = True
                logger.info("End-of-day snapshot saved")

            # Reset flag at midnight
            if now.hour == 0 and now.minute < 5:
                snapshot_saved_today = False
        except Exception as e:
            logger.warning(f"Snapshot loop error: {e}")

        await asyncio.sleep(60)


# ── Lifespan ────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle handler."""
    logger.info("ADHD Second Brain starting up...")
    logger.info(f"   Version : {settings.APP_VERSION}")
    logger.info(f"   Port    : {settings.APP_PORT}")

    # Init database schema (Phase 1 & 6)
    logger.info("Initializing PostgreSQL schema...")
    async with engine.begin() as conn:
        # Check if pgvector extension is created
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created/verified.")

    # Start background model cleanup
    cleanup_task = asyncio.create_task(_model_cleanup_loop())
    logger.info("Background model cleanup task started (30s interval)")

    # Start daily snapshot background task
    snapshot_task = asyncio.create_task(_daily_snapshot_loop())
    logger.info("Daily snapshot task started (checks every 60s, saves at 23:55)")

    yield

    snapshot_task.cancel()
    cleanup_task.cancel()
    if mlx_inference:
        mlx_inference._unload()
    logger.info("ADHD Second Brain shutting down...")


# ── FastAPI Application ─────────────────────────────────────────────
app = FastAPI(
    title="ADHD Second Brain",
    description="Always-on ADHD personal AI assistant — screen monitoring, "
                "affective computing, explainable interventions.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# ── CORS Middleware ─────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Lock down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount Routers ───────────────────────────────────────────────────
app.include_router(health_router)
app.include_router(screen_router)
app.include_router(chat_router)
app.include_router(whoop_auth_router)
app.include_router(whoop_data_router)
app.include_router(insights_router)
app.include_router(interventions_router)
app.include_router(evaluation_router)
app.include_router(notch_router)
app.include_router(google_auth_router)
app.include_router(brain_dump_router)
app.include_router(vent_router)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint — API overview."""
    return {
        "name": "ADHD Second Brain",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "endpoints": [
            "GET  /health",
            "POST /screen/activity",
            "POST /chat/message",
            "GET  /api/auth/whoop",
            "GET  /api/auth/whoop/status",
            "POST /api/auth/whoop/disconnect",
            "GET  /whoop/*",
            "GET  /insights/*",
            "GET  /interventions/*",
            "POST /eval/ablation",
            "GET  /eval/ablation",
            "POST /eval/logging",
            "GET  /api/auth/google",
            "GET  /api/auth/google/callback",
            "GET  /api/auth/google/status",
            "POST /api/v1/brain-dump/",
            "GET  /api/v1/brain-dump/review/recent",
            "GET  /api/v1/brain-dump/review/session/{session_id}",
            "POST /api/v1/vent/chat/stream",
            "POST /api/v1/vent/chat",
            "POST /api/v1/vent/session/new",
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.APP_PORT, reload=True)
