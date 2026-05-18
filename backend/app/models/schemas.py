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
    killzones: Optional[List[str]] = None

    model_config = {"extra": "ignore"}


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


class Pattern(BaseModel):
    id: Optional[int] = None
    pattern_type: str
    direction: Literal["bullish", "bearish", "neutral"] = "neutral"
    confidence: int = 0
    time: Optional[datetime] = None
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    price_top: float = 0.0
    price_bottom: float = 0.0
    price_entry: float = 0.0
    price_sl: float = 0.0
    price_tp: float = 0.0
    candle_start_idx: int = 0
    candle_end_idx: int = 0
    notes: Optional[str] = None
    tags: List[str] = []
    trade_id: Optional[int] = None
    outcome: Optional[str] = None


class ReplayEvent(BaseModel):
    id: Optional[int] = None
    backtest_run_id: int
    event_type: str  # "candle", "pattern", "trade_entry", "trade_exit"
    candle_idx: int
    timestamp: Optional[datetime] = None
    data: dict = {}


class BacktestRun(BaseModel):
    id: Optional[int] = None
    strategy_name: str
    symbol: str
    timeframe: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    initial_balance: float
    total_return: float = 0.0
    win_rate: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    total_trades: int = 0
    created_at: Optional[datetime] = None


class PatternFilterRequest(BaseModel):
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    pattern_types: Optional[List[str]] = None
    directions: Optional[List[str]] = None
    min_confidence: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    killzones: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    limit: int = 100
    offset: int = 0
