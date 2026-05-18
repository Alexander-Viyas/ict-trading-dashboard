import httpx
import json
from datetime import datetime
from typing import List, Optional
from app.config import OLLAMA_URL, OLLAMA_MODEL
from app.models.schemas import JournalEntry, BacktestResult


class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_URL, model: str = OLLAMA_MODEL):
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate_insight(
        self,
        journal_entries: List[JournalEntry],
        backtest_results: Optional[BacktestResult] = None,
        question: str = "Analyze my trading performance and suggest improvements.",
    ) -> str:
        context = self._build_context(journal_entries, backtest_results)
        prompt = f"""You are an expert trading coach specializing in ICT Smart Money Concepts.
Analyze the following trading journal and backtest results. Provide actionable insights.

{context}

User question: {question}

Give a concise but thorough analysis covering:
1. Patterns in behavior/emotions
2. Statistical strengths/weaknesses
3. Specific, actionable next steps
Answer in plain text, no markdown tables."""

        try:
            resp = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "num_predict": 800},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "No response from model.")
        except httpx.ConnectError:
            return "Ollama is not running. Start it with: ollama serve"
        except Exception as e:
            return f"AI insight error: {e}"

    def _build_context(
        self,
        journal_entries: List[JournalEntry],
        backtest_results: Optional[BacktestResult],
    ) -> str:
        parts = []
        if backtest_results:
            parts.append(f"Backtest Results:\n"
                        f"- Strategy: {backtest_results.params.strategy_name}\n"
                        f"- Symbol: {backtest_results.params.symbol}\n"
                        f"- Total Return: {backtest_results.total_return:.2f} ({backtest_results.total_return_pct:.2f}%)\n"
                        f"- Win Rate: {backtest_results.win_rate*100:.1f}%\n"
                        f"- Profit Factor: {backtest_results.profit_factor:.2f}\n"
                        f"- Max Drawdown: {backtest_results.max_drawdown:.2f} ({backtest_results.max_drawdown_pct*100:.1f}%)\n"
                        f"- Sharpe Ratio: {backtest_results.sharpe_ratio:.2f}\n"
                        f"- Total Trades: {len(backtest_results.trades)}\n")

        if journal_entries:
            parts.append("Journal Entries:")
            for entry in journal_entries[:20]:
                parts.append(
                    f"- Date: {entry.date}, Pair: {entry.pair}, Session: {entry.session}, Bias: {entry.bias}\n"
                    f"  Narrative: {entry.narrative or 'N/A'}\n"
                    f"  Emotions: {entry.emotions or 'N/A'}\n"
                    f"  Mistakes: {entry.mistakes or 'N/A'}\n"
                )
        return "\n".join(parts) if parts else "No data provided."

    async def health(self) -> bool:
        try:
            resp = await self.client.get(f"{self.base_url}/api/tags", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False


ollama_client = OllamaClient()
