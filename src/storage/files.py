import shutil
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import anyio
from anyio import to_thread


@dataclass(frozen=True, slots=True)
class StoredFile:
    path: str | None
    size_bytes: int
    digest: str


async def save_stream(
    base_dir: Path,
    check_id: uuid.UUID,
    document_id: uuid.UUID,
    ext: str,
    chunks: AsyncIterator[bytes],
    *,
    max_bytes: int,
) -> StoredFile:
    key = f"{check_id}/{document_id}{ext}"
    path = anyio.Path(base_dir) / key
    await path.parent.mkdir(parents=True, exist_ok=True)

    hasher = sha256()
    size = 0
    oversized = False
    async with await path.open("wb") as buffer:
        async for chunk in chunks:
            if size + len(chunk) > max_bytes:
                hasher.update(chunk[: max_bytes - size])
                oversized = True
                break
            await buffer.write(chunk)
            hasher.update(chunk)
            size += len(chunk)

    if oversized:
        await path.unlink(missing_ok=True)
        return StoredFile(path=None, size_bytes=max_bytes + 1, digest=hasher.hexdigest())
    return StoredFile(path=key, size_bytes=size, digest=hasher.hexdigest())


def _rmtree(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)


async def delete(base_dir: Path, check_id: uuid.UUID) -> None:
    path = Path(base_dir) / str(check_id)
    await to_thread.run_sync(_rmtree, path)
