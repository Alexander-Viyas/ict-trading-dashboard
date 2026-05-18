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
  killzones?: string[];
}

export interface BacktestResult {
  params: BacktestParams;
  trades: TradeRecord[];
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

export interface TradeRecord {
  entry_time: string;
  exit_time?: string;
  symbol: string;
  direction: 'long' | 'short';
  entry_price: number;
  exit_price?: number;
  quantity: number;
  pnl?: number;
  pnl_pct?: number;
  exit_reason?: string;
  tags: string[];
  notes?: string;
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

export interface Pattern {
  id?: number;
  pattern_type: string;
  direction: 'bullish' | 'bearish' | 'neutral';
  confidence: number;
  time?: string;
  symbol?: string;
  timeframe?: string;
  price_top: number;
  price_bottom: number;
  price_entry: number;
  price_sl: number;
  price_tp: number;
  candle_start_idx: number;
  candle_end_idx: number;
  notes?: string;
  tags: string[];
  trade_id?: number;
  outcome?: string;
}

export interface ReplayEvent {
  event_type: 'candle' | 'pattern' | 'trade_entry' | 'trade_exit';
  candle_idx: number;
  timestamp: string;
  data: any;
}

export async function runBacktest(params: BacktestParams): Promise<BacktestResult> {
  // Clean up empty strings to null
  const cleanParams = { ...params };
  if (!cleanParams.start_date) delete (cleanParams as any).start_date;
  if (!cleanParams.end_date) delete (cleanParams as any).end_date;
  const res = await api.post('/backtest/run', cleanParams);
  return res.data;
}

export async function getReplayEvents(): Promise<ReplayEvent[]> {
  const res = await api.get('/backtest/replay');
  return res.data.events;
}

export async function getBacktestPatterns(): Promise<Pattern[]> {
  const res = await api.get('/backtest/patterns');
  return res.data;
}

export async function getBacktestOhlcv(limit = 5000): Promise<any[]> {
  const res = await api.get('/backtest/ohlcv', { params: { limit } });
  return res.data.data;
}

export async function detectPatterns(csv_path: string, symbol: string, timeframe: string, min_confidence = 0): Promise<Pattern[]> {
  const res = await api.post('/patterns/detect', null, {
    params: { csv_path, symbol, timeframe, min_confidence }
  });
  return res.data;
}

export async function filterPatterns(filters: {
  symbol?: string;
  timeframe?: string;
  pattern_types?: string[];
  directions?: string[];
  min_confidence?: number;
  start_date?: string;
  end_date?: string;
  killzones?: string[];
  tags?: string[];
  limit?: number;
  offset?: number;
}): Promise<Pattern[]> {
  const res = await api.post('/patterns/filter', filters);
  return res.data;
}

export async function getPatternStats(symbol?: string, timeframe?: string): Promise<any> {
  const res = await api.get('/patterns/stats/summary', { params: { symbol, timeframe } });
  return res.data;
}

export async function listCsvFiles(): Promise<string[]> {
  const res = await api.get('/data/csv/list');
  return res.data.files;
}

export async function loadCsv(path: string, limit = 5000): Promise<{ data: any[] }> {
  const res = await api.get('/data/csv/load', { params: { path, limit } });
  return res.data;
}

export async function getMt5Status(): Promise<any> {
  const res = await api.get('/data/mt5/status');
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

export async function deleteJournalEntry(id: number): Promise<void> {
  await api.delete(`/journal/entries/${id}`);
}

export async function generateAIInsight(entries: JournalEntry[], question?: string): Promise<{ insight: string; model: string }> {
  const res = await api.post('/ai/generate', { journal_entries: entries, question });
  return res.data;
}

export async function runMtfAnalysis(params: BacktestParams): Promise<any> {
  // Clean up empty strings to null
  const cleanParams = { ...params };
  if (!cleanParams.start_date) delete (cleanParams as any).start_date;
  if (!cleanParams.end_date) delete (cleanParams as any).end_date;
  const res = await api.post('/backtest/mtf', cleanParams);
  return res.data;
}

export async function getLiveStatus(): Promise<any> {
  const res = await api.get('/live/status');
  return res.data;
}

export async function connectMt5(): Promise<any> {
  const res = await api.post('/live/mt5/connect');
  return res.data;
}

export async function getAIHealth(): Promise<{ status: string; model?: string }> {
  const res = await api.get('/ai/health');
  return res.data;
}
