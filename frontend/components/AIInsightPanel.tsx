"use client";

import { useState } from "react";
import { generateAIInsight, getAIHealth, JournalEntry, BacktestResult } from "@/lib/api";
import { Sparkles, Loader2, Wifi, WifiOff } from "lucide-react";

interface AIInsightPanelProps {
  entries: JournalEntry[];
  result?: BacktestResult | null;
}

export default function AIInsightPanel({ entries, result }: AIInsightPanelProps) {
  const [insight, setInsight] = useState("");
  const [loading, setLoading] = useState(false);
  const [question, setQuestion] = useState("Analyze my trading performance and suggest improvements.");
  const [health, setHealth] = useState<boolean | null>(null);

  const checkHealth = async () => {
    try {
      const res = await getAIHealth();
      setHealth(res.ok);
    } catch {
      setHealth(false);
    }
  };

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const res = await generateAIInsight(entries, result || undefined, question);
      setInsight(res.insight);
    } catch (e) {
      setInsight("Failed to generate insight. Ensure Ollama is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-ict-accent flex items-center gap-2">
          <Sparkles className="w-5 h-5" /> AI Insight (Ollama)
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={checkHealth}
            className="text-xs flex items-center gap-1 px-2 py-1 rounded bg-slate-800 border border-slate-600 hover:bg-slate-700 transition"
          >
            {health === true ? <Wifi className="w-3 h-3 text-ict-bull" /> : health === false ? <WifiOff className="w-3 h-3 text-ict-bear" /> : <Wifi className="w-3 h-3 text-slate-500" />}
            Ollama
          </button>
        </div>
      </div>

      <div className="bg-ict-panel rounded-lg p-4 border border-slate-700">
        <textarea
          className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm mb-2"
          rows={2}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button
          onClick={handleGenerate}
          disabled={loading || entries.length === 0}
          className="flex items-center gap-2 bg-violet-600 text-white px-4 py-2 rounded text-sm font-semibold hover:bg-violet-500 transition disabled:opacity-50"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          Generate Insight
        </button>
        {entries.length === 0 && (
          <div className="text-xs text-slate-500 mt-1">Add journal entries to enable AI analysis.</div>
        )}
      </div>

      {insight && (
        <div className="bg-ict-panel rounded-lg p-4 border border-slate-700">
          <h3 className="text-sm font-semibold text-violet-400 mb-2">Analysis</h3>
          <div className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">{insight}</div>
        </div>
      )}
    </div>
  );
}
