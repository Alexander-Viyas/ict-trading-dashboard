import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from app.models.schemas import BacktestParams, TradeRecord, BacktestResult


class BacktestEngine:
    """
    Modular backtest engine supporting ICT Smart Money Concepts.
    Detects: FVG, Order Blocks, BOS/CHoCH, Liquidity Sweeps.
    """

    def __init__(self, df: pd.DataFrame, params: BacktestParams):
        self.df = df.copy()
        self.params = params
        self.balance = params.initial_balance
        self.equity = params.initial_balance
        self.trades: List[TradeRecord] = []
        self.equity_curve: List[float] = [self.equity]
        self.equity_times: List[datetime] = [self.df.iloc[0]["time"] if len(self.df) > 0 else datetime.utcnow()]
        self.position: Optional[Dict[str, Any]] = None

    def run(self) -> BacktestResult:
        self._detect_structures()
        for i in range(len(self.df)):
            row = self.df.iloc[i]
            self._update_equity(row)
            self._check_signals(i, row)
            self._check_exits(i, row)
            self.equity_curve.append(self.equity)
            self.equity_times.append(row["time"])

        self._close_all_at_end()
        return self._build_result()

    def _detect_structures(self):
        df = self.df
        # Fair Value Gaps (FVG)
        df["fvg_bull"] = False
        df["fvg_bear"] = False
        for i in range(2, len(df)):
            c2, c1, c0 = df.iloc[i - 2], df.iloc[i - 1], df.iloc[i]
            # Bullish FVG: low[i] > high[i-2]
            if c0["low"] > c2["high"]:
                df.at[i, "fvg_bull"] = True
            # Bearish FVG: high[i] < low[i-2]
            if c0["high"] < c2["low"]:
                df.at[i, "fvg_bear"] = True

        # Order Blocks (simple: last down candle before strong up move / last up candle before strong down move)
        df["ob_bull"] = False
        df["ob_bear"] = False
        for i in range(3, len(df)):
            prev = df.iloc[i - 3:i]
            c0 = df.iloc[i]
            # Bullish OB: bearish candle before strong bullish impulse
            if (prev.iloc[-3]["close"] < prev.iloc[-3]["open"] and
                    c0["close"] > prev.iloc[-2]["high"] and c0["close"] > prev.iloc[-1]["high"]):
                df.at[i - 3, "ob_bull"] = True
            # Bearish OB: bullish candle before strong bearish impulse
            if (prev.iloc[-3]["close"] > prev.iloc[-3]["open"] and
                    c0["close"] < prev.iloc[-2]["low"] and c0["close"] < prev.iloc[-1]["low"]):
                df.at[i - 3, "ob_bear"] = True

        # BOS/CHoCH (Break of Structure / Change of Character)
        df["bos"] = False
        df["choch"] = False
        last_high = df.iloc[0]["high"]
        last_low = df.iloc[0]["low"]
        for i in range(1, len(df)):
            row = df.iloc[i]
            if row["high"] > last_high:
                df.at[i, "bos"] = True
                last_high = row["high"]
            if row["low"] < last_low:
                df.at[i, "choch"] = True
                last_low = row["low"]

        # Liquidity Sweeps (price takes out prior high/low then reverses)
        df["sweep_high"] = False
        df["sweep_low"] = False
        for i in range(2, len(df)):
            c0, c1 = df.iloc[i - 1], df.iloc[i]
            # Sweep high: breaks above recent high then closes below
            if c0["high"] > df.iloc[i - 2]["high"] and c1["close"] < c0["open"]:
                df.at[i, "sweep_high"] = True
            # Sweep low: breaks below recent low then closes above
            if c0["low"] < df.iloc[i - 2]["low"] and c1["close"] > c0["open"]:
                df.at[i, "sweep_low"] = True

    def _check_signals(self, i: int, row: pd.Series):
        if self.position is not None:
            return

        # Simple ICT strategy: FVG + OB confluence
        if row["fvg_bull"] and row["ob_bull"] and not row["sweep_high"]:
            self._enter("long", row)
        elif row["fvg_bear"] and row["ob_bear"] and not row["sweep_low"]:
            self._enter("short", row)

    def _enter(self, direction: str, row: pd.Series):
        risk_amount = self.equity * self.params.risk_per_trade
        # Simplified: 1 ATR-based stop for sizing
        atr = self._atr(row.name)
        if atr <= 0:
            atr = row["close"] * 0.001
        sl_dist = 1.5 * atr
        qty = risk_amount / sl_dist if sl_dist > 0 else 0
        if qty <= 0:
            return

        self.position = {
            "direction": direction,
            "entry_price": row["close"],
            "quantity": qty,
            "entry_time": row["time"],
            "sl": row["close"] - sl_dist if direction == "long" else row["close"] + sl_dist,
            "tp": row["close"] + 2.0 * sl_dist if direction == "long" else row["close"] - 2.0 * sl_dist,
        }

    def _check_exits(self, i: int, row: pd.Series):
        if self.position is None:
            return

        pos = self.position
        hit_sl = (pos["direction"] == "long" and row["low"] <= pos["sl"]) or (
            pos["direction"] == "short" and row["high"] >= pos["sl"]
        )
        hit_tp = (pos["direction"] == "long" and row["high"] >= pos["tp"]) or (
            pos["direction"] == "short" and row["low"] <= pos["tp"]
        )

        if hit_sl:
            self._exit(pos, pos["sl"], row["time"], "SL")
        elif hit_tp:
            self._exit(pos, pos["tp"], row["time"], "TP")
        elif i == len(self.df) - 1:
            self._exit(pos, row["close"], row["time"], "end_of_data")

    def _exit(self, pos: Dict, exit_price: float, exit_time: datetime, reason: str):
        raw_pnl = (exit_price - pos["entry_price"]) * pos["quantity"] if pos["direction"] == "long" else (
            pos["entry_price"] - exit_price) * pos["quantity"]
        self.equity += raw_pnl
        pnl_pct = (raw_pnl / self.balance) if self.balance != 0 else 0

        trade = TradeRecord(
            entry_time=pos["entry_time"],
            exit_time=exit_time,
            symbol=self.params.symbol,
            direction=pos["direction"],
            entry_price=pos["entry_price"],
            exit_price=exit_price,
            quantity=pos["quantity"],
            pnl=raw_pnl,
            pnl_pct=pnl_pct,
            exit_reason=reason,
            tags=["ict", pos["direction"], reason.lower()],
            notes=f"Strategy: {self.params.strategy_name}",
        )
        self.trades.append(trade)
        self.position = None

    def _update_equity(self, row: pd.Series):
        if self.position is None:
            return
        pos = self.position
        unrealized = (row["close"] - pos["entry_price"]) * pos["quantity"] if pos["direction"] == "long" else (
            pos["entry_price"] - row["close"]) * pos["quantity"]
        self.equity = self.balance + unrealized

    def _close_all_at_end(self):
        if self.position is not None:
            last_row = self.df.iloc[-1]
            self._exit(self.position, last_row["close"], last_row["time"], "end_of_data")

    def _atr(self, idx: int, period: int = 14) -> float:
        start = max(0, idx - period + 1)
        subset = self.df.iloc[start:idx + 1]
        if len(subset) < 2:
            return 0.0
        trs = []
        for i in range(1, len(subset)):
            prev = subset.iloc[i - 1]
            cur = subset.iloc[i]
            tr1 = cur["high"] - cur["low"]
            tr2 = abs(cur["high"] - prev["close"])
            tr3 = abs(cur["low"] - prev["close"])
            trs.append(max(tr1, tr2, tr3))
        return float(np.mean(trs)) if trs else 0.0

    def _build_result(self) -> BacktestResult:
        total_pnl = sum(t.pnl for t in self.trades)
        wins = [t for t in self.trades if t.pnl and t.pnl > 0]
        losses = [t for t in self.trades if t.pnl and t.pnl <= 0]
        win_rate = len(wins) / len(self.trades) if self.trades else 0
        gross_profit = sum(t.pnl for t in wins)
        gross_loss = abs(sum(t.pnl for t in losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

        # Max drawdown
        peak = self.params.initial_balance
        max_dd = 0.0
        for val in self.equity_curve:
            if val > peak:
                peak = val
            dd = peak - val
            if dd > max_dd:
                max_dd = dd
        max_dd_pct = (max_dd / peak) if peak > 0 else 0

        # Sharpe (simplified, assuming risk-free rate ~0)
        returns = np.diff(self.equity_curve)
        std = np.std(returns) if len(returns) > 1 else 1e-9
        sharpe = (np.mean(returns) / std) * np.sqrt(252 * 24) if std > 0 else 0

        return BacktestResult(
            params=self.params,
            trades=self.trades,
            total_return=total_pnl,
            total_return_pct=(total_pnl / self.params.initial_balance) * 100,
            win_rate=win_rate,
            profit_factor=profit_factor,
            max_drawdown=max_dd,
            max_drawdown_pct=max_dd_pct,
            sharpe_ratio=sharpe,
            equity_curve=self.equity_curve,
            equity_times=self.equity_times,
        )
