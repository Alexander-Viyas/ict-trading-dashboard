from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import List, Optional
from datetime import datetime
from app.db.database import get_db, PatternDB
from app.models.schemas import Pattern, PatternFilterRequest
from app.services.csv_loader import csv_loader
from app.services.pattern_engine import PatternEngine

router = APIRouter(prefix="/patterns", tags=["patterns"])


@router.post("/detect", response_model=List[Pattern])
async def detect_patterns(
    csv_path: str,
    symbol: str = "EURUSD",
    timeframe: str = "M15",
    min_confidence: int = 0,
    db: AsyncSession = Depends(get_db),
):
    try:
        df = csv_loader.load_ohlcv(csv_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"CSV not found: {csv_path}")

    engine = PatternEngine(df, symbol=symbol, timeframe=timeframe)
    patterns = engine.detect_all()

    if min_confidence > 0:
        patterns = engine.filter_by_confidence(min_confidence)

    # Save to DB
    for p in patterns:
        db_pattern = PatternDB(
            pattern_type=p.pattern_type,
            direction=p.direction,
            confidence=p.confidence,
            time=p.time,
            symbol=p.symbol,
            timeframe=p.timeframe,
            price_top=p.price_top,
            price_bottom=p.price_bottom,
            price_entry=p.price_entry,
            price_sl=p.price_sl,
            price_tp=p.price_tp,
            candle_start_idx=p.candle_start_idx,
            candle_end_idx=p.candle_end_idx,
            notes=p.notes,
            tags=",".join(p.tags),
        )
        db.add(db_pattern)
    await db.commit()

    return patterns


@router.post("/filter", response_model=List[Pattern])
async def filter_patterns(
    filter_req: PatternFilterRequest,
    db: AsyncSession = Depends(get_db),
):
    query = select(PatternDB)

    if filter_req.symbol:
        query = query.where(PatternDB.symbol == filter_req.symbol)
    if filter_req.timeframe:
        query = query.where(PatternDB.timeframe == filter_req.timeframe)
    if filter_req.pattern_types:
        query = query.where(PatternDB.pattern_type.in_(filter_req.pattern_types))
    if filter_req.directions:
        query = query.where(PatternDB.direction.in_(filter_req.directions))
    if filter_req.min_confidence > 0:
        query = query.where(PatternDB.confidence >= filter_req.min_confidence)
    if filter_req.start_date:
        query = query.where(PatternDB.time >= filter_req.start_date)
    if filter_req.end_date:
        query = query.where(PatternDB.time <= filter_req.end_date)
    if filter_req.tags:
        for tag in filter_req.tags:
            query = query.where(PatternDB.tags.contains(tag))

    query = query.order_by(desc(PatternDB.time)).offset(filter_req.offset).limit(filter_req.limit)
    result = await db.execute(query)
    rows = result.scalars().all()

    return [
        Pattern(
            id=r.id,
            pattern_type=r.pattern_type,
            direction=r.direction,
            confidence=r.confidence,
            time=r.time,
            symbol=r.symbol,
            timeframe=r.timeframe,
            price_top=r.price_top,
            price_bottom=r.price_bottom,
            price_entry=r.price_entry,
            price_sl=r.price_sl,
            price_tp=r.price_tp,
            candle_start_idx=r.candle_start_idx,
            candle_end_idx=r.candle_end_idx,
            notes=r.notes,
            tags=r.tags.split(",") if r.tags else [],
            trade_id=r.trade_id,
            outcome=r.outcome,
        )
        for r in rows
    ]


@router.get("/{pattern_id}", response_model=Pattern)
async def get_pattern(pattern_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PatternDB).where(PatternDB.id == pattern_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return Pattern(
        id=row.id,
        pattern_type=row.pattern_type,
        direction=row.direction,
        confidence=row.confidence,
        time=row.time,
        symbol=row.symbol,
        timeframe=row.timeframe,
        price_top=row.price_top,
        price_bottom=row.price_bottom,
        price_entry=row.price_entry,
        price_sl=row.price_sl,
        price_tp=row.price_tp,
        candle_start_idx=row.candle_start_idx,
        candle_end_idx=row.candle_end_idx,
        notes=row.notes,
        tags=row.tags.split(",") if row.tags else [],
        trade_id=row.trade_id,
        outcome=row.outcome,
    )


@router.get("/stats/summary")
async def pattern_stats(
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(PatternDB)
    if symbol:
        query = query.where(PatternDB.symbol == symbol)
    if timeframe:
        query = query.where(PatternDB.timeframe == timeframe)

    result = await db.execute(query)
    rows = result.scalars().all()

    total = len(rows)
    bullish = sum(1 for r in rows if r.direction == "bullish")
    bearish = sum(1 for r in rows if r.direction == "bearish")
    avg_conf = sum(r.confidence for r in rows) / max(total, 1)

    pattern_counts = {}
    for r in rows:
        pattern_counts[r.pattern_type] = pattern_counts.get(r.pattern_type, 0) + 1

    return {
        "total_patterns": total,
        "bullish": bullish,
        "bearish": bearish,
        "avg_confidence": round(avg_conf, 1),
        "pattern_breakdown": pattern_counts,
    }
