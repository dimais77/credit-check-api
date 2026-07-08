from core.enums import DocumentType, IssueLevel, Program
from services.validation import check_completeness, validate_file

MAX_SIZE_MB = 20


def test_valid_file_no_issues() -> None:
    assert validate_file("договор.pdf", 1024, MAX_SIZE_MB) == []


def test_unrecognized_name_warning() -> None:
    issues = validate_file("scan_0041.jpg", 1024, MAX_SIZE_MB)

    assert [issue.level for issue in issues] == [IssueLevel.WARNING]
    assert issues[0].message == "Не удалось определить тип документа: «scan_0041.jpg»"


def test_invalid_format_warning() -> None:
    issues = validate_file("договор.txt", 1024, MAX_SIZE_MB)

    assert [issue.level for issue in issues] == [IssueLevel.WARNING]


def test_oversized_file_warning() -> None:
    issues = validate_file("договор.pdf", 21 * 1024 * 1024, MAX_SIZE_MB)

    assert [issue.level for issue in issues] == [IssueLevel.WARNING]


def test_federal_complete() -> None:
    detected = {
        DocumentType.CONTRACT,
        DocumentType.SPECIFICATION,
        DocumentType.INVOICE,
        DocumentType.ACT,
    }

    assert check_completeness(detected, Program.FEDERAL) == []


def test_federal_missing_specification() -> None:
    detected = {DocumentType.CONTRACT, DocumentType.INVOICE, DocumentType.ACT}

    issues = check_completeness(detected, Program.FEDERAL)

    assert [issue.level for issue in issues] == [IssueLevel.ERROR]
    assert issues[0].message == "Отсутствует обязательный документ: спецификация"


def test_regional_complete() -> None:
    detected = {DocumentType.CONTRACT, DocumentType.INVOICE, DocumentType.ACT}

    assert check_completeness(detected, Program.REGIONAL) == []
