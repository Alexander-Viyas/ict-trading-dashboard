"use client";

import { useState, useEffect } from "react";
import { filterPatterns, getPatternStats, Pattern } from "@/lib/api";
import { Search, Filter, BarChart3, TrendingUp, TrendingDown, Calendar } from "lucide-react";

const PATTERN_TYPES = [
  "fvg_bullish", "fvg_bearish",
  "order_block_bullish", "order_block_bearish",
  "bos_bullish", "bos_bearish",
  "liquidity_sweep_bullish", "liquidity_sweep_bearish",
  "breaker_block_bullish", "breaker_block_bearish",
  "mitigation_block_bullish", "mitigation_block_bearish",
];

const KILLZONES = [
  { value: "killzone_london", label: "London 8-10am" },
  { value: "killzone_ny_am", label: "NY AM 9:30-11:30am" },
  { value: "killzone_ny_pm", label: "NY PM 1-3pm" },
  { value: "killzone_asia", label: "Asia 1-4am" },
];

export default function PatternLibrary() {
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [filters, setFilters] = useState({
    symbol: "EURUSD",
    timeframe: "M15",
    pattern_types: [] as string[],
    directions: [] as string[],
    min_confidence: 50,
    start_date: "",
    end_date: "",
    killzones: [] as string[],
    limit: 50,
  });
  const [loading, setLoading] = useState(false);
  const [selectedPattern, setSelectedPattern] = useState<Pattern | null>(null);

  const loadPatterns = async () => {
    setLoading(true);
    const res = await filterPatterns({
      ...filters,
      pattern_types: filters.pattern_types.length ? filters.pattern_types : undefined,
      directions: filters.directions.length ? filters.directions : undefined,
      killzones: filters.killzones.length ? filters.killzones : undefined,
      start_date: filters.start_date || undefined,
      end_date: filters.end_date || undefined,
    });
    setPatterns(res);
    const s = await getPatternStats(filters.symbol, filters.timeframe);
    setStats(s);
    setLoading(false);
  };

  useEffect(() => {
    loadPatterns();
  }, []);

  const togglePatternType = (pt: string) => {
    setFilters((prev) => ({
      ...prev,
      pattern_types: prev.pattern_types.includes(pt)
        ? prev.pattern_types.filter((x) => x !== pt)
        : [...prev.pattern_types, pt],
    }));
  };

  const toggleDirection = (dir: string) => {
    setFilters((prev) => ({
      ...prev,
      directions: prev.directions.includes(dir)
        ? prev.directions.filter((x) => x !== dir)
        : [...prev.directions, dir],
    }));
  };

  const toggleKillzone = (kz: string) => {
    setFilters((prev) => ({
      ...prev,
      killzones: prev.killzones.includes(kz)
        ? prev.killzones.filter((x) => x !== kz)
        : [...prev.killzones, kz],
    }));
  };

  const getPatternColor = (type: string) => {
    if (type.includes("bullish")) return "text-emerald-400 bg-emerald-400/10 border-emerald-400/30";
    if (type.includes("bearish")) return "text-rose-400 bg-rose-400/10 border-rose-400/30";
    return "text-slate-300 bg-slate-700/30 border-slate-600/30";
  };

  return (
    <div className="space-y-4">
      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
            <div className="text-xs text-slate-400">Total Patterns</div>
            <div className="text-xl font-bold text-sky-400">{stats.total_patterns}</div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
            <div className="text-xs text-slate-400">Bullish</div>
            <div className="text-xl font-bold text-emerald-400">{stats.bullish}</div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
            <div className="text-xs text-slate-400">Bearish</div>
            <div className="text-xl font-bold text-rose-400">{stats.bearish}</div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
            <div className="text-xs text-slate-400">Avg Confidence</div>
            <div className="text-xl font-bold text-amber-400">{stats.avg_confidence}%</div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700 space-y-3">
        <div className="flex items-center gap-2 text-sky-400 font-semibold">
          <Filter className="w-4 h-4" /> Filters
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Symbol</label>
            <input
              className="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1 text-sm"
              value={filters.symbol}
              onChange={(e) => setFilters({ ...filters, symbol: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Min Confidence</label>
            <input
              type="range"
              min={0}
              max={100}
              className="w-full"
              value={filters.min_confidence}
              onChange={(e) => setFilters({ ...filters, min_confidence: Number(e.target.value) })}
            />
            <div className="text-xs text-slate-400 text-right">{filters.min_confidence}%</div>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Date Range</label>
            <div className="flex gap-2">
              <input
                type="date"
                className="flex-1 bg-slate-900 border border-slate-600 rounded px-2 py-1 text-sm"
                value={filters.start_date}
                onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
              />
              <input
                type="date"
                className="flex-1 bg-slate-900 border border-slate-600 rounded px-2 py-1 text-sm"
                value={filters.end_date}
                onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
              />
            </div>
          </div>
        </div>

        {/* Pattern Types */}
        <div>
          <label className="block text-xs text-slate-400 mb-1">Pattern Types</label>
          <div className="flex flex-wrap gap-2">
            {PATTERN_TYPES.map((pt) => (
              <button
                key={pt}
                onClick={() => togglePatternType(pt)}
                className={`px-2 py-1 text-xs rounded border transition ${
                  filters.pattern_types.includes(pt)
                    ? getPatternColor(pt)
                    : "text-slate-400 border-slate-600 bg-slate-800"
                }`}
              >
                {pt.replace(/_/g, " ")}
              </button>
            ))}
          </div>
        </div>

        {/* Directions */}
        <div className="flex gap-2">
          {["bullish", "bearish"].map((dir) => (
            <button
              key={dir}
              onClick={() => toggleDirection(dir)}
              className={`px-3 py-1 text-xs rounded border transition ${
                filters.directions.includes(dir)
                  ? dir === "bullish"
                    ? "text-emerald-400 border-emerald-400/50 bg-emerald-400/10"
                    : "text-rose-400 border-rose-400/50 bg-rose-400/10"
                  : "text-slate-400 border-slate-600 bg-slate-800"
              }`}
            >
              {dir === "bullish" ? <TrendingUp className="w-3 h-3 inline mr-1" /> : <TrendingDown className="w-3 h-3 inline mr-1" />}
              {dir}
            </button>
          ))}
        </div>

        {/* Killzones */}
        <div className="flex flex-wrap gap-2">
          {KILLZONES.map((kz) => (
            <button
              key={kz.value}
              onClick={() => toggleKillzone(kz.value)}
              className={`px-2 py-1 text-xs rounded border transition ${
                filters.killzones.includes(kz.value)
                  ? "text-amber-400 border-amber-400/50 bg-amber-400/10"
                  : "text-slate-400 border-slate-600 bg-slate-800"
              }`}
            >
              <Calendar className="w-3 h-3 inline mr-1" />
              {kz.label}
            </button>
          ))}
        </div>

        <button
          onClick={loadPatterns}
          disabled={loading}
          className="flex items-center gap-2 bg-sky-500 text-white px-4 py-2 rounded font-semibold hover:bg-sky-400 transition disabled:opacity-50"
        >
          <Search className="w-4 h-4" />
          {loading ? "Loading..." : "Search Patterns"}
        </button>
      </div>

      {/* Pattern List */}
      <div className="grid grid-cols-1 gap-2">
        {patterns.map((p) => (
          <div
            key={p.id}
            onClick={() => setSelectedPattern(p)}
            className={`bg-slate-800/30 rounded-lg p-3 border cursor-pointer hover:bg-slate-800/60 transition ${
              selectedPattern?.id === p.id ? "border-sky-400" : "border-slate-700"
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className={`px-2 py-0.5 text-xs rounded border ${getPatternColor(p.pattern_type)}`}>
                  {p.pattern_type.replace(/_/g, " ")}
                </span>
                <span className="text-xs text-slate-400">{p.time?.split("T")[0]}</span>
              </div>
              <div className="text-xs font-mono">
                <span className={p.confidence >= 70 ? "text-emerald-400" : p.confidence >= 50 ? "text-amber-400" : "text-rose-400"}>
                  {p.confidence}%
                </span>
              </div>
            </div>
            <div className="mt-1 text-xs text-slate-300">
              Entry: {p.price_entry.toFixed(5)} | SL: {p.price_sl.toFixed(5)} | TP: {p.price_tp.toFixed(5)}
            </div>
            <div className="mt-1 text-xs text-slate-500">{p.notes}</div>
            <div className="mt-1 flex gap-1">
              {p.tags.map((tag) => (
                <span key={tag} className="px-1.5 py-0.5 text-[10px] bg-slate-700 rounded text-slate-300">
                  {tag}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Pattern Detail Modal */}
      {selectedPattern && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 rounded-lg border border-slate-700 max-w-lg w-full p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-sky-400">Pattern Details</h3>
              <button onClick={() => setSelectedPattern(null)} className="text-slate-400 hover:text-white">✕</button>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-slate-400">Type:</span><span>{selectedPattern.pattern_type}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Direction:</span><span className={selectedPattern.direction === "bullish" ? "text-emerald-400" : "text-rose-400"}>{selectedPattern.direction}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Confidence:</span><span>{selectedPattern.confidence}%</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Time:</span><span>{selectedPattern.time}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Entry:</span><span className="text-sky-400">{selectedPattern.price_entry.toFixed(5)}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Stop Loss:</span><span className="text-rose-400">{selectedPattern.price_sl.toFixed(5)}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Take Profit:</span><span className="text-emerald-400">{selectedPattern.price_tp.toFixed(5)}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Zone:</span><span>{selectedPattern.price_bottom.toFixed(5)} - {selectedPattern.price_top.toFixed(5)}</span></div>
              <div className="pt-2 border-t border-slate-700">
                <div className="text-slate-400 text-xs mb-1">Notes:</div>
                <div className="text-slate-300">{selectedPattern.notes}</div>
              </div>
              <div className="flex gap-1 pt-2">
                {selectedPattern.tags.map((tag) => (
                  <span key={tag} className="px-2 py-0.5 text-xs bg-slate-700 rounded text-slate-300">{tag}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
