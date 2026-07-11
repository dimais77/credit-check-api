import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Check, Document, Issue
from repositories.dto import CheckSummary, NewCheck


async def create(session: AsyncSession, dto: NewCheck) -> Check:
    check = Check(
        id=dto.id,
        program=dto.program,
        status=dto.status,
        reason=dto.reason,
        checked_at=dto.checked_at,
        documents=[
            Document(
                id=doc.id,
                name=doc.name,
                detected_type=doc.detected_type,
                size_bytes=doc.size_bytes,
                content_type=doc.content_type,
                storage_path=doc.storage_path,
            )
            for doc in dto.documents
        ],
        issues=[Issue(level=issue.level, message=issue.message) for issue in dto.issues],
    )
    session.add(check)
    await session.flush()
    return check


async def get_by_id(session: AsyncSession, check_id: uuid.UUID) -> Check | None:
    result = await session.execute(
        select(Check)
        .where(Check.id == check_id)
        .options(selectinload(Check.documents), selectinload(Check.issues))
    )
    return result.scalar_one_or_none()


async def list_all(session: AsyncSession, limit: int, offset: int) -> list[CheckSummary]:
    result = await session.execute(
        select(
            Check.id,
            Check.checked_at,
            Check.program,
            Check.status,
            func.count(Document.id).label("documents_count"),
        )
        .outerjoin(Document, Document.check_id == Check.id)
        .group_by(Check.id)
        .order_by(Check.checked_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [
        CheckSummary(
            id=row.id,
            checked_at=row.checked_at,
            program=row.program,
            status=row.status,
            documents_count=row.documents_count,
        )
        for row in result.all()
    ]


async def count(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(Check))
    return result.scalar_one()
