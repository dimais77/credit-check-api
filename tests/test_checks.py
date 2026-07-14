import datetime
import io
import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import Program
from models import IdempotencyKey
from repositories import check as check_repo
from services import check_service

pytestmark = pytest.mark.anyio

FileSpec = tuple[str, tuple[str, bytes, str]]


class BytesReader:
    def __init__(self, data: bytes) -> None:
        self._buffer = io.BytesIO(data)

    async def read(self, size: int) -> bytes:
        return self._buffer.read(size)


def _file(name: str) -> FileSpec:
    return "files", (name, b"document contents", "application/pdf")


def _idempotency_headers() -> dict[str, str]:
    return {"Idempotency-Key": str(uuid.uuid4())}


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


async def test_create_without_idempotency_key_creates_separate_checks(client: AsyncClient) -> None:
    first = await client.post("/api/checks", data={"program": "federal"}, files=FEDERAL_COMPLETE)
    second = await client.post("/api/checks", data={"program": "federal"}, files=FEDERAL_COMPLETE)

    assert first.status_code == second.status_code == 201
    assert first.json()["check_id"] != second.json()["check_id"]


async def test_files_cleaned_up_on_db_failure(
    session: AsyncSession, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def failing_create(_session: object, _dto: object) -> None:
        raise RuntimeError("db unavailable")

    monkeypatch.setattr(check_repo, "create", failing_create)

    uploads = [
        check_service.UploadedFile(
            filename=name, content_type="application/pdf", source=BytesReader(b"x")
        )
        for name in ("Договор.pdf", "Спецификация.pdf", "Счёт.pdf", "Акт.pdf")
    ]

    with pytest.raises(RuntimeError):
        await check_service.run_check(
            session, Program.FEDERAL, uploads, None, base_dir=tmp_path, max_size_mb=20
        )

    assert list(tmp_path.iterdir()) == []


async def test_get_check(client: AsyncClient) -> None:
    created = await client.post("/api/checks", data={"program": "federal"}, files=FEDERAL_COMPLETE)
    check_id = created.json()["check_id"]

    response = await client.get(f"/api/checks/{check_id}")
    assert response.status_code == 200
    assert response.json()["check_id"] == check_id


async def test_documents_sorted_in_canonical_order(client: AsyncClient) -> None:
    files = [_file("Акт.pdf"), _file("Счёт.pdf"), _file("Договор.pdf"), _file("Спецификация.pdf")]
    expected = ["Договор.pdf", "Спецификация.pdf", "Счёт.pdf", "Акт.pdf"]

    created = await client.post("/api/checks", data={"program": "federal"}, files=files)
    check_id = created.json()["check_id"]
    assert [doc["name"] for doc in created.json()["documents"]] == expected

    fetched = await client.get(f"/api/checks/{check_id}")
    assert [doc["name"] for doc in fetched.json()["documents"]] == expected


async def test_unrecognized_document_sorted_last(client: AsyncClient) -> None:
    files = [_file("scan_0041.jpg"), _file("Договор.pdf"), _file("Счёт.pdf"), _file("Акт.pdf")]
    expected = ["Договор.pdf", "Счёт.pdf", "Акт.pdf", "scan_0041.jpg"]

    created = await client.post("/api/checks", data={"program": "regional"}, files=files)
    assert [doc["name"] for doc in created.json()["documents"]] == expected


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


_FEDERAL_CONTENTS = [b"document contents"] * 4


async def test_create_replays_same_check_for_same_key(client: AsyncClient) -> None:
    headers = _idempotency_headers()

    first = await client.post(
        "/api/checks", data={"program": "federal"}, files=FEDERAL_COMPLETE, headers=headers
    )
    second = await client.post(
        "/api/checks", data={"program": "federal"}, files=FEDERAL_COMPLETE, headers=headers
    )

    assert first.status_code == second.status_code == 201
    assert first.json()["check_id"] == second.json()["check_id"]

    listed = await client.get("/api/checks")
    assert listed.json()["total"] == 1


async def test_create_conflicts_on_key_reused_with_different_payload(client: AsyncClient) -> None:
    headers = _idempotency_headers()

    first = await client.post(
        "/api/checks", data={"program": "federal"}, files=FEDERAL_COMPLETE, headers=headers
    )
    second = await client.post(
        "/api/checks",
        data={"program": "regional"},
        files=[_file("Договор.pdf"), _file("Счёт.pdf"), _file("Акт.pdf")],
        headers=headers,
    )

    assert first.status_code == 201
    assert second.status_code == 422


async def test_create_returns_409_while_key_still_in_progress(
    client: AsyncClient, session: AsyncSession
) -> None:
    key = str(uuid.uuid4())
    fingerprint = check_service._compute_fingerprint(Program.FEDERAL, _FEDERAL_CONTENTS)
    session.add(IdempotencyKey(key=key, fingerprint=fingerprint, check_id=None))
    await session.commit()

    response = await client.post(
        "/api/checks",
        data={"program": "federal"},
        files=FEDERAL_COMPLETE,
        headers={"Idempotency-Key": key},
    )

    assert response.status_code == 409


async def test_create_reclaims_stale_in_progress_key(
    client: AsyncClient, session: AsyncSession
) -> None:
    key = str(uuid.uuid4())
    fingerprint = check_service._compute_fingerprint(Program.FEDERAL, _FEDERAL_CONTENTS)
    stale_at = datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=1)
    session.add(
        IdempotencyKey(key=key, fingerprint=fingerprint, check_id=None, created_at=stale_at)
    )
    await session.commit()

    response = await client.post(
        "/api/checks",
        data={"program": "federal"},
        files=FEDERAL_COMPLETE,
        headers={"Idempotency-Key": key},
    )

    assert response.status_code == 201
