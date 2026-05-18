"use client";

import { useState } from "react";
import BacktestPanel from "@/components/BacktestPanel";
import JournalPanel from "@/components/JournalPanel";
import AIInsightPanel from "@/components/AIInsightPanel";
import PatternLibrary from "@/components/PatternLibrary";
import ReplayPlayer from "@/components/ReplayPlayer";
import LivePanel from "@/components/LivePanel";
import { BacktestResult } from "@/lib/api";

export default function Home() {
  const [activeTab, setActiveTab] = useState("backtest");
  const [lastResult, setLastResult] = useState<BacktestResult | null>(null);

  const tabs = [
    { id: "backtest", label: "Backtest", icon: "📊" },
    { id: "replay", label: "Replay", icon: "▶️" },
    { id: "patterns", label: "Patterns", icon: "🔍" },
    { id: "journal", label: "Journal", icon: "📝" },
    { id: "live", label: "Live", icon: "🔴" },
    { id: "ai", label: "AI", icon: "🤖" },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 p-4">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-sky-400">ICT Trading Dashboard</h1>
        <p className="text-sm text-slate-500">Pattern Recognition · Visual Replay · Smart Money Concepts · Live Confluence</p>
      </header>

      <nav className="flex flex-wrap gap-2 mb-6 border-b border-slate-800 pb-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-t-lg text-sm font-medium transition ${
              activeTab === tab.id
                ? "bg-slate-800 text-sky-400 border-b-2 border-sky-400"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <span className="mr-1">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </nav>

      <main>
        {activeTab === "backtest" && <BacktestPanel onResult={(r) => setLastResult(r)} />}
        {activeTab === "replay" && <ReplayPlayer />}
        {activeTab === "patterns" && <PatternLibrary />}
        {activeTab === "journal" && <JournalPanel />}
        {activeTab === "live" && <LivePanel />}
        {activeTab === "ai" && <AIInsightPanel />}
      </main>
    </div>
  );
}
