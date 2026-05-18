"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { getReplayEvents, getBacktestOhlcv, ReplayEvent } from "@/lib/api";
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time } from "lightweight-charts";
import { Play, Pause, SkipForward, SkipBack, Settings, ChevronRight } from "lucide-react";

interface ReplayState {
  candleIdx: number;
  isPlaying: boolean;
  speed: number;
  currentEvent: ReplayEvent | null;
}

export default function ReplayPlayer() {
  const [events, setEvents] = useState<ReplayEvent[]>([]);
  const [ohlcv, setOhlcv] = useState<any[]>([]);
  const [state, setState] = useState<ReplayState>({
    candleIdx: 0,
    isPlaying: false,
    speed: 5,
    currentEvent: null,
  });
  const [tradeDetails, setTradeDetails] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const markersRef = useRef<any[]>([]);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Load replay data
  useEffect(() => {
    const load = async () => {
      try {
        const [evs, data] = await Promise.all([
          getReplayEvents(),
          getBacktestOhlcv(),
        ]);
        setEvents(evs);
        setOhlcv(data);
      } catch (err) {
        console.error("No replay data. Run a backtest first.", err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  // Init chart
  useEffect(() => {
    if (!chartContainerRef.current || ohlcv.length === 0) return;
    
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 400,
      layout: {
        background: { color: "#0f172a" },
        textColor: "#94a3b8",
      },
      grid: {
        vertLines: { color: "#1e293b" },
        horzLines: { color: "#1e293b" },
      },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: "#334155" },
      timeScale: { borderColor: "#334155", timeVisible: true },
    });
    
    const series = chart.addCandlestickSeries({
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });
    
    chartRef.current = chart;
    seriesRef.current = series;
    
    return () => chart.remove();
  }, [ohlcv.length]);

  // Update chart as replay progresses
  useEffect(() => {
    if (!seriesRef.current || ohlcv.length === 0) return;
    
    const visibleData = ohlcv.slice(0, state.candleIdx + 1).map((d: any) => ({
      time: (Date.parse(d.time) / 1000) as Time,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }));
    
    seriesRef.current.setData(visibleData);
    
    // Check for events at current candle
    const currentEvents = events.filter((e) => e.candle_idx === state.candleIdx);
    const tradeEntry = currentEvents.find((e) => e.event_type === "trade_entry");
    const tradeExit = currentEvents.find((e) => e.event_type === "trade_exit");
    const pattern = currentEvents.find((e) => e.event_type === "pattern");
    
    if (tradeEntry) {
      setState((s) => ({ ...s, isPlaying: false, currentEvent: tradeEntry }));
      setTradeDetails({
        type: "ENTRY",
        ...tradeEntry.data,
        time: tradeEntry.timestamp,
      });
    } else if (tradeExit) {
      setState((s) => ({ ...s, isPlaying: false, currentEvent: tradeExit }));
      setTradeDetails({
        type: "EXIT",
        ...tradeExit.data,
        time: tradeExit.timestamp,
      });
    } else if (pattern) {
      setState((s) => ({ ...s, currentEvent: pattern }));
    }
  }, [state.candleIdx, ohlcv, events]);

  const play = useCallback(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    
    intervalRef.current = setInterval(() => {
      setState((prev) => {
        if (prev.candleIdx >= ohlcv.length - 1) {
          return { ...prev, isPlaying: false };
        }
        return { ...prev, candleIdx: prev.candleIdx + 1 };
      });
    }, Math.max(50, 500 / state.speed));
    
    setState((s) => ({ ...s, isPlaying: true }));
  }, [ohlcv.length, state.speed]);

  const pause = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setState((s) => ({ ...s, isPlaying: false }));
  }, []);

  const step = useCallback((dir: number) => {
    pause();
    setState((prev) => ({
      ...prev,
      candleIdx: Math.max(0, Math.min(ohlcv.length - 1, prev.candleIdx + dir)),
    }));
  }, [ohlcv.length, pause]);

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  if (loading) {
    return <div className="text-slate-400 p-4">Loading replay data... (Run a backtest first)</div>;
  }

  if (events.length === 0 || ohlcv.length === 0) {
    return (
      <div className="bg-slate-800/50 rounded-lg p-8 border border-slate-700 text-center">
        <div className="text-slate-400 mb-2">No replay data available.</div>
        <div className="text-sm text-slate-500">Run a backtest first to generate replay events.</div>
      </div>
    );
  }

  const progress = ohlcv.length > 0 ? (state.candleIdx / (ohlcv.length - 1)) * 100 : 0;

  return (
    <div className="space-y-4">
      {/* Chart */}
      <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-slate-300">Backtest Replay</h3>
          <div className="text-xs text-slate-400">
            Candle {state.candleIdx + 1} / {ohlcv.length}
          </div>
        </div>
        <div ref={chartContainerRef} className="w-full" />
      </div>

      {/* Controls */}
      <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700 space-y-3">
        {/* Progress */}
        <div className="w-full bg-slate-700 rounded-full h-2">
          <div
            className="bg-sky-500 h-2 rounded-full transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button onClick={() => step(-1)} className="p-2 bg-slate-700 rounded hover:bg-slate-600 transition">
              <SkipBack className="w-4 h-4" />
            </button>
            <button
              onClick={state.isPlaying ? pause : play}
              className="p-2 bg-sky-500 text-white rounded hover:bg-sky-400 transition"
            >
              {state.isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
            </button>
            <button onClick={() => step(1)} className="p-2 bg-slate-700 rounded hover:bg-slate-600 transition">
              <SkipForward className="w-4 h-4" />
            </button>
            <button onClick={() => step(10)} className="p-2 bg-slate-700 rounded hover:bg-slate-600 transition" title="Skip 10 candles">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Settings className="w-4 h-4 text-slate-400" />
              <span className="text-xs text-slate-400">Speed:</span>
              <input
                type="range"
                min={1}
                max={50}
                value={state.speed}
                onChange={(e) => setState((s) => ({ ...s, speed: Number(e.target.value) }))}
                className="w-24"
              />
              <span className="text-xs text-slate-300 w-8">{state.speed}x</span>
            </div>
          </div>
        </div>
      </div>

      {/* Trade Details Panel */}
      {tradeDetails && (
        <div className={`rounded-lg p-4 border space-y-2 ${
          tradeDetails.type === "ENTRY"
            ? "bg-sky-500/10 border-sky-500/30"
            : tradeDetails.data?.pnl > 0
            ? "bg-emerald-500/10 border-emerald-500/30"
            : "bg-rose-500/10 border-rose-500/30"
        }`}>
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">
              {tradeDetails.type === "ENTRY" ? "🎯 Trade Entry" : tradeDetails.data?.pnl > 0 ? "✅ Trade Exit (Win)" : "❌ Trade Exit (Loss)"}
            </h3>
            <button onClick={() => setTradeDetails(null)} className="text-slate-400 hover:text-white text-xs">✕</button>
          </div>
          
          {tradeDetails.type === "ENTRY" && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
              <div><span className="text-slate-400">Direction:</span> <span className={tradeDetails.direction === "long" ? "text-emerald-400" : "text-rose-400"}>{tradeDetails.direction.toUpperCase()}</span></div>
              <div><span className="text-slate-400">Entry:</span> <span className="text-sky-400">{tradeDetails.entry_price.toFixed(5)}</span></div>
              <div><span className="text-slate-400">Quantity:</span> {tradeDetails.quantity.toFixed(2)}</div>
              <div><span className="text-slate-400">Stop Loss:</span> <span className="text-rose-400">{tradeDetails.sl.toFixed(5)}</span></div>
              <div><span className="text-slate-400">Take Profit:</span> <span className="text-emerald-400">{tradeDetails.tp.toFixed(5)}</span></div>
              <div><span className="text-slate-400">Pattern:</span> {tradeDetails.pattern_type}</div>
              <div><span className="text-slate-400">Confidence:</span> {tradeDetails.confidence}%</div>
              <div className="col-span-2 md:col-span-3"><span className="text-slate-400">Why:</span> <span className="text-slate-300">{tradeDetails.pattern_notes}</span></div>
            </div>
          )}
          
          {tradeDetails.type === "EXIT" && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
              <div><span className="text-slate-400">Direction:</span> <span className={tradeDetails.direction === "long" ? "text-emerald-400" : "text-rose-400"}>{tradeDetails.direction.toUpperCase()}</span></div>
              <div><span className="text-slate-400">Entry:</span> {tradeDetails.entry_price.toFixed(5)}</div>
              <div><span className="text-slate-400">Exit:</span> {tradeDetails.exit_price.toFixed(5)}</div>
              <div><span className="text-slate-400">P&L:</span> <span className={tradeDetails.pnl > 0 ? "text-emerald-400" : "text-rose-400"}>{tradeDetails.pnl.toFixed(2)} ({(tradeDetails.pnl_pct * 100).toFixed(2)}%)</span></div>
              <div><span className="text-slate-400">Reason:</span> {tradeDetails.reason}</div>
              <div><span className="text-slate-400">Pattern:</span> {tradeDetails.pattern_type}</div>
            </div>
          )}
        </div>
      )}

      {/* Current Event */}
      {state.currentEvent && state.currentEvent.event_type === "pattern" && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-amber-400 font-semibold">📊 Pattern Detected:</span>
            <span>{state.currentEvent.data.pattern_type}</span>
            <span className="text-slate-400">({state.currentEvent.data.confidence}% confidence)</span>
          </div>
        </div>
      )}
    </div>
  );
}
