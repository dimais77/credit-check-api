import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import Settings, get_settings
from core.database import get_session
from core.enums import Program
from schemas.check import CheckListItem, CheckResult
from schemas.pagination import CursorPage
from services import check_service
from services.upload import UploadedFile

router = APIRouter(prefix="/api/checks", tags=["checks"])

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


@router.post("", response_model=CheckResult, status_code=status.HTTP_201_CREATED)
async def create_check(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    program: Annotated[Program, Form()],
    idempotency_key: Annotated[str | None, Header()] = None,
    package_id: Annotated[uuid.UUID | None, Header()] = None,
    created_by: Annotated[str | None, Header()] = None,
    files: Annotated[list[UploadFile] | None, File()] = None,
) -> CheckResult:
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided")

    uploads = [
        UploadedFile(
            filename=file.filename or "",
            content_type=file.content_type,
            source=file,
        )
        for file in files
    ]
    check = await check_service.run_check(
        session,
        program,
        uploads,
        idempotency_key,
        package_id=package_id,
        created_by=created_by,
        base_dir=settings.storage.dir,
        max_size_mb=settings.storage.max_file_size_mb,
    )
    return CheckResult.model_validate(check)


@router.get("", response_model=CursorPage[CheckListItem])
async def list_checks(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    cursor: Annotated[str | None, Query()] = None,
) -> CursorPage[CheckListItem]:
    page = await check_service.list_checks(session, limit, cursor)
    items = [CheckListItem.model_validate(item) for item in page.items]
    return CursorPage[CheckListItem](
        items=items, next_cursor=page.next_cursor, has_more=page.has_more
    )


@router.get(
    "/{check_id}",
    response_model=CheckResult,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Check not found"}},
)
async def get_check(
    session: Annotated[AsyncSession, Depends(get_session)],
    check_id: uuid.UUID,
) -> CheckResult:
    check = await check_service.get_check(session, check_id)
    return CheckResult.model_validate(check)
