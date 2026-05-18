import asyncio
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from app.services.mt5_bridge import mt5_bridge
from app.services.csv_loader import csv_loader
from app.models.schemas import OHLCV

router = APIRouter(prefix="/data", tags=["data"])

live_subscribers = []


@router.get("/mt5/tick")
async def get_mt5_tick(symbol: str = "EURUSD"):
    """Request latest tick from MT5 (requires MT5 bridge to be connected)."""
    # For REST: we cache last tick in bridge or request it. Simplified.
    return {"symbol": symbol, "note": "Use WebSocket /ws/live for real-time ticks."}


@router.get("/csv/list")
async def list_csv_files():
    return {"files": csv_loader.list_available()}


@router.get("/csv/load")
async def load_csv(
    path: str = Query(..., description="Relative path inside data/ directory"),
    limit: int = Query(1000),
):
    try:
        df = csv_loader.load_ohlcv(path)
        records = df.head(limit).to_dict("records")
        return {"count": len(records), "columns": list(df.columns), "data": records}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.websocket("/ws/live")
async def websocket_live(websocket):
    await websocket.accept()
    live_subscribers.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        live_subscribers.remove(websocket)
