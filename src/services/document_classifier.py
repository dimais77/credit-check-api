import re

from core.enums import DocumentType
from services.document_types import CLASSIFICATION_ORDER, DOCUMENT_META

_PATTERNS: dict[DocumentType, tuple[re.Pattern[str], ...]] = {
    document_type: tuple(re.compile(source) for source in meta.patterns)
    for document_type, meta in DOCUMENT_META.items()
}


def _normalize(filename: str) -> str:
    return filename.lower().replace("ё", "е").replace("_", " ")


def classify_document(filename: str) -> DocumentType | None:
    normalized = _normalize(filename)
    for document_type in CLASSIFICATION_ORDER:
        if any(pattern.search(normalized) for pattern in _PATTERNS[document_type]):
            return document_type
    return None
