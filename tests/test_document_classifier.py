import pytest

from core.enums import DocumentType
from services.document_classifier import classify_document
from services.document_types import DOCUMENT_META


def test_document_meta_covers_all_types() -> None:
    assert set(DOCUMENT_META) == set(DocumentType)


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("договор_47.pdf", DocumentType.CONTRACT),
        ("Договор.PDF", DocumentType.CONTRACT),
        ("договора_поставки.pdf", DocumentType.CONTRACT),
        ("спецификация.docx", DocumentType.SPECIFICATION),
        ("спецификации_2025.pdf", DocumentType.SPECIFICATION),
        ("счет_на_оплату.pdf", DocumentType.INVOICE),
        ("счёт.pdf", DocumentType.INVOICE),
        ("акт.pdf", DocumentType.ACT),
        ("УПД_2025.pdf", DocumentType.ACT),
    ],
)
def test_classify_known(filename: str, expected: DocumentType) -> None:
    assert classify_document(filename) == expected


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("спецификация_к_договору.pdf", DocumentType.SPECIFICATION),
        ("акт_к_договору.pdf", DocumentType.ACT),
        ("счёт_по_договору.pdf", DocumentType.INVOICE),
    ],
)
def test_classify_specific_wins_over_contract(filename: str, expected: DocumentType) -> None:
    assert classify_document(filename) == expected


@pytest.mark.parametrize(
    "filename",
    [
        "scan_0041.jpg",
        "счётчик_показания.pdf",
        "актуальный_прайс.pdf",
    ],
)
def test_classify_unknown(filename: str) -> None:
    assert classify_document(filename) is None
