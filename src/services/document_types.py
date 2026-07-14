from dataclasses import dataclass

from core.enums import DocumentType


@dataclass(frozen=True, slots=True)
class DocumentMeta:
    label: str
    patterns: tuple[str, ...]


DOCUMENT_META: dict[DocumentType, DocumentMeta] = {
    DocumentType.CONTRACT: DocumentMeta(label="договор", patterns=(r"\bдоговор",)),
    DocumentType.SPECIFICATION: DocumentMeta(label="спецификация", patterns=(r"\bспецификац",)),
    DocumentType.INVOICE: DocumentMeta(
        label="счёт", patterns=(r"\bсчет(?:ами|ах|ам|ов|ом|а|у|е|ы)?\b",)
    ),
    DocumentType.ACT: DocumentMeta(
        label="акт", patterns=(r"\bакт(?:ами|ах|ам|ов|ом|а|у|е|ы)?\b", r"\bупд\b")
    ),
}

CLASSIFICATION_ORDER: tuple[DocumentType, ...] = (
    DocumentType.SPECIFICATION,
    DocumentType.INVOICE,
    DocumentType.ACT,
    DocumentType.CONTRACT,
)
