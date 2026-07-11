import shutil
import uuid
from pathlib import Path

import anyio
from anyio import to_thread


async def save(
    base_dir: Path,
    check_id: uuid.UUID,
    document_id: uuid.UUID,
    ext: str,
    data: bytes,
) -> str:
    key = f"{check_id}/{document_id}{ext}"
    path = anyio.Path(base_dir) / key
    await path.parent.mkdir(parents=True, exist_ok=True)
    await path.write_bytes(data)
    return key


def _rmtree(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)


async def delete(base_dir: Path, check_id: uuid.UUID) -> None:
    path = Path(base_dir) / str(check_id)
    await to_thread.run_sync(_rmtree, path)
