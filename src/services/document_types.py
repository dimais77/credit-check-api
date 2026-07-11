from dataclasses import dataclass

from core.enums import DocumentType


@dataclass(frozen=True, slots=True)
class DocumentMeta:
    label: str
    patterns: tuple[str, ...]


DOCUMENT_META: dict[DocumentType, DocumentMeta] = {
    DocumentType.CONTRACT: DocumentMeta(label="договор", patterns=("договор",)),
    DocumentType.SPECIFICATION: DocumentMeta(label="спецификация", patterns=("спецификац",)),
    DocumentType.INVOICE: DocumentMeta(label="счёт", patterns=("счет",)),
    DocumentType.ACT: DocumentMeta(label="акт", patterns=("акт", "упд")),
}
