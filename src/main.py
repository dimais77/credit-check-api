from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import checks, health
from core import database
from core.config import get_settings
from core.exceptions import register_exception_handlers
from core.logging import configure_logging

configure_logging(get_settings().log_level)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    yield
    await database.dispose()


app = FastAPI(
    title="Credit Check API",
    description="Preliminary validation of subsidized-loan document packages",
    lifespan=lifespan,
)

register_exception_handlers(app)
app.include_router(health.router)
app.include_router(checks.router)
