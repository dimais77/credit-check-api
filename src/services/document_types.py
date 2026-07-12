import re
from dataclasses import dataclass

from core.enums import DocumentType


@dataclass(frozen=True, slots=True)
class DocumentMeta:
    label: str
    pattern: re.Pattern[str]


DOCUMENT_META: dict[DocumentType, DocumentMeta] = {
    DocumentType.CONTRACT: DocumentMeta(label="договор", pattern=re.compile(r"\bдоговор")),
    DocumentType.SPECIFICATION: DocumentMeta(
        label="спецификация", pattern=re.compile(r"\bспецификац")
    ),
    DocumentType.INVOICE: DocumentMeta(label="счёт", pattern=re.compile(r"\bсчет\b")),
    DocumentType.ACT: DocumentMeta(label="акт", pattern=re.compile(r"\b(?:акт|упд)\b")),
}

CLASSIFICATION_ORDER: tuple[DocumentType, ...] = (
    DocumentType.SPECIFICATION,
    DocumentType.INVOICE,
    DocumentType.ACT,
    DocumentType.CONTRACT,
)
