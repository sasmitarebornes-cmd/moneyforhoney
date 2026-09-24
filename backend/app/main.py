"""
MONEY For HONEY
Main FastAPI Application & AsyncIO Autonomous Trading Engine Loop.
Initializes background workers:
- Market Scanner & Regime Classifier (ATR, ADX)
- Spatial Arbitrage Poller (Binance vs Bybit vs OKX)
- Risk Manager Circuit Breaker Monitor
- Auto-Vault Compounding Sweeper
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import router as api_router
from app.core.config import settings
from app.engine.exchange import exchange_service
from app.engine.loop import autonomous_trading_loop

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("money_for_honey.main")

# Background task reference
engine_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine_task
    logger.info(f"Booting {settings.APP_NAME} - {settings.TAGLINE}")
    engine_task = asyncio.create_task(autonomous_trading_loop())
    yield
    if engine_task:
        engine_task.cancel()
        try:
            await engine_task
        except asyncio.CancelledError:
            pass
    await exchange_service.close()
    logger.info("Engine gracefully shutdown.")


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.TAGLINE,
    version="2.0.0",
    lifespan=lifespan,
)

# CORS configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "tagline": settings.TAGLINE,
        "status": "ONLINE",
        "docs_url": "/docs",
        "api_prefix": "/api",
    }
