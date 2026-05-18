"""
ICT Pattern Detection Engine
Detects: FVG, Order Blocks, BOS/CHoCH, Liquidity Sweeps,
         Breaker Blocks, Mitigation Blocks, Killzone Sessions
Confidence: 0-100 structural quality score
"""

from dataclasses import dataclass, field
from typing import List, Optional, Literal
from datetime import datetime
import pandas as pd
import numpy as np


@dataclass
class Pattern:
    id: Optional[int] = None
    pattern_type: str = ""
    direction: Literal["bullish", "bearish", "neutral"] = "neutral"
    confidence: int = 0
    time: Optional[datetime] = None
    symbol: str = ""
    timeframe: str = ""
    
    # Price levels for chart annotation
    price_top: float = 0.0
    price_bottom: float = 0.0
    price_entry: float = 0.0
    price_sl: float = 0.0
    price_tp: float = 0.0
    
    # Context
    candle_start_idx: int = 0
    candle_end_idx: int = 0
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    
    # For live / backtest linking
    trade_id: Optional[int] = None
    outcome: Optional[str] = None  # "win", "loss", "pending"


class PatternEngine:
    def __init__(self, df: pd.DataFrame, symbol: str = "", timeframe: str = ""):
        self.df = df.reset_index(drop=True)
        self.symbol = symbol
        self.timeframe = timeframe
        self.patterns: List[Pattern] = []
        
        # Precompute ATR for confidence scoring
        self.atr = self._compute_atr(14)
        
    def _compute_atr(self, period: int = 14) -> pd.Series:
        high_low = self.df["high"] - self.df["low"]
        high_close = np.abs(self.df["high"] - self.df["close"].shift())
        low_close = np.abs(self.df["low"] - self.df["close"].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(period, min_periods=1).mean()
    
    def detect_all(self) -> List[Pattern]:
        """Run all pattern detectors."""
        self.patterns = []
        self._detect_fvg()
        self._detect_order_blocks()
        self._detect_bos_choch()
        self._detect_liquidity_sweeps()
        self._detect_breaker_blocks()
        self._detect_mitigation_blocks()
        self._tag_killzones()
        
        # Sort by time
        self.patterns.sort(key=lambda p: p.time or datetime.min)
        return self.patterns
    
    def _detect_fvg(self):
        """Fair Value Gaps: 3-candle imbalance."""
        for i in range(2, len(self.df)):
            c1 = self.df.iloc[i-2]
            c2 = self.df.iloc[i-1]
            c3 = self.df.iloc[i]
            
            # Bullish FVG: c2 low > c1 high (gap up)
            if c2["low"] > c1["high"]:
                gap_size = c2["low"] - c1["high"]
                atr_val = self.atr.iloc[i]
                confidence = min(100, int((gap_size / max(atr_val * 0.1, 1e-9)) * 50))
                
                self.patterns.append(Pattern(
                    pattern_type="fvg_bullish",
                    direction="bullish",
                    confidence=confidence,
                    time=c3["time"],
                    symbol=self.symbol,
                    timeframe=self.timeframe,
                    price_top=c2["low"],
                    price_bottom=c1["high"],
                    price_entry=c2["low"],
                    price_sl=c1["low"] - atr_val * 0.5,
                    price_tp=c2["low"] + atr_val * 2.0,
                    candle_start_idx=i-2,
                    candle_end_idx=i,
                    notes=f"Bullish FVG, gap={gap_size:.5f}, ATR={atr_val:.5f}",
                    tags=["fvg", "bullish", "imbalance"]
                ))
            
            # Bearish FVG: c2 high < c1 low (gap down)
            if c2["high"] < c1["low"]:
                gap_size = c1["low"] - c2["high"]
                atr_val = self.atr.iloc[i]
                confidence = min(100, int((gap_size / max(atr_val * 0.1, 1e-9)) * 50))
                
                self.patterns.append(Pattern(
                    pattern_type="fvg_bearish",
                    direction="bearish",
                    confidence=confidence,
                    time=c3["time"],
                    symbol=self.symbol,
                    timeframe=self.timeframe,
                    price_top=c1["low"],
                    price_bottom=c2["high"],
                    price_entry=c2["high"],
                    price_sl=c1["high"] + atr_val * 0.5,
                    price_tp=c2["high"] - atr_val * 2.0,
                    candle_start_idx=i-2,
                    candle_end_idx=i,
                    notes=f"Bearish FVG, gap={gap_size:.5f}, ATR={atr_val:.5f}",
                    tags=["fvg", "bearish", "imbalance"]
                ))
    
    def _detect_order_blocks(self):
        """Order Blocks: last opposing candle before a strong impulse."""
        lookback = 5
        for i in range(lookback + 3, len(self.df)):
            window = self.df.iloc[i-lookback:i+1]
            
            # Find strongest bullish impulse (last candle big green)
            last = window.iloc[-1]
            if last["close"] > last["open"]:
                body = last["close"] - last["open"]
                atr_val = self.atr.iloc[i]
                if body > atr_val * 0.5:
                    # Look for last bearish candle before impulse
                    for j in range(len(window)-2, -1, -1):
                        candle = window.iloc[j]
                        if candle["close"] < candle["open"]:
                            confidence = min(100, int((body / max(atr_val * 0.1, 1e-9)) * 40))
                            self.patterns.append(Pattern(
                                pattern_type="order_block_bullish",
                                direction="bullish",
                                confidence=confidence,
                                time=last["time"],
                                symbol=self.symbol,
                                timeframe=self.timeframe,
                                price_top=candle["high"],
                                price_bottom=candle["low"],
                                price_entry=candle["high"],
                                price_sl=candle["low"] - atr_val * 0.3,
                                price_tp=candle["high"] + atr_val * 2.0,
                                candle_start_idx=i-lookback+j,
                                candle_end_idx=i,
                                notes=f"Bullish OB, impulse body={body:.5f}",
                                tags=["order_block", "bullish"]
                            ))
                            break
            
            # Bearish impulse
            if last["close"] < last["open"]:
                body = last["open"] - last["close"]
                atr_val = self.atr.iloc[i]
                if body > atr_val * 0.5:
                    for j in range(len(window)-2, -1, -1):
                        candle = window.iloc[j]
                        if candle["close"] > candle["open"]:
                            confidence = min(100, int((body / max(atr_val * 0.1, 1e-9)) * 40))
                            self.patterns.append(Pattern(
                                pattern_type="order_block_bearish",
                                direction="bearish",
                                confidence=confidence,
                                time=last["time"],
                                symbol=self.symbol,
                                timeframe=self.timeframe,
                                price_top=candle["high"],
                                price_bottom=candle["low"],
                                price_entry=candle["low"],
                                price_sl=candle["high"] + atr_val * 0.3,
                                price_tp=candle["low"] - atr_val * 2.0,
                                candle_start_idx=i-lookback+j,
                                candle_end_idx=i,
                                notes=f"Bearish OB, impulse body={body:.5f}",
                                tags=["order_block", "bearish"]
                            ))
                            break
    
    def _detect_bos_choch(self):
        """Break of Structure / Change of Character."""
        swing_window = 10
        for i in range(swing_window * 2, len(self.df)):
            recent = self.df.iloc[i-swing_window:i]
            prev = self.df.iloc[i-swing_window*2:i-swing_window]
            
            prev_high = prev["high"].max()
            prev_low = prev["low"].min()
            recent_high = recent["high"].max()
            recent_low = recent["low"].min()
            
            atr_val = self.atr.iloc[i]
            
            # BOS Bullish: breaks above previous swing high
            if recent_high > prev_high:
                confidence = min(100, int(((recent_high - prev_high) / max(atr_val * 0.1, 1e-9)) * 60))
                self.patterns.append(Pattern(
                    pattern_type="bos_bullish",
                    direction="bullish",
                    confidence=confidence,
                    time=self.df.iloc[i]["time"],
                    symbol=self.symbol,
                    timeframe=self.timeframe,
                    price_top=recent_high,
                    price_bottom=prev_low,
                    price_entry=recent_high,
                    price_sl=recent_low - atr_val * 0.5,
                    price_tp=recent_high + atr_val * 2.0,
                    candle_start_idx=i-swing_window*2,
                    candle_end_idx=i,
                    notes=f"Bullish BOS, broke {prev_high:.5f}",
                    tags=["bos", "bullish", "structure"]
                ))
            
            # BOS Bearish: breaks below previous swing low
            if recent_low < prev_low:
                confidence = min(100, int(((prev_low - recent_low) / max(atr_val * 0.1, 1e-9)) * 60))
                self.patterns.append(Pattern(
                    pattern_type="bos_bearish",
                    direction="bearish",
                    confidence=confidence,
                    time=self.df.iloc[i]["time"],
                    symbol=self.symbol,
                    timeframe=self.timeframe,
                    price_top=prev_high,
                    price_bottom=recent_low,
                    price_entry=recent_low,
                    price_sl=recent_high + atr_val * 0.5,
                    price_tp=recent_low - atr_val * 2.0,
                    candle_start_idx=i-swing_window*2,
                    candle_end_idx=i,
                    notes=f"Bearish BOS, broke {prev_low:.5f}",
                    tags=["bos", "bearish", "structure"]
                ))
    
    def _detect_liquidity_sweeps(self):
        """Liquidity Sweeps: wick above/below key level with reversal."""
        lookback = 20
        for i in range(lookback + 2, len(self.df)):
            window = self.df.iloc[i-lookback:i]
            prev_high = window["high"].max()
            prev_low = window["low"].min()
            
            current = self.df.iloc[i]
            prev = self.df.iloc[i-1]
            atr_val = self.atr.iloc[i]
            
            # Bullish sweep: wick below prev low, then close green above
            if prev["low"] < prev_low * 1.0001 and current["close"] > current["open"]:
                wick_size = prev["high"] - prev["low"]
                confidence = min(100, int((wick_size / max(atr_val * 0.1, 1e-9)) * 35))
                self.patterns.append(Pattern(
                    pattern_type="liquidity_sweep_bullish",
                    direction="bullish",
                    confidence=confidence,
                    time=current["time"],
                    symbol=self.symbol,
                    timeframe=self.timeframe,
                    price_top=current["high"],
                    price_bottom=prev["low"],
                    price_entry=current["close"],
                    price_sl=prev["low"] - atr_val * 0.3,
                    price_tp=current["close"] + atr_val * 2.5,
                    candle_start_idx=i-1,
                    candle_end_idx=i,
                    notes=f"Bullish liquidity sweep at {prev['low']:.5f}",
                    tags=["liquidity_sweep", "bullish", "reversal"]
                ))
            
            # Bearish sweep: wick above prev high, then close red below
            if prev["high"] > prev_high * 0.9999 and current["close"] < current["open"]:
                wick_size = prev["high"] - prev["low"]
                confidence = min(100, int((wick_size / max(atr_val * 0.1, 1e-9)) * 35))
                self.patterns.append(Pattern(
                    pattern_type="liquidity_sweep_bearish",
                    direction="bearish",
                    confidence=confidence,
                    time=current["time"],
                    symbol=self.symbol,
                    timeframe=self.timeframe,
                    price_top=prev["high"],
                    price_bottom=current["low"],
                    price_entry=current["close"],
                    price_sl=prev["high"] + atr_val * 0.3,
                    price_tp=current["close"] - atr_val * 2.5,
                    candle_start_idx=i-1,
                    candle_end_idx=i,
                    notes=f"Bearish liquidity sweep at {prev['high']:.5f}",
                    tags=["liquidity_sweep", "bearish", "reversal"]
                ))
    
    def _detect_breaker_blocks(self):
        """Breaker Blocks: failed order block that flips role."""
        # Simplified: find OB that was mitigated, then price breaks through it
        # For now, detect as strong reversal through prior OB zone
        for i in range(5, len(self.df)):
            current = self.df.iloc[i]
            prev = self.df.iloc[i-1]
            atr_val = self.atr.iloc[i]
            
            # Bullish breaker: prior bearish OB broken to upside
            if current["close"] > current["open"]:
                # Check if we broke above recent consolidation high
                recent_high = self.df.iloc[i-5:i]["high"].max()
                if current["close"] > recent_high and prev["close"] < prev["open"]:
                    confidence = min(100, int((current["close"] - prev["close"]) / max(atr_val * 0.1, 1e-9) * 40))
                    self.patterns.append(Pattern(
                        pattern_type="breaker_block_bullish",
                        direction="bullish",
                        confidence=confidence,
                        time=current["time"],
                        symbol=self.symbol,
                        timeframe=self.timeframe,
                        price_top=current["high"],
                        price_bottom=prev["low"],
                        price_entry=current["close"],
                        price_sl=prev["low"],
                        price_tp=current["close"] + atr_val * 2.0,
                        candle_start_idx=i-5,
                        candle_end_idx=i,
                        notes="Bullish breaker block",
                        tags=["breaker_block", "bullish"]
                    ))
            
            # Bearish breaker
            if current["close"] < current["open"]:
                recent_low = self.df.iloc[i-5:i]["low"].min()
                if current["close"] < recent_low and prev["close"] > prev["open"]:
                    confidence = min(100, int((prev["close"] - current["close"]) / max(atr_val * 0.1, 1e-9) * 40))
                    self.patterns.append(Pattern(
                        pattern_type="breaker_block_bearish",
                        direction="bearish",
                        confidence=confidence,
                        time=current["time"],
                        symbol=self.symbol,
                        timeframe=self.timeframe,
                        price_top=prev["high"],
                        price_bottom=current["low"],
                        price_entry=current["close"],
                        price_sl=prev["high"],
                        price_tp=current["close"] - atr_val * 2.0,
                        candle_start_idx=i-5,
                        candle_end_idx=i,
                        notes="Bearish breaker block",
                        tags=["breaker_block", "bearish"]
                    ))
    
    def _detect_mitigation_blocks(self):
        """Mitigation Blocks: price returns to fill/mitigate a prior FVG/OB."""
        # Find recent FVGs and check if price returned to them
        fvgs = [p for p in self.patterns if "fvg" in p.pattern_type]
        
        for fvg in fvgs:
            start_idx = fvg.candle_end_idx
            end_idx = min(start_idx + 50, len(self.df))  # Look 50 candles ahead
            
            for i in range(start_idx, end_idx):
                candle = self.df.iloc[i]
                
                if fvg.direction == "bullish":
                    # Price comes back into FVG zone (mitigation)
                    if candle["low"] <= fvg.price_top and candle["high"] >= fvg.price_bottom:
                        if candle["close"] > candle["open"]:  # Rejection bullish
                            self.patterns.append(Pattern(
                                pattern_type="mitigation_block_bullish",
                                direction="bullish",
                                confidence=min(100, fvg.confidence + 10),
                                time=candle["time"],
                                symbol=self.symbol,
                                timeframe=self.timeframe,
                                price_top=fvg.price_top,
                                price_bottom=fvg.price_bottom,
                                price_entry=candle["close"],
                                price_sl=fvg.price_bottom - self.atr.iloc[i] * 0.3,
                                price_tp=candle["close"] + self.atr.iloc[i] * 2.0,
                                candle_start_idx=fvg.candle_start_idx,
                                candle_end_idx=i,
                                notes=f"Mitigation of {fvg.pattern_type} at {fvg.price_bottom:.5f}-{fvg.price_top:.5f}",
                                tags=["mitigation", "bullish", "fvg_fill"]
                            ))
                            break
                else:
                    # Bearish mitigation
                    if candle["high"] >= fvg.price_bottom and candle["low"] <= fvg.price_top:
                        if candle["close"] < candle["open"]:
                            self.patterns.append(Pattern(
                                pattern_type="mitigation_block_bearish",
                                direction="bearish",
                                confidence=min(100, fvg.confidence + 10),
                                time=candle["time"],
                                symbol=self.symbol,
                                timeframe=self.timeframe,
                                price_top=fvg.price_top,
                                price_bottom=fvg.price_bottom,
                                price_entry=candle["close"],
                                price_sl=fvg.price_top + self.atr.iloc[i] * 0.3,
                                price_tp=candle["close"] - self.atr.iloc[i] * 2.0,
                                candle_start_idx=fvg.candle_start_idx,
                                candle_end_idx=i,
                                notes=f"Mitigation of {fvg.pattern_type} at {fvg.price_bottom:.5f}-{fvg.price_top:.5f}",
                                tags=["mitigation", "bearish", "fvg_fill"]
                            ))
                            break
    
    def _tag_killzones(self):
        """Tag patterns that occurred during ICT killzones."""
        for p in self.patterns:
            if not p.time:
                continue
            
            t = p.time
            # Convert to weekday and hour (naive UTC for now)
            hour = t.hour
            weekday = t.weekday()
            
            # London Killzone: 8:00-10:00 AM GMT (roughly 8-10 UTC)
            # NY Killzone AM: 9:30-11:30 AM EST (roughly 14:30-16:30 UTC)
            # NY Killzone PM: 1:00-3:00 PM EST (roughly 18:00-20:00 UTC)
            # Asia: 8:00-11:00 PM EST previous day (roughly 1:00-4:00 UTC)
            
            if 8 <= hour < 10:
                p.tags.append("killzone_london")
                p.notes += " | London Killzone"
            elif 14 <= hour < 16:
                p.tags.append("killzone_ny_am")
                p.notes += " | NY AM Killzone"
            elif 18 <= hour < 20:
                p.tags.append("killzone_ny_pm")
                p.notes += " | NY PM Killzone"
            elif 1 <= hour < 4:
                p.tags.append("killzone_asia")
                p.notes += " | Asia Killzone"
    
    def filter_by_time_range(self, start: datetime, end: datetime) -> List[Pattern]:
        return [p for p in self.patterns if p.time and start <= p.time <= end]
    
    def filter_by_killzone(self, zones: List[str]) -> List[Pattern]:
        """zones: ['killzone_london', 'killzone_ny_am', etc.]"""
        return [p for p in self.patterns if any(z in p.tags for z in zones)]
    
    def filter_by_confidence(self, min_conf: int = 0) -> List[Pattern]:
        return [p for p in self.patterns if p.confidence >= min_conf]
    
    def get_patterns_for_candle(self, idx: int) -> List[Pattern]:
        """Get all patterns that span or start at a given candle index."""
        return [p for p in self.patterns if p.candle_start_idx <= idx <= p.candle_end_idx]
