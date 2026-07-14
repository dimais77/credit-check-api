from collections.abc import Iterable
from hashlib import sha256

from core.enums import Program


def _of_file(filename: str, content_digest: str) -> str:
    return sha256(f"{filename}\0{content_digest}".encode()).hexdigest()


def from_digests(program: Program, files: Iterable[tuple[str, str]]) -> str:
    parts = sorted(_of_file(name, digest) for name, digest in files)
    return sha256("|".join([program.value, *parts]).encode()).hexdigest()


def from_bytes(program: Program, files: Iterable[tuple[str, bytes]]) -> str:
    return from_digests(program, [(name, sha256(content).hexdigest()) for name, content in files])
