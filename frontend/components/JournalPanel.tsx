"use client";

import { useEffect, useState } from "react";
import { getJournalEntries, createJournalEntry, deleteJournalEntry, JournalEntry } from "@/lib/api";
import { Plus, Trash2, BookOpen } from "lucide-react";

interface JournalPanelProps {
  onChange?: () => void;
}

export default function JournalPanel({ onChange }: JournalPanelProps) {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<Partial<JournalEntry>>({
    date: new Date().toISOString().slice(0, 16),
    session: "london",
    bias: "neutral",
    pair: "EURUSD",
    narrative: "",
    emotions: "",
    mistakes: "",
    improvements: "",
  });

  useEffect(() => {
    refresh();
  }, []);

  const refresh = async () => {
    const data = await getJournalEntries();
    setEntries(data);
  };

  const handleSubmit = async () => {
    await createJournalEntry(form as JournalEntry);
    setShowForm(false);
    refresh();
    if (onChange) onChange();
  };

  const handleDelete = async (id: number) => {
    await deleteJournalEntry(id);
    refresh();
    if (onChange) onChange();
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-ict-accent flex items-center gap-2">
          <BookOpen className="w-5 h-5" /> Trade Journal
        </h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1 bg-ict-accent text-slate-900 px-3 py-1.5 rounded text-sm font-semibold hover:bg-sky-400 transition"
        >
          <Plus className="w-4 h-4" /> New Entry
        </button>
      </div>

      {showForm && (
        <div className="bg-ict-panel rounded-lg p-4 border border-slate-700 grid grid-cols-1 md:grid-cols-2 gap-3">
          <input
            type="datetime-local"
            className="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm"
            value={form.date}
            onChange={(e) => setForm({ ...form, date: e.target.value })}
          />
          <select
            className="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm"
            value={form.session}
            onChange={(e) => setForm({ ...form, session: e.target.value as any })}
          >
            <option value="asia">Asia</option>
            <option value="london">London</option>
            <option value="ny_am">NY AM</option>
            <option value="ny_pm">NY PM</option>
          </select>
          <select
            className="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm"
            value={form.bias}
            onChange={(e) => setForm({ ...form, bias: e.target.value as any })}
          >
            <option value="bullish">Bullish</option>
            <option value="bearish">Bearish</option>
            <option value="neutral">Neutral</option>
          </select>
          <input
            className="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm"
            placeholder="Pair (e.g. EURUSD)"
            value={form.pair}
            onChange={(e) => setForm({ ...form, pair: e.target.value })}
          />
          <textarea
            className="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm md:col-span-2"
            placeholder="Market Narrative / Setup"
            rows={2}
            value={form.narrative}
            onChange={(e) => setForm({ ...form, narrative: e.target.value })}
          />
          <textarea
            className="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm"
            placeholder="Emotions"
            rows={2}
            value={form.emotions}
            onChange={(e) => setForm({ ...form, emotions: e.target.value })}
          />
          <textarea
            className="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm"
            placeholder="Mistakes"
            rows={2}
            value={form.mistakes}
            onChange={(e) => setForm({ ...form, mistakes: e.target.value })}
          />
          <textarea
            className="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm md:col-span-2"
            placeholder="Improvements for next session"
            rows={2}
            value={form.improvements}
            onChange={(e) => setForm({ ...form, improvements: e.target.value })}
          />
          <div className="md:col-span-2 flex justify-end">
            <button
              onClick={handleSubmit}
              className="bg-ict-bull text-white px-4 py-1.5 rounded text-sm font-semibold hover:bg-green-600 transition"
            >
              Save Entry
            </button>
          </div>
        </div>
      )}

      <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
        {entries.length === 0 && (
          <div className="text-slate-500 text-sm italic">No journal entries yet.</div>
        )}
        {entries.map((entry) => (
          <div
            key={entry.id}
            className="bg-ict-panel rounded-lg p-3 border border-slate-700 hover:border-slate-500 transition"
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-slate-400">
                  {entry.date ? new Date(entry.date).toLocaleString() : ""}
                </span>
                <span className="text-xs px-2 py-0.5 rounded bg-slate-700 text-slate-200 uppercase">
                  {entry.session}
                </span>
                <span
                  className={`text-xs px-2 py-0.5 rounded font-semibold ${
                    entry.bias === "bullish"
                      ? "bg-green-900 text-green-300"
                      : entry.bias === "bearish"
                      ? "bg-red-900 text-red-300"
                      : "bg-slate-700 text-slate-300"
                  }`}
                >
                  {entry.bias}
                </span>
                <span className="text-xs font-semibold text-ict-accent">{entry.pair}</span>
              </div>
              <button
                onClick={() => entry.id && handleDelete(entry.id)}
                className="text-slate-500 hover:text-red-400 transition"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
            {entry.narrative && (
              <div className="text-sm text-slate-300 mb-1">{entry.narrative}</div>
            )}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-xs text-slate-400">
              {entry.emotions && <div>Emotions: {entry.emotions}</div>}
              {entry.mistakes && <div>Mistakes: {entry.mistakes}</div>}
              {entry.improvements && <div>Next: {entry.improvements}</div>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
