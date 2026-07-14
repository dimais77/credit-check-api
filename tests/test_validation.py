from core.enums import DocumentType, IssueLevel, Program
from services.validation import check_completeness, check_duplicates, validate_file

MAX_SIZE_MB = 20


def test_valid_file_no_issues() -> None:
    assert validate_file("договор.pdf", 1024, MAX_SIZE_MB, DocumentType.CONTRACT) == []


def test_unrecognized_name_warning() -> None:
    issues = validate_file("scan_0041.jpg", 1024, MAX_SIZE_MB, None)

    assert [issue.level for issue in issues] == [IssueLevel.WARNING]
    assert issues[0].message == "Не удалось определить тип документа: «scan_0041.jpg»"


def test_invalid_format_warning() -> None:
    issues = validate_file("договор.txt", 1024, MAX_SIZE_MB, DocumentType.CONTRACT)

    assert [issue.level for issue in issues] == [IssueLevel.WARNING]


def test_oversized_file_warning() -> None:
    issues = validate_file("договор.pdf", 21 * 1024 * 1024, MAX_SIZE_MB, DocumentType.CONTRACT)

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


def test_no_duplicates_no_issues() -> None:
    counts = {
        DocumentType.CONTRACT: 1,
        DocumentType.SPECIFICATION: 1,
        DocumentType.INVOICE: 1,
        DocumentType.ACT: 1,
    }

    assert check_duplicates(counts, Program.FEDERAL) == []


def test_duplicate_required_type_warning() -> None:
    counts = {DocumentType.CONTRACT: 2, DocumentType.INVOICE: 1, DocumentType.ACT: 1}

    issues = check_duplicates(counts, Program.REGIONAL)

    assert [issue.level for issue in issues] == [IssueLevel.WARNING]
    assert issues[0].message == "Несколько документов типа «договор» в пакете"


def test_duplicate_non_required_type_ignored() -> None:
    counts = {
        DocumentType.CONTRACT: 1,
        DocumentType.INVOICE: 1,
        DocumentType.ACT: 1,
        DocumentType.SPECIFICATION: 2,
    }

    assert check_duplicates(counts, Program.REGIONAL) == []
