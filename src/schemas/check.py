import datetime
import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, computed_field

from core.enums import CheckStatus, DocumentType, IssueLevel, Program

STATUS_LABELS: dict[CheckStatus, str] = {
    CheckStatus.REJECTED: "Нельзя заявлять в банк",
    CheckStatus.CHECK_IN_PROGRESS: "Требуется ручная проверка",
    CheckStatus.APPROVED: "Можно заявлять в банк",
}


def _to_utc_z(value: datetime.datetime) -> str:
    return value.astimezone(datetime.UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


UtcDateTime = Annotated[
    datetime.datetime, PlainSerializer(_to_utc_z, return_type=str, when_used="json")
]


class IssueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    level: IssueLevel
    message: str


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    detected_type: DocumentType | None
    size_bytes: int = Field(exclude=True)

    @computed_field
    def size_kb(self) -> int:
        return round(self.size_bytes / 1024)


class ExtractedData(BaseModel):
    pass


class CheckResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    check_id: uuid.UUID = Field(validation_alias="id")
    status: CheckStatus
    reason: str | None
    issues: list[IssueOut]
    documents: list[DocumentOut]
    extracted: ExtractedData | None = None
    checked_at: UtcDateTime

    @computed_field
    def status_label(self) -> str:
        return STATUS_LABELS[self.status]


class CheckListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    checked_at: UtcDateTime
    program: Program
    status: CheckStatus
    documents_count: int
