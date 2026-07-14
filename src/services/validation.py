from collections.abc import Mapping
from pathlib import Path

from core.enums import DocumentType, IssueLevel, Program
from services.document_types import DOCUMENT_META
from services.issue import Issue

ALLOWED_EXTENSIONS = frozenset({".pdf", ".docx", ".jpg", ".png"})

_REQUIRED_TYPES: dict[Program, tuple[DocumentType, ...]] = {
    Program.FEDERAL: (
        DocumentType.CONTRACT,
        DocumentType.SPECIFICATION,
        DocumentType.INVOICE,
        DocumentType.ACT,
    ),
    Program.REGIONAL: (
        DocumentType.CONTRACT,
        DocumentType.INVOICE,
        DocumentType.ACT,
    ),
}


def validate_file(
    filename: str, size_bytes: int, max_size_mb: int, detected: DocumentType | None
) -> list[Issue]:
    issues: list[Issue] = []

    if Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        issues.append(Issue(IssueLevel.WARNING, f"Недопустимый формат файла: «{filename}»"))

    if size_bytes > max_size_mb * 1024 * 1024:
        issues.append(
            Issue(IssueLevel.WARNING, f"Размер файла превышает {max_size_mb} МБ: «{filename}»")
        )

    if detected is None:
        issues.append(
            Issue(IssueLevel.WARNING, f"Не удалось определить тип документа: «{filename}»")
        )

    return issues


def check_completeness(detected: set[DocumentType], program: Program) -> list[Issue]:
    return [
        Issue(
            IssueLevel.ERROR,
            f"Отсутствует обязательный документ: {DOCUMENT_META[document_type].label}",
        )
        for document_type in _REQUIRED_TYPES[program]
        if document_type not in detected
    ]


def check_duplicates(counts: Mapping[DocumentType, int], program: Program) -> list[Issue]:
    return [
        Issue(
            IssueLevel.WARNING,
            f"Несколько документов типа «{DOCUMENT_META[document_type].label}» в пакете",
        )
        for document_type in _REQUIRED_TYPES[program]
        if counts.get(document_type, 0) > 1
    ]
