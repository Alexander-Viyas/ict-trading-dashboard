from datetime import datetime
from typing import AsyncGenerator
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_URL

async_engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


class JournalEntryDB(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(Integer, nullable=True)
    date = Column(DateTime, default=datetime.utcnow)
    session = Column(String, nullable=True)
    bias = Column(String, nullable=True)
    pair = Column(String, nullable=True)
    narrative = Column(Text, nullable=True)
    emotions = Column(Text, nullable=True)
    mistakes = Column(Text, nullable=True)
    improvements = Column(Text, nullable=True)
    screenshots = Column(Text, nullable=True)


class TradeDB(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime, nullable=True)
    symbol = Column(String, nullable=False)
    direction = Column(String, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    quantity = Column(Float, nullable=False)
    pnl = Column(Float, nullable=True)
    pnl_pct = Column(Float, nullable=True)
    exit_reason = Column(String, nullable=True)
    tags = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)


class PatternDB(Base):
    __tablename__ = "patterns"

    id = Column(Integer, primary_key=True, index=True)
    pattern_type = Column(String, nullable=False)
    direction = Column(String, nullable=False)
    confidence = Column(Integer, default=0)
    time = Column(DateTime, nullable=True)
    symbol = Column(String, nullable=True)
    timeframe = Column(String, nullable=True)
    price_top = Column(Float, default=0.0)
    price_bottom = Column(Float, default=0.0)
    price_entry = Column(Float, default=0.0)
    price_sl = Column(Float, default=0.0)
    price_tp = Column(Float, default=0.0)
    candle_start_idx = Column(Integer, default=0)
    candle_end_idx = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    trade_id = Column(Integer, nullable=True)
    outcome = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ReplayEventDB(Base):
    __tablename__ = "replay_events"

    id = Column(Integer, primary_key=True, index=True)
    backtest_run_id = Column(Integer, nullable=False)
    event_type = Column(String, nullable=False)  # "candle", "pattern", "trade_entry", "trade_exit"
    candle_idx = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=True)
    data_json = Column(Text, nullable=True)  # serialized event data
    created_at = Column(DateTime, default=datetime.utcnow)


class BacktestRunDB(Base):
    __tablename__ = "backtest_runs"

    id = Column(Integer, primary_key=True, index=True)
    strategy_name = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    initial_balance = Column(Float, nullable=False)
    total_return = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    total_trades = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    params_json = Column(Text, nullable=True)


async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
