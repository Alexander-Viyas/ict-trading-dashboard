import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

export interface BacktestParams {
  strategy_name: string;
  symbol: string;
  timeframe: string;
  start_date?: string;
  end_date?: string;
  initial_balance: number;
  risk_per_trade: number;
  csv_path: string;
}

export interface BacktestResult {
  params: BacktestParams;
  trades: any[];
  total_return: number;
  total_return_pct: number;
  win_rate: number;
  profit_factor: number;
  max_drawdown: number;
  max_drawdown_pct: number;
  sharpe_ratio: number;
  equity_curve: number[];
  equity_times: string[];
}

export interface JournalEntry {
  id?: number;
  trade_id?: number;
  date: string;
  session?: 'london' | 'ny_am' | 'ny_pm' | 'asia';
  bias?: 'bullish' | 'bearish' | 'neutral';
  pair?: string;
  narrative?: string;
  emotions?: string;
  mistakes?: string;
  improvements?: string;
  screenshots?: string[];
}

export async function runBacktest(params: BacktestParams): Promise<BacktestResult> {
  const res = await api.post('/backtest/run', params);
  return res.data;
}

export async function getJournalEntries(): Promise<JournalEntry[]> {
  const res = await api.get('/journal/entries');
  return res.data;
}

export async function createJournalEntry(entry: JournalEntry): Promise<JournalEntry> {
  const res = await api.post('/journal/entries', entry);
  return res.data;
}

export async function deleteJournalEntry(id: number) {
  await api.delete(`/journal/entries/${id}`);
}

export async function getAIHealth() {
  const res = await api.get('/ai/health');
  return res.data;
}

export async function generateAIInsight(
  entries: JournalEntry[],
  result?: BacktestResult,
  question?: string
) {
  const res = await api.post('/ai/insight', {
    journal_entries: entries,
    backtest_results: result,
    question: question || 'Analyze my trading performance and suggest improvements.',
  });
  return res.data;
}

export async function listCsvFiles(): Promise<string[]> {
  const res = await api.get('/data/csv/list');
  return res.data.files;
}

export async function loadCsv(path: string, limit = 1000) {
  const res = await api.get('/data/csv/load', { params: { path, limit } });
  return res.data;
}
