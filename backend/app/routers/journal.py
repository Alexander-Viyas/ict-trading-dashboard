from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.database import get_db, JournalEntryDB
from app.models.schemas import JournalEntry
from typing import List

router = APIRouter(prefix="/journal", tags=["journal"])


def db_to_schema(entry: JournalEntryDB) -> JournalEntry:
    return JournalEntry(
        id=entry.id,
        trade_id=entry.trade_id,
        date=entry.date,
        session=entry.session,
        bias=entry.bias,
        pair=entry.pair,
        narrative=entry.narrative,
        emotions=entry.emotions,
        mistakes=entry.mistakes,
        improvements=entry.improvements,
        screenshots=entry.screenshots.split(",") if entry.screenshots else [],
    )


def schema_to_db(entry: JournalEntry) -> JournalEntryDB:
    return JournalEntryDB(
        id=entry.id,
        trade_id=entry.trade_id,
        date=entry.date,
        session=entry.session,
        bias=entry.bias,
        pair=entry.pair,
        narrative=entry.narrative,
        emotions=entry.emotions,
        mistakes=entry.mistakes,
        improvements=entry.improvements,
        screenshots=",".join(entry.screenshots) if entry.screenshots else None,
    )


@router.get("/entries", response_model=List[JournalEntry])
async def get_entries(limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(JournalEntryDB).order_by(desc(JournalEntryDB.date)).limit(limit))
    rows = result.scalars().all()
    return [db_to_schema(r) for r in rows]


@router.post("/entries", response_model=JournalEntry)
async def create_entry(entry: JournalEntry, db: AsyncSession = Depends(get_db)):
    db_entry = schema_to_db(entry)
    db.add(db_entry)
    await db.commit()
    await db.refresh(db_entry)
    return db_to_schema(db_entry)


@router.delete("/entries/{entry_id}")
async def delete_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(JournalEntryDB).where(JournalEntryDB.id == entry_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Entry not found")
    await db.delete(row)
    await db.commit()
    return {"deleted": True}
