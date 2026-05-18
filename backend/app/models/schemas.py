from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class TickData(BaseModel):
    symbol: str
    bid: float
    ask: float
    time: datetime
    volume: Optional[int] = None


class OHLCV(BaseModel):
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class BacktestParams(BaseModel):
    strategy_name: str = "ict_smart_money"
    symbol: str = "EURUSD"
    timeframe: str = "M15"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    initial_balance: float = 10000.0
    risk_per_trade: float = 0.01
    csv_path: Optional[str] = None


class TradeRecord(BaseModel):
    entry_time: datetime
    exit_time: Optional[datetime] = None
    symbol: str
    direction: Literal["long", "short"]
    entry_price: float
    exit_price: Optional[float] = None
    quantity: float
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    exit_reason: Optional[str] = None
    tags: Optional[List[str]] = []
    notes: Optional[str] = None


class BacktestResult(BaseModel):
    params: BacktestParams
    trades: List[TradeRecord]
    total_return: float
    total_return_pct: float
    win_rate: float
    profit_factor: float
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_ratio: float
    equity_curve: List[float]
    equity_times: List[datetime]


class JournalEntry(BaseModel):
    id: Optional[int] = None
    trade_id: Optional[int] = None
    date: datetime = Field(default_factory=datetime.utcnow)
    session: Optional[Literal["london", "ny_am", "ny_pm", "asia"]] = None
    bias: Optional[Literal["bullish", "bearish", "neutral"]] = None
    pair: Optional[str] = None
    narrative: Optional[str] = None
    emotions: Optional[str] = None
    mistakes: Optional[str] = None
    improvements: Optional[str] = None
    screenshots: Optional[List[str]] = []


class AIInsightRequest(BaseModel):
    journal_entries: List[JournalEntry]
    backtest_results: Optional[BacktestResult] = None
    question: Optional[str] = "Analyze my trading performance and suggest improvements."


class AIInsightResponse(BaseModel):
    insight: str
    model: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
