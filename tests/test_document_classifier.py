import pytest

from core.enums import DocumentType
from services.document_classifier import classify_document


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("договор_47.pdf", DocumentType.CONTRACT),
        ("Договор.PDF", DocumentType.CONTRACT),
        ("спецификация.docx", DocumentType.SPECIFICATION),
        ("счет_на_оплату.pdf", DocumentType.INVOICE),
        ("счёт.pdf", DocumentType.INVOICE),
        ("акт.pdf", DocumentType.ACT),
        ("УПД_2025.pdf", DocumentType.ACT),
    ],
)
def test_classify_known(filename: str, expected: DocumentType) -> None:
    assert classify_document(filename) == expected


def test_classify_unknown() -> None:
    assert classify_document("scan_0041.jpg") is None
