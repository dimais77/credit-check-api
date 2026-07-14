import datetime
import uuid
from types import SimpleNamespace

import pytest

from core.enums import CheckStatus, DocumentType, IssueLevel, Program
from schemas.check import CheckListItem, CheckResult
from schemas.pagination import CursorPage

CHECKED_AT = datetime.datetime(2025, 3, 15, 14, 32, 0, 654321, tzinfo=datetime.UTC)


def _orm_check(status: CheckStatus = CheckStatus.REJECTED) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        package_id=uuid.uuid4(),
        program=Program.FEDERAL,
        status=status,
        reason="Отсутствует обязательный документ: спецификация",
        checked_at=CHECKED_AT,
        created_by=None,
        documents=[
            SimpleNamespace(
                name="договор_47.pdf", detected_type=DocumentType.CONTRACT, size_bytes=145408
            )
        ],
        issues=[
            SimpleNamespace(
                level=IssueLevel.ERROR, message="Отсутствует обязательный документ: спецификация"
            )
        ],
    )


def test_check_result() -> None:
    orm = _orm_check()

    payload = CheckResult.model_validate(orm).model_dump(mode="json")

    assert payload["check_id"] == str(orm.id)
    assert payload["package_id"] == str(orm.package_id)
    assert payload["program"] == "federal"
    assert payload["extracted"] is None
    assert payload["checked_at"] == "2025-03-15T14:32:00Z"
    assert payload["documents"][0] == {
        "name": "договор_47.pdf",
        "detected_type": "contract",
        "size_kb": 142,
    }


@pytest.mark.parametrize(
    ("status", "label"),
    [
        (CheckStatus.REJECTED, "Нельзя заявлять в банк"),
        (CheckStatus.CHECK_IN_PROGRESS, "Требуется ручная проверка"),
        (CheckStatus.APPROVED, "Можно заявлять в банк"),
    ],
)
def test_status_label(status: CheckStatus, label: str) -> None:
    payload = CheckResult.model_validate(_orm_check(status)).model_dump(mode="json")

    assert payload["status"] == status.value
    assert payload["status_label"] == label


def test_page() -> None:
    row = SimpleNamespace(
        id=uuid.uuid4(),
        package_id=uuid.uuid4(),
        checked_at=CHECKED_AT,
        program=Program.FEDERAL,
        status=CheckStatus.REJECTED,
        documents_count=3,
    )

    page = CursorPage[CheckListItem](
        items=[CheckListItem.model_validate(row)], next_cursor="abc", has_more=True
    )
    payload = page.model_dump(mode="json")

    assert payload["next_cursor"] == "abc"
    assert payload["has_more"] is True
    assert payload["items"][0] == {
        "check_id": str(row.id),
        "package_id": str(row.package_id),
        "checked_at": "2025-03-15T14:32:00Z",
        "program": "federal",
        "status": "rejected",
        "documents_count": 3,
    }
