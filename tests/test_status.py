from core.enums import CheckStatus, IssueLevel
from services.issue import Issue
from services.status import build_reason, resolve_status

ERROR = Issue(IssueLevel.ERROR, "Отсутствует обязательный документ: спецификация")
WARNING = Issue(IssueLevel.WARNING, "Не удалось определить тип документа: «scan.jpg»")


def test_resolve_rejected() -> None:
    assert resolve_status([ERROR, WARNING]) is CheckStatus.REJECTED


def test_resolve_check_in_progress() -> None:
    assert resolve_status([WARNING]) is CheckStatus.CHECK_IN_PROGRESS


def test_resolve_approved() -> None:
    assert resolve_status([]) is CheckStatus.APPROVED


def test_reason_rejected_first_error() -> None:
    assert build_reason([ERROR, WARNING], CheckStatus.REJECTED) == ERROR.message


def test_reason_check_in_progress_first_warning() -> None:
    assert build_reason([WARNING], CheckStatus.CHECK_IN_PROGRESS) == WARNING.message


def test_reason_approved_none() -> None:
    assert build_reason([], CheckStatus.APPROVED) is None
