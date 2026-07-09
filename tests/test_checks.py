import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio

FileSpec = tuple[str, tuple[str, bytes, str]]


def _file(name: str) -> FileSpec:
    return ("files", (name, b"document contents", "application/pdf"))


FEDERAL_COMPLETE = [
    _file("Договор.pdf"),
    _file("Спецификация.pdf"),
    _file("Счёт.pdf"),
    _file("Акт.pdf"),
]


async def test_create_approved(client: AsyncClient) -> None:
    response = await client.post("/api/checks", data={"program": "federal"}, files=FEDERAL_COMPLETE)
    assert response.status_code == 201
    body = response.json()
    assert uuid.UUID(body["check_id"])
    assert body["status"] == "approved"
    assert body["reason"] is None
    assert body["issues"] == []
    assert len(body["documents"]) == 4
    assert body["extracted"] is None
    assert body["status_label"] == "Можно заявлять в банк"
    assert body["checked_at"].endswith("Z")


async def test_create_rejected_missing_document(client: AsyncClient) -> None:
    response = await client.post(
        "/api/checks",
        data={"program": "regional"},
        files=[_file("Договор.pdf"), _file("Счёт.pdf")],
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "rejected"
    assert "акт" in body["reason"]
    assert any(issue["level"] == "error" for issue in body["issues"])


async def test_create_check_in_progress_on_warning(client: AsyncClient) -> None:
    response = await client.post(
        "/api/checks",
        data={"program": "regional"},
        files=[_file("Договор.txt"), _file("Счёт.pdf"), _file("Акт.pdf")],
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "check_in_progress"
    assert all(issue["level"] == "warning" for issue in body["issues"])


async def test_create_no_files_returns_400(client: AsyncClient) -> None:
    response = await client.post("/api/checks", data={"program": "federal"})
    assert response.status_code == 400
    assert response.json() == {"detail": "No files provided"}


async def test_create_invalid_program_returns_422(client: AsyncClient) -> None:
    response = await client.post(
        "/api/checks", data={"program": "bogus"}, files=[_file("Договор.pdf")]
    )
    assert response.status_code == 422


async def test_create_persists_files(client: AsyncClient, tmp_path: Path) -> None:
    response = await client.post("/api/checks", data={"program": "federal"}, files=FEDERAL_COMPLETE)
    check_id = response.json()["check_id"]
    stored = list((tmp_path / check_id).iterdir())
    assert len(stored) == 4


async def test_get_check(client: AsyncClient) -> None:
    created = await client.post("/api/checks", data={"program": "federal"}, files=FEDERAL_COMPLETE)
    check_id = created.json()["check_id"]

    response = await client.get(f"/api/checks/{check_id}")
    assert response.status_code == 200
    assert response.json()["check_id"] == check_id


async def test_get_check_not_found(client: AsyncClient) -> None:
    response = await client.get(f"/api/checks/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Check not found"}


async def test_get_check_invalid_uuid(client: AsyncClient) -> None:
    response = await client.get("/api/checks/not-a-uuid")
    assert response.status_code == 422


async def test_list_checks(client: AsyncClient) -> None:
    await client.post("/api/checks", data={"program": "federal"}, files=FEDERAL_COMPLETE)
    await client.post("/api/checks", data={"program": "regional"}, files=FEDERAL_COMPLETE)

    response = await client.get("/api/checks", params={"limit": 10, "offset": 0})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["limit"] == 10
    assert body["offset"] == 0
    assert len(body["items"]) == 2
    assert body["items"][0]["documents_count"] == 4


async def test_list_checks_invalid_limit_returns_422(client: AsyncClient) -> None:
    response = await client.get("/api/checks", params={"limit": 0})
    assert response.status_code == 422
