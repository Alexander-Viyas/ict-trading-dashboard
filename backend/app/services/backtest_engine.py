import pandas as pd
import numpy as np
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.models.schemas import BacktestParams, TradeRecord, BacktestResult
from app.services.pattern_engine import PatternEngine, Pattern


class BacktestEngine:
    """
    ICT Pattern-Driven Backtest Engine.
    Uses PatternEngine signals for entries with confidence scoring.
    Emits replay events for visual playback.
    """

    def __init__(self, df: pd.DataFrame, params: BacktestParams):
        self.df = df.copy().reset_index(drop=True)
        self.params = params
        self.balance = params.initial_balance
        self.equity = params.initial_balance
        self.trades: List[TradeRecord] = []
        self.equity_curve: List[float] = [self.equity]
        self.equity_times: List[datetime] = [self.df.iloc[0]["time"] if len(self.df) > 0 else datetime.utcnow()]
        self.position: Optional[Dict[str, Any]] = None
        self.patterns: List[Pattern] = []
        self.replay_events: List[Dict] = []
        self.pattern_idx_map: Dict[int, List[Pattern]] = {}
        self.min_confidence = 50  # Minimum pattern confidence to trade

    def run(self) -> BacktestResult:
        # 1. Detect all patterns first
        self._detect_patterns()
        
        # 2. Run bar-by-bar backtest
        for i in range(len(self.df)):
            row = self.df.iloc[i]
            
            # Emit candle event for replay
            self._emit_event("candle", i, row["time"], {
                "open": row["open"], "high": row["high"],
                "low": row["low"], "close": row["close"], "volume": row.get("volume", 0)
            })
            
            # Emit pattern events if any at this candle
            for pat in self.pattern_idx_map.get(i, []):
                self._emit_event("pattern", i, row["time"], {
                    "pattern_type": pat.pattern_type,
                    "direction": pat.direction,
                    "confidence": pat.confidence,
                    "price_entry": pat.price_entry,
                    "price_sl": pat.price_sl,
                    "price_tp": pat.price_tp,
                    "tags": pat.tags,
                })
            
            self._update_equity(row)
            self._check_signals(i, row)
            self._check_exits(i, row)
            self.equity_curve.append(self.equity)
            self.equity_times.append(row["time"])

        self._close_all_at_end()
        return self._build_result()

    def _detect_patterns(self):
        """Run PatternEngine and build index map."""
        engine = PatternEngine(self.df, symbol=self.params.symbol, timeframe=self.params.timeframe)
        all_patterns = engine.detect_all()
        
        # Filter by confidence
        self.patterns = [p for p in all_patterns if p.confidence >= self.min_confidence]
        
        # Build index map for fast lookup
        for p in self.patterns:
            for idx in range(p.candle_start_idx, p.candle_end_idx + 1):
                if idx not in self.pattern_idx_map:
                    self.pattern_idx_map[idx] = []
                self.pattern_idx_map[idx].append(p)

    def _check_signals(self, i: int, row: pd.Series):
        if self.position is not None:
            return

        patterns_here = self.pattern_idx_map.get(i, [])
        if not patterns_here:
            return

        # Check killzone filter if enabled
        if hasattr(self.params, 'killzones') and self.params.killzones:
            # Tag patterns with killzone info (already done in engine)
            pass

        # Strategy: Enter on highest-confidence bullish/bearish pattern
        bullish = [p for p in patterns_here if p.direction == "bullish"]
        bearish = [p for p in patterns_here if p.direction == "bearish"]

        if bullish and not bearish:
            best = max(bullish, key=lambda p: p.confidence)
            self._enter("long", row, best)
        elif bearish and not bullish:
            best = max(bearish, key=lambda p: p.confidence)
            self._enter("short", row, best)
        elif bullish and bearish:
            # Take the stronger side
            b_conf = max(p.confidence for p in bullish)
            s_conf = max(p.confidence for p in bearish)
            if b_conf > s_conf + 10:
                best = max(bullish, key=lambda p: p.confidence)
                self._enter("long", row, best)
            elif s_conf > b_conf + 10:
                best = max(bearish, key=lambda p: p.confidence)
                self._enter("short", row, best)

    def _enter(self, direction: str, row: pd.Series, pattern: Pattern):
        risk_amount = self.equity * self.params.risk_per_trade
        atr = self._atr(row.name)
        if atr <= 0:
            atr = row["close"] * 0.001

        sl_dist = abs(row["close"] - pattern.price_sl)
        if sl_dist <= 0:
            sl_dist = 1.5 * atr

        qty = risk_amount / sl_dist if sl_dist > 0 else 0
        if qty <= 0:
            return

        self.position = {
            "direction": direction,
            "entry_price": row["close"],
            "quantity": qty,
            "entry_time": row["time"],
            "sl": pattern.price_sl,
            "tp": pattern.price_tp,
            "pattern": pattern,
        }

        self._emit_event("trade_entry", row.name, row["time"], {
            "direction": direction,
            "entry_price": row["close"],
            "quantity": qty,
            "sl": pattern.price_sl,
            "tp": pattern.price_tp,
            "pattern_type": pattern.pattern_type,
            "confidence": pattern.confidence,
            "pattern_notes": pattern.notes,
        })

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
            self._exit(pos, pos["sl"], row["time"], "SL", i)
        elif hit_tp:
            self._exit(pos, pos["tp"], row["time"], "TP", i)
        elif i == len(self.df) - 1:
            self._exit(pos, row["close"], row["time"], "end_of_data", i)

    def _exit(self, pos: Dict, exit_price: float, exit_time: datetime, reason: str, candle_idx: int):
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
            tags=["ict", pos["direction"], reason.lower(), pos["pattern"].pattern_type],
            notes=f"Pattern: {pos['pattern'].pattern_type} (conf: {pos['pattern'].confidence}) | {pos['pattern'].notes}",
        )
        self.trades.append(trade)

        self._emit_event("trade_exit", candle_idx, exit_time, {
            "direction": pos["direction"],
            "entry_price": pos["entry_price"],
            "exit_price": exit_price,
            "pnl": raw_pnl,
            "pnl_pct": pnl_pct,
            "reason": reason,
            "pattern_type": pos["pattern"].pattern_type,
        })

        self.position = None

    def _emit_event(self, event_type: str, candle_idx: int, timestamp: datetime, data: Dict):
        self.replay_events.append({
            "event_type": event_type,
            "candle_idx": candle_idx,
            "timestamp": timestamp.isoformat() if timestamp else None,
            "data": data,
        })

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
            self._exit(self.position, last_row["close"], last_row["time"], "end_of_data", len(self.df) - 1)

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

        peak = self.params.initial_balance
        max_dd = 0.0
        for val in self.equity_curve:
            if val > peak:
                peak = val
            dd = peak - val
            if dd > max_dd:
                max_dd = dd
        max_dd_pct = (max_dd / peak) if peak > 0 else 0

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
