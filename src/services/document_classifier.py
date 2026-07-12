from core.enums import DocumentType
from services.document_types import CLASSIFICATION_ORDER, DOCUMENT_META


def _normalize(filename: str) -> str:
    return filename.lower().replace("ё", "е").replace("_", " ")


def classify_document(filename: str) -> DocumentType | None:
    normalized = _normalize(filename)
    for document_type in CLASSIFICATION_ORDER:
        if DOCUMENT_META[document_type].pattern.search(normalized):
            return document_type
    return None
