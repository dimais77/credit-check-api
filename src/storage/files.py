import uuid
from pathlib import Path

import anyio


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
