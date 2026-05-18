from fastapi import APIRouter, HTTPException
from app.models.schemas import BacktestParams, BacktestResult
from app.services.csv_loader import csv_loader
from app.services.backtest_engine import BacktestEngine
from app.services.mtf_analyzer import MultiTimeframeAnalyzer
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


@router.post("/mtf")
async def run_mtf_analysis(params: BacktestParams):
    """Multi-timeframe pattern analysis with confluence scoring."""
    if not params.csv_path:
        raise HTTPException(status_code=400, detail="csv_path is required.")
    try:
        df = csv_loader.load_ohlcv(params.csv_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if params.start_date:
        df = df[df["time"] >= params.start_date]
    if params.end_date:
        df = df[df["time"] <= params.end_date]

    mtf = MultiTimeframeAnalyzer(
        df,
        symbol=params.symbol,
        base_timeframe=params.timeframe,
        higher_timeframes=["M15", "H1"],
    )
    confluence = mtf.get_top_confluence(min_score=30, limit=50)

    return {
        "symbol": params.symbol,
        "base_timeframe": params.timeframe,
        "total_confluence_patterns": len(confluence),
        "patterns": [
            {
                "base": {
                    "pattern_type": c.base_pattern.pattern_type,
                    "direction": c.base_pattern.direction,
                    "confidence": c.base_pattern.confidence,
                    "time": c.base_pattern.time.isoformat() if c.base_pattern.time else None,
                    "price_entry": c.base_pattern.price_entry,
                    "price_sl": c.base_pattern.price_sl,
                    "price_tp": c.base_pattern.price_tp,
                    "candle_start_idx": c.base_pattern.candle_start_idx,
                    "candle_end_idx": c.base_pattern.candle_end_idx,
                },
                "confluence_score": c.confluence_score,
                "alignment": c.alignment,
                "summary": c.summary,
                "higher_timeframes": [
                    {
                        "timeframe": h["timeframe"],
                        "pattern_type": h["pattern"].pattern_type,
                        "direction": h["pattern"].direction,
                        "confidence": h["pattern"].confidence,
                        "price_entry": h["pattern"].price_entry,
                        "aligned": h["aligned"],
                    }
                    for h in c.higher_timeframe_patterns
                ],
            }
            for c in confluence
        ],
    }
