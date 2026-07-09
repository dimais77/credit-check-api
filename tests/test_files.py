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
