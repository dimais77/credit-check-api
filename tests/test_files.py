import asyncio
import uuid
from collections.abc import AsyncIterator
from hashlib import sha256
from pathlib import Path

from storage import files


async def _chunks(data: bytes, size: int = 3) -> AsyncIterator[bytes]:
    for start in range(0, len(data), size):
        yield data[start : start + size]


def test_save_stream(tmp_path: Path) -> None:
    check_id = uuid.uuid4()
    document_id = uuid.uuid4()
    data = b"contract contents"

    stored = asyncio.run(
        files.save_stream(tmp_path, check_id, document_id, ".pdf", _chunks(data), max_bytes=1024)
    )

    assert stored.path == f"{check_id}/{document_id}.pdf"
    assert stored.size_bytes == len(data)
    assert stored.digest == sha256(data).hexdigest()
    assert (tmp_path / str(stored.path)).read_bytes() == data


def test_save_stream_without_extension(tmp_path: Path) -> None:
    check_id = uuid.uuid4()
    document_id = uuid.uuid4()

    stored = asyncio.run(
        files.save_stream(tmp_path, check_id, document_id, "", _chunks(b"scan"), max_bytes=1024)
    )

    assert stored.path == f"{check_id}/{document_id}"
    assert (tmp_path / str(stored.path)).read_bytes() == b"scan"


def test_save_stream_aborts_and_skips_oversized(tmp_path: Path) -> None:
    check_id = uuid.uuid4()
    document_id = uuid.uuid4()
    data = b"x" * 100

    stored = asyncio.run(
        files.save_stream(tmp_path, check_id, document_id, ".pdf", _chunks(data), max_bytes=10)
    )

    assert stored.path is None
    assert stored.size_bytes == 11
    assert stored.digest == sha256(data[:10]).hexdigest()
    assert not (tmp_path / f"{check_id}/{document_id}.pdf").exists()


def test_delete_removes_check_files(tmp_path: Path) -> None:
    check_id = uuid.uuid4()
    asyncio.run(
        files.save_stream(tmp_path, check_id, uuid.uuid4(), ".pdf", _chunks(b"c"), max_bytes=1024)
    )
    assert (tmp_path / str(check_id)).exists()

    asyncio.run(files.delete(tmp_path, check_id))

    assert not (tmp_path / str(check_id)).exists()


def test_delete_missing_dir_is_noop(tmp_path: Path) -> None:
    asyncio.run(files.delete(tmp_path, uuid.uuid4()))
