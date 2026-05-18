import json
import asyncio
import zmq.asyncio
from datetime import datetime
from typing import Callable, Optional, Dict, Any
from app.config import MT5_HOST, MT5_PULL_PORT, MT5_SUB_PORT
from app.models.schemas import TickData


class MT5Bridge:
    """Async ZeroMQ bridge to MT5 via DWX ZeroMQ Connector pattern."""

    def __init__(self):
        self.ctx = zmq.asyncio.Context()
        self.pull_socket: Optional[zmq.asyncio.Socket] = None
        self.sub_socket: Optional[zmq.asyncio.Socket] = None
        self.connected = False
        self._running = False
        self._tick_callbacks: list[Callable[[TickData], None]] = []

    async def connect(self):
        self.pull_socket = self.ctx.socket(zmq.PULL)
        self.pull_socket.connect(f"tcp://{MT5_HOST}:{MT5_PULL_PORT}")

        self.sub_socket = self.ctx.socket(zmq.SUB)
        self.sub_socket.connect(f"tcp://{MT5_HOST}:{MT5_SUB_PORT}")
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")

        self.connected = True
        self._running = True
        asyncio.create_task(self._receive_loop())

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

    def _parse_tick(self, data: Dict[str, Any]) -> Optional[TickData]:
        try:
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
        """Request historical data from MT5 EA via PUSH/PULL."""
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
