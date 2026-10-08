from __future__ import annotations

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Book, Question


def normalize_text(value: str) -> str:
    return " ".join(value.casefold().strip().split())[:1000]


async def search_books(session: AsyncSession, query: str, limit: int = 20) -> list[Book]:
    q = f"%{query.strip()}%"
    result = await session.execute(
        select(Book)
        .where(Book.is_active.is_(True), or_(Book.title.ilike(q), Book.author.ilike(q)))
        .order_by(Book.title)
        .limit(limit)
    )
    return list(result.scalars().all())


async def list_books(session: AsyncSession, offset: int = 0, limit: int = 20) -> list[Book]:
    result = await session.execute(
        select(Book).where(Book.is_active.is_(True)).order_by(Book.title).offset(offset).limit(limit)
    )
    return list(result.scalars().all())


async def list_all_active_books(session: AsyncSession, limit: int = 100) -> list[Book]:
    result = await session.execute(select(Book).where(Book.is_active.is_(True)).order_by(Book.title).limit(limit))
    return list(result.scalars().all())


async def get_book(session: AsyncSession, book_id: int) -> Book | None:
    return await session.scalar(select(Book).where(Book.id == book_id))


async def book_question_count(session: AsyncSession, book_id: int) -> int:
    result = await session.execute(
        select(func.count(Question.id)).where(Question.book_id == book_id, Question.is_active.is_(True))
    )
    return int(result.scalar_one())


async def delete_book(session: AsyncSession, book_id: int) -> None:
    await session.execute(delete(Book).where(Book.id == book_id))
    await session.commit()
