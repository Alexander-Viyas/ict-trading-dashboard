"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { getLiveStatus, connectMt5 } from "@/lib/api";
import { Activity, Wifi, WifiOff, Zap, TrendingUp, TrendingDown } from "lucide-react";

interface LiveAlert {
  id: number;
  type: string;
  symbol: string;
  timeframe: string;
  pattern_type: string;
  direction: string;
  confidence: number;
  price_entry: number;
  time: string;
  notes?: string;
}

export default function LivePanel() {
  const [connected, setConnected] = useState(false);
  const [mt5Connected, setMt5Connected] = useState(false);
  const [alerts, setAlerts] = useState<LiveAlert[]>([]);
  const [status, setStatus] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const alertIdRef = useRef(0);

  const connectWebSocket = useCallback(() => {
    const wsUrl = `ws://127.0.0.1:8000/live/ws`;
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      setConnected(true);
      console.log("[WS] Connected");
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "pattern_alert") {
        const alert: LiveAlert = {
          id: ++alertIdRef.current,
          ...data,
        };
        setAlerts((prev) => [alert, ...prev].slice(0, 50));
      }
    };
    
    ws.onclose = () => {
      setConnected(false);
      console.log("[WS] Disconnected");
      // Auto-reconnect after 3s
      setTimeout(connectWebSocket, 3000);
    };
    
    ws.onerror = (err) => {
      console.error("[WS] Error:", err);
    };
    
    wsRef.current = ws;
  }, []);

  const loadStatus = async () => {
    try {
      const s = await getLiveStatus();
      setStatus(s);
      setMt5Connected(s.mt5_connected);
    } catch (e) {
      console.error("Status error:", e);
    }
  };

  const handleConnectMt5 = async () => {
    try {
      await connectMt5();
      await loadStatus();
    } catch (e) {
      console.error("MT5 connect error:", e);
    }
  };

  useEffect(() => {
    loadStatus();
    connectWebSocket();
    const interval = setInterval(loadStatus, 5000);
    return () => {
      clearInterval(interval);
      wsRef.current?.close();
    };
  }, [connectWebSocket]);

  const clearAlerts = () => setAlerts([]);

  return (
    <div className="space-y-4">
      {/* Status Header */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className={`rounded-lg p-3 border flex items-center gap-3 ${
          connected ? "bg-emerald-500/10 border-emerald-500/30" : "bg-rose-500/10 border-rose-500/30"
        }`}>
          {connected ? <Wifi className="w-5 h-5 text-emerald-400" /> : <WifiOff className="w-5 h-5 text-rose-400" />}
          <div>
            <div className="text-sm font-semibold">WebSocket</div>
            <div className="text-xs text-slate-400">{connected ? "Connected" : "Disconnected"}</div>
          </div>
        </div>
        
        <div className={`rounded-lg p-3 border flex items-center gap-3 ${
          mt5Connected ? "bg-emerald-500/10 border-emerald-500/30" : "bg-amber-500/10 border-amber-500/30"
        }`}>
          <Activity className={`w-5 h-5 ${mt5Connected ? "text-emerald-400" : "text-amber-400"}`} />
          <div>
            <div className="text-sm font-semibold">MT5 Bridge</div>
            <div className="text-xs text-slate-400">{mt5Connected ? "Online" : "Offline"}</div>
          </div>
        </div>
        
        <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Zap className="w-5 h-5 text-sky-400" />
            <div>
              <div className="text-sm font-semibold">Alerts</div>
              <div className="text-xs text-slate-400">{alerts.length} received</div>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleConnectMt5}
              className="px-3 py-1 bg-sky-500 text-white text-xs rounded hover:bg-sky-400 transition"
            >
              Connect MT5
            </button>
            <button
              onClick={clearAlerts}
              className="px-3 py-1 bg-slate-700 text-slate-300 text-xs rounded hover:bg-slate-600 transition"
            >
              Clear
            </button>
          </div>
        </div>
      </div>

      {/* Live Alerts Feed */}
      <div className="bg-slate-800/50 rounded-lg border border-slate-700">
        <div className="p-3 border-b border-slate-700 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-300">Live Pattern Alerts</h3>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${connected ? "bg-emerald-400 animate-pulse" : "bg-rose-400"}`} />
            <span className="text-xs text-slate-400">{connected ? "Listening..." : "Reconnecting..."}</span>
          </div>
        </div>
        
        <div className="max-h-[500px] overflow-y-auto">
          {alerts.length === 0 ? (
            <div className="p-8 text-center text-slate-500 text-sm">
              No live alerts yet. Connect MT5 and wait for patterns to form...
            </div>
          ) : (
            <div className="divide-y divide-slate-800">
              {alerts.map((alert) => (
                <div key={alert.id} className="p-3 hover:bg-slate-800/30 transition">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 text-[10px] rounded border ${
                        alert.direction === "bullish"
                          ? "text-emerald-400 border-emerald-400/30 bg-emerald-400/10"
                          : "text-rose-400 border-rose-400/30 bg-rose-400/10"
                      }`}>
                        {alert.direction === "bullish" ? (
                          <TrendingUp className="w-3 h-3 inline mr-1" />
                        ) : (
                          <TrendingDown className="w-3 h-3 inline mr-1" />
                        )}
                        {alert.direction.toUpperCase()}
                      </span>
                      <span className="text-xs text-slate-300 font-mono">{alert.symbol}</span>
                      <span className="text-xs text-slate-500">{alert.timeframe}</span>
                    </div>
                    <div className="text-xs font-mono">
                      <span className={alert.confidence >= 70 ? "text-emerald-400" : alert.confidence >= 50 ? "text-amber-400" : "text-rose-400"}>
                        {alert.confidence}%
                      </span>
                    </div>
                  </div>
                  <div className="mt-1 text-sm text-slate-200">
                    {alert.pattern_type.replace(/_/g, " ")}
                  </div>
                  <div className="mt-1 flex items-center gap-3 text-xs text-slate-400">
                    <span>Entry: <span className="text-sky-400">{alert.price_entry.toFixed(5)}</span></span>
                    <span>SL: <span className="text-rose-400">{alert.price_sl?.toFixed(5)}</span></span>
                    <span>TP: <span className="text-emerald-400">{alert.price_tp?.toFixed(5)}</span></span>
                  </div>
                  {alert.notes && (
                    <div className="mt-1 text-xs text-slate-500">{alert.notes}</div>
                  )}
                  <div className="mt-1 text-[10px] text-slate-600">{alert.time}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
