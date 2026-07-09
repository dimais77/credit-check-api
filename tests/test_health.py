import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from core import database
from main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


class _StubConnection:
    def __init__(self, error: Exception | None) -> None:
        self._error = error

    async def __aenter__(self) -> "_StubConnection":
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    async def execute(self, _statement: object) -> None:
        if self._error is not None:
            raise self._error


class _StubEngine:
    def __init__(self, error: Exception | None = None) -> None:
        self._error = error

    def connect(self) -> _StubConnection:
        return _StubConnection(self._error)


def test_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database, "engine", _StubEngine())

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_ready_db_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database, "engine", _StubEngine(SQLAlchemyError("db down")))

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
