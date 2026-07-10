import datetime
import logging
import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import DocumentType, Program
from models import Check
from repositories import check as check_repo
from repositories.dto import NewCheck, NewDocument, NewIssue
from services.document_classifier import classify_document
from services.issue import Issue
from services.status import build_reason, resolve_status
from services.validation import check_completeness, validate_file
from storage import files

logger = logging.getLogger(__name__)

# Canonical document-flow order (contract → specification → invoice → act);
# unrecognized documents go last.
_TYPE_ORDER = {document_type: index for index, document_type in enumerate(DocumentType)}


def _order_key(document: NewDocument) -> int:
    if document.detected_type is None:
        return len(_TYPE_ORDER)
    return _TYPE_ORDER[document.detected_type]


@dataclass(frozen=True, slots=True)
class UploadedFile:
    filename: str
    content_type: str | None
    data: bytes


async def run_check(
    session: AsyncSession,
    program: Program,
    uploads: list[UploadedFile],
    *,
    base_dir: Path,
    max_size_mb: int,
) -> Check:
    check_id = uuid.uuid4()
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

    new_check = NewCheck(
        id=check_id,
        program=program,
        status=status,
        reason=reason,
        checked_at=datetime.datetime.now(datetime.UTC),
        documents=documents,
        issues=[NewIssue(level=issue.level, message=issue.message) for issue in issues],
    )

    try:
        created = await check_repo.create(session, new_check)
        await session.commit()
    except SQLAlchemyError:
        logger.exception(
            "Commit failed for check %s; %d file(s) orphaned under %s",
            check_id,
            len(documents),
            base_dir / str(check_id),
        )
        raise

    return created
