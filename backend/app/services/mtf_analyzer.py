"""
Multi-Timeframe Pattern Analyzer
Resamples data to M15/H1, detects patterns on each timeframe,
computes confluence scores across timeframes.
Higher timeframe patterns carry more weight.
"""

import pandas as pd
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from app.services.pattern_engine import PatternEngine, Pattern


@dataclass
class ConfluencePattern:
    base_pattern: Pattern
    higher_timeframe_patterns: List[Dict[str, Any]]
    confluence_score: float  # 0-100
    alignment: str  # "strong", "neutral", "conflict"
    summary: str


TIMEFRAME_WEIGHTS = {
    "M5": 1.0,
    "M15": 2.0,
    "H1": 3.0,
    "H4": 4.0,
    "D1": 5.0,
}


def resample_ohlcv(df: pd.DataFrame, target_tf: str) -> pd.DataFrame:
    """Resample OHLCV data to higher timeframe."""
    df = df.copy()
    df["time"] = pd.to_datetime(df["time"])
    df.set_index("time", inplace=True)

    freq = {
        "M5": "5T", "M15": "15T", "M30": "30T",
        "H1": "1H", "H4": "4H", "D1": "1D",
    }.get(target_tf, "15T")

    resampled = df.resample(freq).agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }).dropna()

    resampled.reset_index(inplace=True)
    return resampled


class MultiTimeframeAnalyzer:
    def __init__(
        self,
        df: pd.DataFrame,
        symbol: str = "EURUSD",
        base_timeframe: str = "M5",
        higher_timeframes: Optional[List[str]] = None,
        lookback_window: int = 50,
    ):
        self.df = df.copy()
        self.symbol = symbol
        self.base_timeframe = base_timeframe
        self.higher_timeframes = higher_timeframes or ["M15", "H1"]
        self.lookback_window = lookback_window
        self.pattern_cache: Dict[str, List[Pattern]] = {}

    def detect_all_timeframes(self) -> Dict[str, List[Pattern]]:
        """Detect patterns on base + all higher timeframes."""
        result = {}

        # Base timeframe
        engine_base = PatternEngine(self.df, symbol=self.symbol, timeframe=self.base_timeframe)
        result[self.base_timeframe] = engine_base.detect_all()
        self.pattern_cache[self.base_timeframe] = result[self.base_timeframe]

        # Higher timeframes
        for tf in self.higher_timeframes:
            resampled = resample_ohlcv(self.df, tf)
            if len(resampled) < 20:
                continue
            engine = PatternEngine(resampled, symbol=self.symbol, timeframe=tf)
            result[tf] = engine.detect_all()
            self.pattern_cache[tf] = result[tf]

        return result

    def find_confluence(self, tf_patterns: Dict[str, List[Pattern]]) -> List[ConfluencePattern]:
        """For each base pattern, check if higher TFs align."""
        base_patterns = tf_patterns.get(self.base_timeframe, [])
        confluence_results: List[ConfluencePattern] = []

        for bp in base_patterns:
            htf_matches = []
            alignment_scores = []

            for tf in self.higher_timeframes:
                htf_pats = tf_patterns.get(tf, [])
                # Find patterns within time proximity (same direction, similar price zone)
                for hp in htf_pats:
                    # Time proximity: base pattern time should be within htf candle range
                    time_diff = abs((pd.to_datetime(bp.time) - pd.to_datetime(hp.time)).total_seconds())
                    # Price proximity: within 2x ATR range
                    price_diff = abs(bp.price_entry - hp.price_entry)
                    price_range = max(bp.price_top - bp.price_bottom, hp.price_top - hp.price_bottom, 0.0001)

                    if time_diff <= 900 * TIMEFRAME_WEIGHTS.get(tf, 1):  # 15 min * weight
                        if price_diff <= price_range * 2:
                            if bp.direction == hp.direction:
                                # Aligned
                                weight = TIMEFRAME_WEIGHTS.get(tf, 1)
                                score = (bp.confidence + hp.confidence) / 2 * weight
                                htf_matches.append({
                                    "timeframe": tf,
                                    "pattern": hp,
                                    "weight": weight,
                                    "score": score,
                                    "aligned": True,
                                })
                                alignment_scores.append(score)
                            else:
                                # Conflict
                                weight = TIMEFRAME_WEIGHTS.get(tf, 1)
                                htf_matches.append({
                                    "timeframe": tf,
                                    "pattern": hp,
                                    "weight": weight,
                                    "score": -weight * 20,
                                    "aligned": False,
                                })
                                alignment_scores.append(-weight * 20)

            # Compute confluence score
            base_weight = TIMEFRAME_WEIGHTS.get(self.base_timeframe, 1)
            base_score = bp.confidence * base_weight

            if alignment_scores:
                total_score = base_score + sum(alignment_scores)
                max_possible = base_score + sum(TIMEFRAME_WEIGHTS.get(tf, 1) * 100 for tf in self.higher_timeframes)
                confluence_pct = min(100, max(0, (total_score / max(max_possible, 1)) * 100))
            else:
                confluence_pct = bp.confidence * 0.5  # No confluence = halved confidence

            # Determine alignment
            aligned_count = sum(1 for m in htf_matches if m["aligned"])
            conflict_count = sum(1 for m in htf_matches if not m["aligned"])

            if conflict_count > aligned_count:
                alignment = "conflict"
                summary = f"{bp.pattern_type} on {self.base_timeframe} conflicts with higher timeframe signals"
            elif aligned_count >= 2:
                alignment = "strong"
                summary = f"Strong {bp.direction} confluence: {bp.pattern_type} aligned across {aligned_count + 1} timeframes"
            elif aligned_count == 1:
                alignment = "neutral"
                summary = f"Moderate {bp.direction} confluence: {bp.pattern_type} aligned with 1 higher timeframe"
            else:
                alignment = "neutral"
                summary = f"No higher timeframe confluence for {bp.pattern_type}"

            # Boost base pattern's confidence with confluence
            bp.confluence_score = round(confluence_pct, 1)

            confluence_results.append(ConfluencePattern(
                base_pattern=bp,
                higher_timeframe_patterns=htf_matches,
                confluence_score=round(confluence_pct, 1),
                alignment=alignment,
                summary=summary,
            ))

        # Sort by confluence score descending
        confluence_results.sort(key=lambda x: x.confluence_score, reverse=True)
        return confluence_results

    def get_top_confluence(self, min_score: float = 50, limit: int = 20) -> List[ConfluencePattern]:
        """Get top confluence patterns."""
        all_tf = self.detect_all_timeframes()
        confluence = self.find_confluence(all_tf)
        filtered = [c for c in confluence if c.confluence_score >= min_score]
        return filtered[:limit]

    def get_confluence_at_candle(self, candle_time: pd.Timestamp) -> List[ConfluencePattern]:
        """Get confluence patterns active at a specific candle time."""
        all_tf = self.detect_all_timeframes()
        confluence = self.find_confluence(all_tf)
        return [c for c in confluence if abs(
            (pd.to_datetime(c.base_pattern.time) - pd.to_datetime(candle_time)).total_seconds()
        ) < 60]
