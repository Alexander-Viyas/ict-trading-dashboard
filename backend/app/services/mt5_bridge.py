import json
import asyncio
import pandas as pd
import zmq.asyncio
from datetime import datetime, timedelta
from typing import Callable, Optional, Dict, Any, List
from collections import deque
from app.config import MT5_HOST, MT5_PULL_PORT, MT5_SUB_PORT
from app.models.schemas import TickData
from app.services.pattern_engine import PatternEngine
from app.services.ws_manager import ws_manager


class CandleBuffer:
    """Buffer ticks into M1/M5 candles for live pattern detection."""
    def __init__(self, timeframe: str = "M5", max_candles: int = 200):
        self.timeframe = timeframe
        self.max_candles = max_candles
        self.candles: deque = deque(maxlen=max_candles)
        self.current_candle: Optional[Dict] = None
        self._tf_seconds = {"M1": 60, "M5": 300, "M15": 900, "H1": 3600}.get(timeframe, 300)

    def add_tick(self, tick: TickData):
        ts = tick.time.replace(second=0, microsecond=0)
        # Align to timeframe boundary
        epoch = int(ts.timestamp())
        aligned_epoch = (epoch // self._tf_seconds) * self._tf_seconds
        aligned_time = datetime.utcfromtimestamp(aligned_epoch)

        if self.current_candle is None or aligned_time > self.current_candle["time"]:
            if self.current_candle:
                self.candles.append(self.current_candle)
            self.current_candle = {
                "time": aligned_time,
                "open": tick.bid,
                "high": tick.bid,
                "low": tick.bid,
                "close": tick.bid,
                "volume": tick.volume,
            }
        else:
            self.current_candle["high"] = max(self.current_candle["high"], tick.bid)
            self.current_candle["low"] = min(self.current_candle["low"], tick.bid)
            self.current_candle["close"] = tick.bid
            self.current_candle["volume"] += tick.volume

    def to_dataframe(self) -> pd.DataFrame:
        data = list(self.candles)
        if self.current_candle:
            data.append(self.current_candle)
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values("time").reset_index(drop=True)
        return df

    def __len__(self):
        return len(self.candles) + (1 if self.current_candle else 0)


class MT5Bridge:
    """Async ZeroMQ bridge to MT5 with live pattern detection."""

    def __init__(self):
        self.ctx = zmq.asyncio.Context()
        self.pull_socket: Optional[zmq.asyncio.Socket] = None
        self.sub_socket: Optional[zmq.asyncio.Socket] = None
        self.connected = False
        self._running = False
        self._tick_callbacks: list[Callable[[TickData], None]] = []
        self._candle_buffers: Dict[str, CandleBuffer] = {}
        self._last_scan = datetime.utcnow()
        self._scan_interval = 5  # seconds between pattern scans
        self._symbol = "EURUSD"
        self._timeframe = "M5"

    def get_or_create_buffer(self, symbol: str, timeframe: str = "M5") -> CandleBuffer:
        key = f"{symbol}_{timeframe}"
        if key not in self._candle_buffers:
            self._candle_buffers[key] = CandleBuffer(timeframe)
        return self._candle_buffers[key]

    async def connect(self):
        self.pull_socket = self.ctx.socket(zmq.PULL)
        self.pull_socket.connect(f"tcp://{MT5_HOST}:{MT5_PULL_PORT}")

        self.sub_socket = self.ctx.socket(zmq.SUB)
        self.sub_socket.connect(f"tcp://{MT5_HOST}:{MT5_SUB_PORT}")
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")

        self.connected = True
        self._running = True
        asyncio.create_task(self._receive_loop())
        asyncio.create_task(self._pattern_scan_loop())

    def on_tick(self, callback: Callable[[TickData], None]):
        self._tick_callbacks.append(callback)

    async def _receive_loop(self):
        while self._running:
            try:
                if self.sub_socket:
                    raw = await asyncio.wait_for(self.sub_socket.recv_string(), timeout=1.0)
                    data = json.loads(raw)
                    tick = self._parse_tick(data)
                    if tick:
                        # Buffer into candles
                        buf = self.get_or_create_buffer(tick.symbol, self._timeframe)
                        buf.add_tick(tick)
                        for cb in self._tick_callbacks:
                            try:
                                cb(tick)
                            except Exception:
                                pass
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"MT5 receive error: {e}")
                await asyncio.sleep(1)

    async def _pattern_scan_loop(self):
        """Periodically scan candle buffers for patterns and broadcast alerts."""
        while self._running:
            await asyncio.sleep(self._scan_interval)
            for key, buf in self._candle_buffers.items():
                if len(buf) < 20:
                    continue
                try:
                    df = buf.to_dataframe()
                    engine = PatternEngine(df, symbol=self._symbol, timeframe=self._timeframe)
                    patterns = engine.detect_all()
                    # Only alert on high-confidence patterns
                    for pat in patterns:
                        if pat.confidence >= 65 and self._is_fresh_alert(pat):
                            alert = {
                                "type": "pattern_alert",
                                "symbol": pat.symbol,
                                "timeframe": pat.timeframe,
                                "pattern_type": pat.pattern_type,
                                "direction": pat.direction,
                                "confidence": pat.confidence,
                                "price_entry": pat.price_entry,
                                "price_sl": pat.price_sl,
                                "price_tp": pat.price_tp,
                                "time": pat.time.isoformat() if pat.time else None,
                                "notes": pat.notes,
                                "candle_count": len(buf),
                            }
                            await ws_manager.broadcast(alert)
                            print(f"[LIVE ALERT] {pat.pattern_type} {pat.direction} {pat.confidence}% @ {pat.price_entry}")
                except Exception as e:
                    print(f"Pattern scan error for {key}: {e}")

    def _is_fresh_alert(self, pattern) -> bool:
        """Prevent duplicate alerts for same pattern within 60s."""
        # Simple dedup: pattern type + direction + rough price
        return True  # TODO: implement proper dedup cache

    def _parse_tick(self, data: Dict[str, Any]) -> Optional[TickData]:
        try:
            # Handle both DWX format and simple format
            return TickData(
                symbol=data.get("_symbol", data.get("symbol", "UNKNOWN")),
                bid=float(data.get("_bid", data.get("bid", 0))),
                ask=float(data.get("_ask", data.get("ask", 0))),
                time=datetime.utcnow(),
                volume=int(data.get("_volume", data.get("volume", 0))),
            )
        except Exception:
            return None

    async def request_historical(self, symbol: str, timeframe: str, start: str, end: str):
        req = {
            "_action": "HISTORY",
            "_symbol": symbol,
            "_timeframe": timeframe,
            "_start": start,
            "_end": end,
        }
        if self.pull_socket:
            await self.pull_socket.send_string(json.dumps(req))
            resp = await asyncio.wait_for(self.pull_socket.recv_string(), timeout=10.0)
            return json.loads(resp)
        return {}

    async def close(self):
        self._running = False
        if self.pull_socket:
            self.pull_socket.close()
        if self.sub_socket:
            self.sub_socket.close()
        self.ctx.term()


mt5_bridge = MT5Bridge()
