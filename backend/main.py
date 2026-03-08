"""
ADHD Second Brain — FastAPI Backend Entry Point

Central brain of the system. All interfaces (Swift app, OpenClaw, Dashboard)
are thin clients that call this backend via REST on port 8420.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings

# ── Route imports ───────────────────────────────────────────────────
from api.health import router as health_router
from api.screen import router as screen_router
from api.chat import router as chat_router
from api.whoop import router as whoop_router
from api.insights import router as insights_router
from api.interventions import router as interventions_router


settings = get_settings()

# ── Logging ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("adhd-brain")


# ── Lifespan ────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle handler."""
    logger.info("🧠 ADHD Second Brain starting up...")
    logger.info(f"   Version : {settings.APP_VERSION}")
    logger.info(f"   Port    : {settings.APP_PORT}")
    # TODO: init database connection pool (Phase 2+)
    # TODO: init memory service (Phase 6)
    yield
    logger.info("🧠 ADHD Second Brain shutting down...")


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
app.include_router(whoop_router)
app.include_router(insights_router)
app.include_router(interventions_router)


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
            "GET  /whoop/*",
            "GET  /insights/*",
            "GET  /interventions/*",
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.APP_PORT, reload=True)
