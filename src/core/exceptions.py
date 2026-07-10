import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "Internal error"


class CheckNotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Check not found"


class IdempotencyKeyConflictError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    detail = "Idempotency-Key was already used with a different request"


class IdempotencyKeyInProgressError(AppError):
    status_code = status.HTTP_409_CONFLICT
    detail = "A request with this Idempotency-Key is already being processed"


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


async def unhandled_error_handler(_request: Request, _exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_error_handler)
