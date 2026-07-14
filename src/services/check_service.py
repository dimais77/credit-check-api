import datetime
import logging
import uuid
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import DocumentType, Program
from core.exceptions import (
    CheckNotFoundError,
    IdempotencyKeyConflictError,
    IdempotencyKeyInProgressError,
)
from models import Check
from repositories import check as check_repo
from repositories import idempotency as idempotency_repo
from repositories.dto import CheckSummary, NewCheck, NewDocument, NewIssue
from services import fingerprint
from services.cursor import decode_cursor, encode_cursor
from services.document_classifier import classify_document
from services.issue import Issue
from services.status import build_reason, resolve_status
from services.upload import UploadedFile
from services.validation import check_completeness, check_duplicates, validate_file
from storage import files

logger = logging.getLogger(__name__)

_TYPE_ORDER = {document_type: index for index, document_type in enumerate(DocumentType)}
_IN_PROGRESS_TTL = datetime.timedelta(seconds=60)


def _order_key(document: NewDocument) -> int:
    if document.detected_type is None:
        return len(_TYPE_ORDER)
    return _TYPE_ORDER[document.detected_type]


@dataclass(frozen=True, slots=True)
class CheckPage:
    items: list[CheckSummary]
    next_cursor: str | None
    has_more: bool


async def _prepare_check(
    check_id: uuid.UUID,
    package_id: uuid.UUID,
    program: Program,
    uploads: list[UploadedFile],
    *,
    base_dir: Path,
    max_size_mb: int,
) -> tuple[NewCheck, str]:
    issues: list[Issue] = []
    documents: list[NewDocument] = []
    detected_counts: Counter[DocumentType] = Counter()
    file_digests: list[tuple[str, str]] = []
    max_bytes = max_size_mb * 1024 * 1024

    for upload in uploads:
        detected = classify_document(upload.filename)
        document_id = uuid.uuid4()
        ext = Path(upload.filename).suffix
        stored = await files.save_stream(
            base_dir, check_id, document_id, ext, upload.chunks(), max_bytes=max_bytes
        )
        file_digests.append((upload.filename, stored.digest))
        issues.extend(validate_file(upload.filename, stored.size_bytes, max_size_mb, detected))
        if detected is not None:
            detected_counts[detected] += 1

        documents.append(
            NewDocument(
                id=document_id,
                name=upload.filename,
                detected_type=detected,
                size_bytes=stored.size_bytes,
                content_type=upload.content_type,
                storage_path=stored.path,
            )
        )

    documents.sort(key=_order_key)

    issues.extend(check_completeness(set(detected_counts), program))
    issues.extend(check_duplicates(detected_counts, program))
    status = resolve_status(issues)
    reason = build_reason(issues, status)

    new_check = NewCheck(
        id=check_id,
        package_id=package_id,
        program=program,
        status=status,
        reason=reason,
        checked_at=datetime.datetime.now(datetime.UTC),
        documents=documents,
        issues=[NewIssue(level=issue.level, message=issue.message) for issue in issues],
    )
    return new_check, fingerprint.from_digests(program, file_digests)


async def _claim_or_replay(
    session: AsyncSession,
    idempotency_key: str,
    fp: str,
    *,
    base_dir: Path,
    check_id: uuid.UUID,
) -> Check | None:
    stale_before = datetime.datetime.now(datetime.UTC) - _IN_PROGRESS_TTL
    claimed = await idempotency_repo.claim(session, idempotency_key, fp, stale_before=stale_before)
    await session.commit()
    if claimed is not None:
        return None

    await files.delete(base_dir, check_id)
    existing = await idempotency_repo.get_by_key(session, idempotency_key)
    if existing is None:
        raise IdempotencyKeyInProgressError
    if existing.fingerprint != fp:
        raise IdempotencyKeyConflictError
    if existing.check_id is not None:
        return await get_check(session, existing.check_id)
    raise IdempotencyKeyInProgressError


async def run_check(
    session: AsyncSession,
    program: Program,
    uploads: list[UploadedFile],
    idempotency_key: str | None,
    *,
    package_id: uuid.UUID | None,
    base_dir: Path,
    max_size_mb: int,
) -> Check:
    check_id = uuid.uuid4()
    resolved_package_id = package_id or uuid.uuid4()
    try:
        new_check, fp = await _prepare_check(
            check_id,
            resolved_package_id,
            program,
            uploads,
            base_dir=base_dir,
            max_size_mb=max_size_mb,
        )
    except Exception:
        logger.exception(
            "Check %s failed during preparation; removing stored files under %s",
            check_id,
            base_dir / str(check_id),
        )
        await files.delete(base_dir, check_id)
        raise

    if idempotency_key is not None:
        replay = await _claim_or_replay(
            session, idempotency_key, fp, base_dir=base_dir, check_id=check_id
        )
        if replay is not None:
            return replay

    try:
        async with session.begin():
            check = await check_repo.create(session, new_check)
            if idempotency_key is not None:
                await idempotency_repo.complete(session, idempotency_key, check_id)
            return check
    except Exception:
        logger.exception(
            "Check %s failed; removing stored files under %s",
            check_id,
            base_dir / str(check_id),
        )
        await files.delete(base_dir, check_id)
        if idempotency_key is not None:
            await idempotency_repo.release(session, idempotency_key)
            await session.commit()
        raise


async def get_check(session: AsyncSession, check_id: uuid.UUID) -> Check:
    check = await check_repo.get_by_id(session, check_id)
    if check is None:
        raise CheckNotFoundError
    return check


async def list_checks(session: AsyncSession, limit: int, cursor: str | None) -> CheckPage:
    decoded = decode_cursor(cursor) if cursor else None
    rows = await check_repo.list_page(session, limit=limit + 1, cursor=decoded)
    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = encode_cursor(items[-1].checked_at, items[-1].id) if has_more else None
    return CheckPage(items=items, next_cursor=next_cursor, has_more=has_more)
