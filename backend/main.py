# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# main.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""FastAPI application entry point."""

import asyncio
import logging
import os
import sys

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

from .api import (
    auth_router,
    control_router,
    config_router,
    serial_router,
    ws_router,
    airport_router,
)
from .auto_start import perform_auto_start, AutoStartError

# Configure logging to stdout with INFO level
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Set specific loggers
logging.getLogger("backend.network.receiver").setLevel(logging.INFO)
logging.getLogger("backend.rebroadcaster_runner").setLevel(logging.INFO)
logging.getLogger("backend.receiver_runner").setLevel(logging.INFO)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - runs on startup and shutdown."""
    # Startup
    logger.info("Application starting up...")
    try:
        event_loop = asyncio.get_event_loop()
        auto_started = await perform_auto_start(event_loop)
        if auto_started:
            logger.info("Auto-start completed successfully")
    except AutoStartError as e:
        logger.error(f"Auto-start failed: {e}")
        # Don't crash the app, just log the error
    except Exception as e:
        logger.error(f"Unexpected error during auto-start: {e}")

    yield  # App is running

    # Shutdown
    logger.info("Application shutting down...")


app = FastAPI(
    title="NMEA GPS Simulator API",
    description=(
        "REST + WebSocket API for the NMEA GPS Simulator. "
        "Provides authentication, mode control, runtime configuration, "
        "serial-port management, airport lookup, and real-time NMEA "
        "broadcast over a WebSocket."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Include API routers
app.include_router(auth_router)
app.include_router(control_router)
app.include_router(config_router)
app.include_router(serial_router)
app.include_router(ws_router)
app.include_router(airport_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/redoc", include_in_schema=False)
async def redoc_html() -> HTMLResponse:
    """ReDoc UI served from a pinned CDN.

    FastAPI's default ReDoc mount uses an `@next` CDN tag that periodically
    returns 404. Serving ReDoc through this custom route with a pinned version
    keeps the page reliable.
    """
    return get_redoc_html(
        openapi_url="/api/openapi.json",
        title="NMEA GPS Simulator API - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
    )


# Static files (React build output)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(static_dir, "assets")),
        name="assets",
    )

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(os.path.join(static_dir, "index.html"))

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        file_path = os.path.join(static_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(static_dir, "index.html"))
