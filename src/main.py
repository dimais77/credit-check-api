from fastapi import FastAPI

from api.routes import health

app = FastAPI(
    title="Credit Check API",
    description="Preliminary validation of subsidized-loan document packages",
)

app.include_router(health.router)
