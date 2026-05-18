from fastapi import APIRouter, HTTPException
from app.models.schemas import BacktestParams, BacktestResult
from app.services.csv_loader import csv_loader
from app.services.backtest_engine import BacktestEngine
import pandas as pd
import json

router = APIRouter(prefix="/backtest", tags=["backtest"])


@router.post("/run", response_model=BacktestResult)
async def run_backtest(params: BacktestParams):
    if not params.csv_path:
        raise HTTPException(status_code=400, detail="csv_path is required for backtests.")

    try:
        df = csv_loader.load_ohlcv(params.csv_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Filter by date if provided
    if params.start_date:
        df = df[df["time"] >= params.start_date]
    if params.end_date:
        df = df[df["time"] <= params.end_date]

    if len(df) < 50:
        raise HTTPException(status_code=400, detail="Not enough data points after filtering.")

    engine = BacktestEngine(df, params)
    result = engine.run()
    
    # Store replay events in memory for retrieval (in production, use Redis/DB)
    # For now, we just return them via a separate endpoint
    router.replay_events = engine.replay_events
    router.patterns = engine.patterns
    router.ohlcv = df.to_dict('records')
    
    return result


@router.get("/replay")
async def get_replay():
    if not hasattr(router, 'replay_events'):
        raise HTTPException(status_code=404, detail="No replay data. Run a backtest first.")
    return {"events": router.replay_events}


@router.get("/patterns")
async def get_backtest_patterns():
    if not hasattr(router, 'patterns'):
        raise HTTPException(status_code=404, detail="No pattern data. Run a backtest first.")
    return [{
        "pattern_type": p.pattern_type,
        "direction": p.direction,
        "confidence": p.confidence,
        "time": p.time.isoformat() if p.time else None,
        "price_entry": p.price_entry,
        "price_sl": p.price_sl,
        "price_tp": p.price_tp,
        "candle_start_idx": p.candle_start_idx,
        "candle_end_idx": p.candle_end_idx,
        "notes": p.notes,
        "tags": p.tags,
    } for p in router.patterns]


@router.get("/strategies")
async def list_strategies():
    return {
        "strategies": [
            {"id": "ict_smart_money", "name": "ICT Smart Money Concepts", "description": "Pattern-driven entries: FVG, OB, BOS, Liquidity Sweeps with confidence scoring"},
            {"id": "liquidity_sweep", "name": "Liquidity Sweep Reversal", "description": "Trade sweeps of prior highs/lows"},
        ]
    }


@router.get("/ohlcv")
async def get_ohlcv(limit: int = 5000):
    if not hasattr(router, 'ohlcv'):
        raise HTTPException(status_code=404, detail="No OHLCV data. Run a backtest first.")
    return {"data": router.ohlcv[:limit]}
