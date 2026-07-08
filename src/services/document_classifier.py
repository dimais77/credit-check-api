from core.enums import DocumentType

_PATTERNS: tuple[tuple[str, DocumentType], ...] = (
    ("договор", DocumentType.CONTRACT),
    ("спецификац", DocumentType.SPECIFICATION),
    ("счет", DocumentType.INVOICE),
    ("акт", DocumentType.ACT),
    ("упд", DocumentType.ACT),
)


def _normalize(filename: str) -> str:
    return filename.lower().replace("ё", "е")


def classify_document(filename: str) -> DocumentType | None:
    normalized = _normalize(filename)
    for pattern, document_type in _PATTERNS:
        if pattern in normalized:
            return document_type
    return None
