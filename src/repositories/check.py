import datetime
import uuid

from sqlalchemy import func, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Check, Document, Issue
from repositories.dto import CheckSummary, NewCheck


async def create(session: AsyncSession, dto: NewCheck) -> Check:
    check = Check(
        id=dto.id,
        package_id=dto.package_id,
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


async def list_page(
    session: AsyncSession,
    *,
    limit: int,
    cursor: tuple[datetime.datetime, uuid.UUID] | None,
) -> list[CheckSummary]:
    documents_count = (
        select(func.count(Document.id))
        .where(Document.check_id == Check.id)
        .correlate(Check)
        .scalar_subquery()
        .label("documents_count")
    )
    stmt = (
        select(
            Check.id,
            Check.package_id,
            Check.checked_at,
            Check.program,
            Check.status,
            documents_count,
        )
        .order_by(Check.checked_at.desc(), Check.id.desc())
        .limit(limit)
    )
    if cursor is not None:
        stmt = stmt.where(tuple_(Check.checked_at, Check.id) < cursor)

    result = await session.execute(stmt)
    return [
        CheckSummary(
            id=row.id,
            package_id=row.package_id,
            checked_at=row.checked_at,
            program=row.program,
            status=row.status,
            documents_count=row.documents_count,
        )
        for row in result.all()
    ]
