from core.enums import DocumentType
from services.document_types import DOCUMENT_META


def _normalize(filename: str) -> str:
    return filename.lower().replace("ё", "е")


def classify_document(filename: str) -> DocumentType | None:
    normalized = _normalize(filename)
    for document_type in DocumentType:
        if any(pattern in normalized for pattern in DOCUMENT_META[document_type].patterns):
            return document_type
    return None
