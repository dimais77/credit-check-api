import asyncio
import uuid
from pathlib import Path

from storage import files


def test_save(tmp_path: Path) -> None:
    check_id = uuid.uuid4()
    document_id = uuid.uuid4()

    key = asyncio.run(files.save(tmp_path, check_id, document_id, ".pdf", b"contract contents"))

    assert key == f"{check_id}/{document_id}.pdf"
    assert (tmp_path / key).read_bytes() == b"contract contents"


def test_save_without_extension(tmp_path: Path) -> None:
    check_id = uuid.uuid4()
    document_id = uuid.uuid4()

    key = asyncio.run(files.save(tmp_path, check_id, document_id, "", b"scanned document"))

    assert key == f"{check_id}/{document_id}"
    assert (tmp_path / key).read_bytes() == b"scanned document"


def test_delete_removes_check_files(tmp_path: Path) -> None:
    check_id = uuid.uuid4()
    asyncio.run(files.save(tmp_path, check_id, uuid.uuid4(), ".pdf", b"contract"))
    assert (tmp_path / str(check_id)).exists()

    asyncio.run(files.delete(tmp_path, check_id))

    assert not (tmp_path / str(check_id)).exists()


def test_delete_missing_dir_is_noop(tmp_path: Path) -> None:
    asyncio.run(files.delete(tmp_path, uuid.uuid4()))
