"""Health check endpoint."""

import time
from fastapi import APIRouter

router = APIRouter(tags=["health"])

_start_time = time.time()


@router.get("/health")
async def health_check():
    """
    Basic health check — returns status, version, and uptime.
    Target latency: <10ms.
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
        "uptime_seconds": round(time.time() - _start_time),
    }
