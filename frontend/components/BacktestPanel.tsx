"use client";

import { useState } from "react";
import { runBacktest, listCsvFiles, BacktestResult, BacktestParams } from "@/lib/api";
import PriceChart from "./PriceChart";
import EquityChart from "./EquityChart";
import StatCard from "./StatCard";
import { Play, Loader2 } from "lucide-react";

interface BacktestPanelProps {
  onResult?: (result: BacktestResult) => void;
}

export default function BacktestPanel({ onResult }: BacktestPanelProps) {
  const [params, setParams] = useState<BacktestParams>({
    strategy_name: "ict_smart_money",
    symbol: "EURUSD",
    timeframe: "M15",
    initial_balance: 10000,
    risk_per_trade: 0.01,
    csv_path: "sample/eurusd_m15.csv",
  });
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [csvFiles, setCsvFiles] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [ohlcvData, setOhlcvData] = useState<any[]>([]);

  const loadCsvList = async () => {
    const files = await listCsvFiles();
    setCsvFiles(files);
  };

  const handleRun = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await runBacktest(params);
      setResult(res);
      if (onResult) onResult(res);
      // Also load raw data for chart
      const raw = await import("@/lib/api").then((m) => m.loadCsv(params.csv_path, 500));
      setOhlcvData(raw.data || []);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Backtest failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="bg-ict-panel rounded-lg p-4 border border-slate-700">
        <h2 className="text-lg font-semibold text-ict-accent mb-3">Backtest Configuration</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Strategy</label>
            <select
              className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm"
              value={params.strategy_name}
              onChange={(e) => setParams({ ...params, strategy_name: e.target.value })}
            >
              <option value="ict_smart_money">ICT Smart Money</option>
              <option value="liquidity_sweep">Liquidity Sweep</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Symbol</label>
            <input
              className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm"
              value={params.symbol}
              onChange={(e) => setParams({ ...params, symbol: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Timeframe</label>
            <input
              className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm"
              value={params.timeframe}
              onChange={(e) => setParams({ ...params, timeframe: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Initial Balance</label>
            <input
              type="number"
              className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm"
              value={params.initial_balance}
              onChange={(e) => setParams({ ...params, initial_balance: Number(e.target.value) })}
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Risk / Trade</label>
            <input
              type="number"
              step={0.001}
              className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm"
              value={params.risk_per_trade}
              onChange={(e) => setParams({ ...params, risk_per_trade: Number(e.target.value) })}
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">CSV Path</label>
            <div className="flex gap-2">
              <input
                className="flex-1 bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm"
                placeholder="sample/eurusd_m15.csv"
                value={params.csv_path}
                onChange={(e) => setParams({ ...params, csv_path: e.target.value })}
                onFocus={loadCsvList}
              />
              <datalist id="csvFiles">
                {csvFiles.map((f) => (
                  <option key={f} value={f} />
                ))}
              </datalist>
            </div>
          </div>
        </div>
        <div className="mt-3 flex gap-2">
          <button
            onClick={handleRun}
            disabled={loading}
            className="flex items-center gap-2 bg-ict-accent text-slate-900 px-4 py-2 rounded font-semibold hover:bg-sky-400 transition disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            Run Backtest
          </button>
        </div>
        {error && <div className="mt-2 text-red-400 text-sm">{error}</div>}
      </div>

      {result && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatCard label="Total Return" value={`${result.total_return.toFixed(2)} (${result.total_return_pct.toFixed(2)}%)`} />
            <StatCard label="Win Rate" value={`${(result.win_rate * 100).toFixed(1)}%`} color={result.win_rate > 0.5 ? "text-ict-bull" : "text-ict-bear"} />
            <StatCard label="Profit Factor" value={result.profit_factor.toFixed(2)} />
            <StatCard label="Max Drawdown" value={`${result.max_drawdown.toFixed(2)} (${(result.max_drawdown_pct * 100).toFixed(1)}%)`} color="text-ict-bear" />
            <StatCard label="Sharpe" value={result.sharpe_ratio.toFixed(2)} />
            <StatCard label="Trades" value={result.trades.length} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-ict-panel rounded-lg p-3 border border-slate-700">
              <h3 className="text-sm font-semibold text-slate-300 mb-2">Equity Curve</h3>
              <EquityChart equityCurve={result.equity_curve} times={result.equity_times} />
            </div>
            {ohlcvData.length > 0 && (
              <div className="bg-ict-panel rounded-lg p-3 border border-slate-700">
                <h3 className="text-sm font-semibold text-slate-300 mb-2">Price Chart</h3>
                <PriceChart data={ohlcvData} height={300} />
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
