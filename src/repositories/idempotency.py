import datetime
import uuid

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from models import IdempotencyKey


async def get_by_key(session: AsyncSession, key: str) -> IdempotencyKey | None:
    result = await session.execute(select(IdempotencyKey).where(IdempotencyKey.key == key))
    return result.scalar_one_or_none()


async def claim(
    session: AsyncSession, key: str, fingerprint: str, *, stale_before: datetime.datetime
) -> IdempotencyKey | None:
    """Insert a fresh in-progress row, or reclaim a stale one for the same fingerprint.

    Returns None if the key is held by a completed or still-fresh in-progress row
    (caller must inspect that row to tell a replay from a genuine conflict).
    """
    stmt = (
        insert(IdempotencyKey)
        .values(key=key, fingerprint=fingerprint, check_id=None)
        .on_conflict_do_update(
            index_elements=[IdempotencyKey.key],
            set_={"created_at": func.now()},
            where=(
                (IdempotencyKey.fingerprint == fingerprint)
                & IdempotencyKey.check_id.is_(None)
                & (IdempotencyKey.created_at < stale_before)
            ),
        )
        .returning(IdempotencyKey)
        .execution_options(populate_existing=True)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def complete(session: AsyncSession, key: str, check_id: uuid.UUID) -> None:
    await session.execute(
        update(IdempotencyKey).where(IdempotencyKey.key == key).values(check_id=check_id)
    )


async def release(session: AsyncSession, key: str) -> None:
    await session.execute(
        delete(IdempotencyKey).where(IdempotencyKey.key == key, IdempotencyKey.check_id.is_(None))
    )
