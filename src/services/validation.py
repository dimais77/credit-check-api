from pathlib import Path

from core.enums import DocumentType, IssueLevel, Program
from services.document_classifier import classify_document
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

_TYPE_LABELS: dict[DocumentType, str] = {
    DocumentType.CONTRACT: "договор",
    DocumentType.SPECIFICATION: "спецификация",
    DocumentType.INVOICE: "счёт",
    DocumentType.ACT: "акт",
}


def validate_file(filename: str, size_bytes: int, max_size_mb: int) -> list[Issue]:
    issues: list[Issue] = []

    if Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        issues.append(Issue(IssueLevel.WARNING, f"Недопустимый формат файла: «{filename}»"))

    if size_bytes > max_size_mb * 1024 * 1024:
        issues.append(
            Issue(IssueLevel.WARNING, f"Размер файла превышает {max_size_mb} МБ: «{filename}»")
        )

    if classify_document(filename) is None:
        issues.append(
            Issue(IssueLevel.WARNING, f"Не удалось определить тип документа: «{filename}»")
        )

    return issues


def check_completeness(detected: set[DocumentType], program: Program) -> list[Issue]:
    return [
        Issue(IssueLevel.ERROR, f"Отсутствует обязательный документ: {_TYPE_LABELS[document_type]}")
        for document_type in _REQUIRED_TYPES[program]
        if document_type not in detected
    ]
