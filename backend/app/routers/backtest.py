from fastapi import APIRouter, HTTPException
from app.models.schemas import BacktestParams, BacktestResult
from app.services.csv_loader import csv_loader
from app.services.backtest_engine import BacktestEngine
import pandas as pd

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
    return result


@router.get("/strategies")
async def list_strategies():
    return {
        "strategies": [
            {"id": "ict_smart_money", "name": "ICT Smart Money Concepts", "description": "FVG + OB confluence with ATR sizing"},
            {"id": "liquidity_sweep", "name": "Liquidity Sweep Reversal", "description": "Trade sweeps of prior highs/lows"},
        ]
    }
