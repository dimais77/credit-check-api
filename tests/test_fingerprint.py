from core.enums import Program
from services import fingerprint


def test_order_independent() -> None:
    a = fingerprint.from_bytes(Program.FEDERAL, [("a.pdf", b"one"), ("b.pdf", b"two")])
    b = fingerprint.from_bytes(Program.FEDERAL, [("b.pdf", b"two"), ("a.pdf", b"one")])
    assert a == b


def test_filename_changes_fingerprint() -> None:
    same_bytes = b"same"
    a = fingerprint.from_bytes(Program.FEDERAL, [("contract.pdf", same_bytes)])
    b = fingerprint.from_bytes(Program.FEDERAL, [("invoice.pdf", same_bytes)])
    assert a != b


def test_content_changes_fingerprint() -> None:
    a = fingerprint.from_bytes(Program.FEDERAL, [("a.pdf", b"one")])
    b = fingerprint.from_bytes(Program.FEDERAL, [("a.pdf", b"two")])
    assert a != b


def test_program_changes_fingerprint() -> None:
    files = [("a.pdf", b"one")]
    assert fingerprint.from_bytes(Program.FEDERAL, files) != fingerprint.from_bytes(
        Program.REGIONAL, files
    )
