"use client";

import { useState, useEffect } from "react";
import BacktestPanel from "@/components/BacktestPanel";
import JournalPanel from "@/components/JournalPanel";
import AIInsightPanel from "@/components/AIInsightPanel";
import { BarChart3, BookOpen, Sparkles } from "lucide-react";
import { BacktestResult, JournalEntry, getJournalEntries } from "@/lib/api";

type Tab = "backtest" | "journal" | "ai";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<Tab>("backtest");
  const [journalEntries, setJournalEntries] = useState<JournalEntry[]>([]);
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);

  useEffect(() => {
    getJournalEntries().then(setJournalEntries);
  }, []);

  const refreshJournal = async () => {
    const entries = await getJournalEntries();
    setJournalEntries(entries);
  };

  const tabs = [
    { id: "backtest" as Tab, label: "Backtest", icon: BarChart3 },
    { id: "journal" as Tab, label: "Journal", icon: BookOpen },
    { id: "ai" as Tab, label: "AI Insight", icon: Sparkles },
  ];

  return (
    <div className="min-h-screen bg-ict-dark text-slate-200">
      <header className="border-b border-slate-800 bg-ict-panel/50 backdrop-blur sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">ICT Trading Dashboard</h1>
            <p className="text-xs text-slate-500">Hybrid MT5 + CSV Backtesting Engine</p>
          </div>
          <nav className="flex gap-1 bg-slate-800/50 rounded-lg p-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded text-sm font-medium transition ${
                    activeTab === tab.id
                      ? "bg-ict-accent text-slate-900"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-700"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === "backtest" && (
          <BacktestPanel onResult={setBacktestResult} />
        )}
        {activeTab === "journal" && <JournalPanel onChange={refreshJournal} />}
        {activeTab === "ai" && (
          <AIInsightPanel entries={journalEntries} result={backtestResult} />
        )}
      </main>
    </div>
  );
}
