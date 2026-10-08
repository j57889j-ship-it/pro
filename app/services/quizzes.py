from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Question, QuizAnswer, QuizAttempt, User


async def get_questions(session: AsyncSession, book_id: int, count: int) -> list[Question]:
    # PostgreSQL evaluates random() before LIMIT, keeping the query compact for a book-sized pool.
    result = await session.execute(
        select(Question)
        .where(Question.book_id == book_id, Question.is_active.is_(True))
        .order_by(func.random())
        .limit(max(1, min(count, 100)))
    )
    return list(result.scalars().all())


async def get_random_questions(session: AsyncSession, count: int) -> list[Question]:
    result = await session.execute(
        select(Question).where(Question.is_active.is_(True)).order_by(func.random()).limit(max(1, min(count, 100)))
    )
    return list(result.scalars().all())


async def get_wrong_questions(session: AsyncSession, user_id: int, limit: int = 30) -> list[Question]:
    stmt = (
        select(Question)
        .join(QuizAnswer, QuizAnswer.question_id == Question.id)
        .join(QuizAttempt, QuizAttempt.id == QuizAnswer.attempt_id)
        .where(
            QuizAttempt.user_id == user_id,
            QuizAnswer.is_correct.is_(False),
            Question.is_active.is_(True),
        )
        .distinct()
        .order_by(desc(Question.id))
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_attempt(session: AsyncSession, user_id: int, book_id: int | None, total: int) -> QuizAttempt:
    attempt = QuizAttempt(user_id=user_id, book_id=book_id, total=total, completed=False)
    session.add(attempt)
    await session.commit()
    await session.refresh(attempt)
    return attempt


async def record_answer(
    session: AsyncSession,
    attempt_id: int,
    question_id: int,
    selected: str,
    correct_points: int,
) -> tuple[bool, int, int, int] | None:
    attempt = await session.scalar(select(QuizAttempt).where(QuizAttempt.id == attempt_id).with_for_update())
    question = await session.scalar(select(Question).where(Question.id == question_id))
    if not attempt or not question or attempt.finished_at is not None:
        return None

    existing = await session.scalar(
        select(QuizAnswer).where(QuizAnswer.attempt_id == attempt_id, QuizAnswer.question_id == question_id)
    )
    if existing:
        return None

    user = await session.scalar(select(User).where(User.id == attempt.user_id).with_for_update())
    if user is None:
        return None

    is_correct = selected.upper() == question.correct_option.upper()
    session.add(
        QuizAnswer(
            attempt_id=attempt.id,
            question_id=question.id,
            selected_option=selected.upper(),
            is_correct=is_correct,
        )
    )
    user.total_questions += 1
    if is_correct:
        user.correct_answers += 1
        user.score += correct_points
        attempt.correct += 1
        attempt.score += correct_points
    else:
        user.wrong_answers += 1

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        return None
    return is_correct, attempt.correct, attempt.score, user.streak


async def finish_attempt(session: AsyncSession, attempt_id: int, completed: bool = True) -> tuple[int, int, int]:
    attempt = await session.scalar(select(QuizAttempt).where(QuizAttempt.id == attempt_id).with_for_update())
    if not attempt:
        return 0, 0, 0
    if attempt.finished_at is None:
        attempt.finished_at = datetime.now(timezone.utc)
    attempt.completed = completed

    if completed:
        user = await session.scalar(select(User).where(User.id == attempt.user_id).with_for_update())
        if user:
            today = datetime.now(timezone.utc).date()
            today_s = today.isoformat()
            yesterday_s = (today - timedelta(days=1)).isoformat()
            if user.last_quiz_day == today_s:
                pass
            elif user.last_quiz_day == yesterday_s:
                user.streak += 1
                user.last_quiz_day = today_s
            else:
                user.streak = 1
                user.last_quiz_day = today_s

    await session.commit()
    return attempt.correct, attempt.total, attempt.score


async def top_users(session: AsyncSession, limit: int) -> list[User]:
    result = await session.execute(
        select(User)
        .where(User.is_blocked.is_(False))
        .order_by(User.score.desc(), User.correct_answers.desc(), User.id.asc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def user_rank(session: AsyncSession, user_id: int) -> int:
    user = await session.get(User, user_id)
    if not user or user.is_blocked:
        return 0
    score = int(user.score)
    correct = int(user.correct_answers)
    uid = int(user.id)
    better = or_(
        User.score > score,
        and_(User.score == score, User.correct_answers > correct),
        and_(User.score == score, User.correct_answers == correct, User.id < uid),
    )
    result = await session.execute(
        select(func.count(User.id)).where(User.is_blocked.is_(False), better)
    )
    return int(result.scalar_one()) + 1
