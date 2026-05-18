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
    start_date: undefined,
    end_date: undefined,
    killzones: [],
  });
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [csvFiles, setCsvFiles] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [ohlcvData, setOhlcvData] = useState<any[]>([]);
  const [tradeDetails, setTradeDetails] = useState<TradeRecord[]>([]);

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
      setTradeDetails(res.trades);
      if (onResult) onResult(res);
      const raw = await import("@/lib/api").then((m) => m.loadCsv(params.csv_path, 500));
      setOhlcvData(raw.data || []);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Backtest failed.");
    } finally {
      setLoading(false);
    }
  };

  const toggleKillzone = (kz: string) => {
    const current = params.killzones || [];
    setParams({
      ...params,
      killzones: current.includes(kz) ? current.filter((x) => x !== kz) : [...current, kz],
    });
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
          {/* Date Range */}
          <div>
            <label className="block text-xs text-slate-400 mb-1">Start Date</label>
            <input
              type="date"
              className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm"
              value={params.start_date || ""}
              onChange={(e) => setParams({ ...params, start_date: e.target.value || undefined })}
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">End Date</label>
            <input
              type="date"
              className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm"
              value={params.end_date || ""}
              onChange={(e) => setParams({ ...params, end_date: e.target.value || undefined })}
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Killzones</label>
            <div className="flex flex-wrap gap-1">
              {["killzone_london", "killzone_ny_am", "killzone_ny_pm", "killzone_asia"].map((kz) => (
                <button
                  key={kz}
                  onClick={() => toggleKillzone(kz)}
                  className={`px-2 py-0.5 text-[10px] rounded border transition ${
                    (params.killzones || []).includes(kz)
                      ? "text-amber-400 border-amber-400/50 bg-amber-400/10"
                      : "text-slate-500 border-slate-700 bg-slate-800"
                  }`}
                >
                  {kz.replace("killzone_", "").toUpperCase()}
                </button>
              ))}
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
            <StatCard label="Win Rate" value={`${(result.win_rate * 100).toFixed(1)}%`} color={result.win_rate > 0.5 ? "text-emerald-400" : "text-rose-400"} />
            <StatCard label="Profit Factor" value={result.profit_factor.toFixed(2)} />
            <StatCard label="Max Drawdown" value={`${result.max_drawdown.toFixed(2)} (${(result.max_drawdown_pct * 100).toFixed(1)}%)`} color="text-rose-400" />
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

          {/* Trade Details Table */}
          {tradeDetails.length > 0 && (
            <div className="bg-ict-panel rounded-lg p-3 border border-slate-700 overflow-x-auto">
              <h3 className="text-sm font-semibold text-slate-300 mb-2">Trade Details</h3>
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-slate-400 border-b border-slate-700">
                    <th className="text-left py-1">#</th>
                    <th className="text-left py-1">Dir</th>
                    <th className="text-left py-1">Entry</th>
                    <th className="text-left py-1">Exit</th>
                    <th className="text-left py-1">P&L</th>
                    <th className="text-left py-1">Reason</th>
                    <th className="text-left py-1">Pattern</th>
                    <th className="text-left py-1">Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {tradeDetails.map((t: any, i: number) => (
                    <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                      <td className="py-1 text-slate-500">{i + 1}</td>
                      <td className={`py-1 ${t.direction === 'long' ? 'text-emerald-400' : 'text-rose-400'}`}>{t.direction.toUpperCase()}</td>
                      <td className="py-1 text-slate-300">{t.entry_price.toFixed(5)}</td>
                      <td className="py-1 text-slate-300">{t.exit_price?.toFixed(5) || '-'}</td>
                      <td className={`py-1 ${(t.pnl || 0) > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>{t.pnl?.toFixed(2) || '-'}</td>
                      <td className="py-1 text-slate-400">{t.exit_reason}</td>
                      <td className="py-1">
                        {t.tags?.filter((tag: string) => tag.includes('fvg') || tag.includes('order_block') || tag.includes('bos') || tag.includes('sweep') || tag.includes('breaker') || tag.includes('mitigation')).map((tag: string) => (
                          <span key={tag} className="px-1 py-0.5 rounded bg-slate-700 text-slate-300 mr-1">{tag}</span>
                        ))}
                      </td>
                      <td className="py-1 text-slate-500 max-w-xs truncate">{t.notes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}
