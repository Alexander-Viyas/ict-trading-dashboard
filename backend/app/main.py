import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import init_db
from app.services.mt5_bridge import mt5_bridge
from app.routers import data, backtest, journal, ai, patterns, live


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Auto-connect MT5 bridge on startup
    try:
        await mt5_bridge.connect()
        print("[MT5] Bridge auto-connected")
    except Exception as e:
        print(f"[MT5] Auto-connect failed (MT5 may not be running): {e}")
    yield
    await mt5_bridge.close()


app = FastAPI(
    title="ICT Trading Dashboard API",
    description="Hybrid MT5 + CSV backtesting engine with pattern recognition + live confluence",
    version="2.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data.router)
app.include_router(backtest.router)
app.include_router(journal.router)
app.include_router(ai.router)
app.include_router(patterns.router)
app.include_router(live.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
