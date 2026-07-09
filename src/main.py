from fastapi import FastAPI

from api.routes import health
from core.config import get_settings
from core.exceptions import register_exception_handlers
from core.logging import configure_logging

configure_logging(get_settings().log_level)

app = FastAPI(
    title="Credit Check API",
    description="Preliminary validation of subsidized-loan document packages",
)

register_exception_handlers(app)
app.include_router(health.router)
