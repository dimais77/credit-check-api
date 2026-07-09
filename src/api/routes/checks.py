import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import Settings, get_settings
from core.database import get_session
from core.enums import Program
from core.exceptions import CheckNotFoundError
from repositories import check as check_repo
from schemas.check import CheckListItem, CheckResult
from schemas.pagination import Page
from services import check_service
from services.check_service import UploadedFile

router = APIRouter(prefix="/api/checks", tags=["checks"])


@router.post("", response_model=CheckResult, status_code=status.HTTP_201_CREATED)
async def create_check(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    program: Annotated[Program, Form()],
    files: Annotated[list[UploadFile] | None, File()] = None,
) -> CheckResult:
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided")

    uploads = [
        UploadedFile(
            filename=file.filename or "",
            content_type=file.content_type,
            data=await file.read(),
        )
        for file in files
    ]
    check = await check_service.run_check(
        session,
        program,
        uploads,
        base_dir=settings.storage.dir,
        max_size_mb=settings.storage.max_file_size_mb,
    )
    return CheckResult.model_validate(check)


@router.get("", response_model=Page[CheckListItem])
async def list_checks(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[CheckListItem]:
    rows = await check_repo.list_all(session, limit, offset)
    total = await check_repo.count(session)
    items = [CheckListItem.model_validate(row) for row in rows]
    return Page[CheckListItem](items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/{check_id}",
    response_model=CheckResult,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Check not found"}},
)
async def get_check(
    session: Annotated[AsyncSession, Depends(get_session)],
    check_id: uuid.UUID,
) -> CheckResult:
    check = await check_repo.get_by_id(session, check_id)
    if check is None:
        raise CheckNotFoundError
    return CheckResult.model_validate(check)
