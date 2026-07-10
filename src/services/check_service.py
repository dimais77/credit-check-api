import datetime
import logging
import uuid
from dataclasses import dataclass
from hashlib import sha256
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
from services.document_classifier import classify_document
from services.issue import Issue
from services.status import build_reason, resolve_status
from services.validation import check_completeness, validate_file
from storage import files

logger = logging.getLogger(__name__)

_TYPE_ORDER = {document_type: index for index, document_type in enumerate(DocumentType)}
_IN_PROGRESS_TTL = datetime.timedelta(seconds=60)


def _order_key(document: NewDocument) -> int:
    if document.detected_type is None:
        return len(_TYPE_ORDER)
    return _TYPE_ORDER[document.detected_type]


@dataclass(frozen=True, slots=True)
class UploadedFile:
    filename: str
    content_type: str | None
    data: bytes


@dataclass(frozen=True, slots=True)
class CheckPage:
    items: list[CheckSummary]
    total: int
    limit: int
    offset: int


def _compute_fingerprint(program: Program, uploads: list[UploadedFile]) -> str:
    digests = sorted(sha256(upload.data).hexdigest() for upload in uploads)
    payload = "|".join([program.value, *digests])
    return sha256(payload.encode()).hexdigest()


async def _prepare_check(
    check_id: uuid.UUID,
    program: Program,
    uploads: list[UploadedFile],
    *,
    base_dir: Path,
    max_size_mb: int,
) -> NewCheck:
    issues: list[Issue] = []
    documents: list[NewDocument] = []
    detected_types: set[DocumentType] = set()

    for upload in uploads:
        size_bytes = len(upload.data)
        detected = classify_document(upload.filename)
        issues.extend(validate_file(upload.filename, size_bytes, max_size_mb, detected))
        if detected is not None:
            detected_types.add(detected)

        document_id = uuid.uuid4()
        ext = Path(upload.filename).suffix
        storage_path = await files.save(base_dir, check_id, document_id, ext, upload.data)
        documents.append(
            NewDocument(
                id=document_id,
                name=upload.filename,
                detected_type=detected,
                size_bytes=size_bytes,
                content_type=upload.content_type,
                storage_path=storage_path,
            )
        )

    documents.sort(key=_order_key)

    issues.extend(check_completeness(detected_types, program))
    status = resolve_status(issues)
    reason = build_reason(issues, status)

    return NewCheck(
        id=check_id,
        program=program,
        status=status,
        reason=reason,
        checked_at=datetime.datetime.now(datetime.UTC),
        documents=documents,
        issues=[NewIssue(level=issue.level, message=issue.message) for issue in issues],
    )


async def run_check(
    session: AsyncSession,
    program: Program,
    uploads: list[UploadedFile],
    idempotency_key: str | None,
    *,
    base_dir: Path,
    max_size_mb: int,
) -> Check:
    if idempotency_key is not None:
        fingerprint = _compute_fingerprint(program, uploads)
        stale_before = datetime.datetime.now(datetime.UTC) - _IN_PROGRESS_TTL
        claimed = await idempotency_repo.claim(
            session, idempotency_key, fingerprint, stale_before=stale_before
        )
        await session.commit()
        if claimed is None:
            existing = await idempotency_repo.get_by_key(session, idempotency_key)
            if existing is None:
                raise IdempotencyKeyInProgressError
            if existing.fingerprint != fingerprint:
                raise IdempotencyKeyConflictError
            if existing.check_id is not None:
                return await get_check(session, existing.check_id)
            raise IdempotencyKeyInProgressError

    check_id = uuid.uuid4()
    try:
        new_check = await _prepare_check(
            check_id, program, uploads, base_dir=base_dir, max_size_mb=max_size_mb
        )
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


async def list_checks(session: AsyncSession, limit: int, offset: int) -> CheckPage:
    items = await check_repo.list_all(session, limit, offset)
    total = await check_repo.count(session)
    return CheckPage(items=items, total=total, limit=limit, offset=offset)
