from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol

_CHUNK_SIZE = 1024 * 1024


class SupportsRead(Protocol):
    async def read(self, size: int, /) -> bytes: ...


@dataclass(frozen=True, slots=True)
class UploadedFile:
    filename: str
    content_type: str | None
    source: SupportsRead

    async def chunks(self) -> AsyncIterator[bytes]:
        while data := await self.source.read(_CHUNK_SIZE):
            yield data
