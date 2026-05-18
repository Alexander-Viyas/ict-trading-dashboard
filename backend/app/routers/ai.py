from fastapi import APIRouter, HTTPException
from app.models.schemas import AIInsightRequest, AIInsightResponse
from app.services.ollama_client import ollama_client

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/insight", response_model=AIInsightResponse)
async def generate_insight(req: AIInsightRequest):
    insight_text = await ollama_client.generate_insight(
        journal_entries=req.journal_entries,
        backtest_results=req.backtest_results,
        question=req.question,
    )
    return AIInsightResponse(
        insight=insight_text,
        model=ollama_client.model,
    )


@router.get("/health")
async def ai_health():
    ok = await ollama_client.health()
    return {"ok": ok, "model": ollama_client.model}
