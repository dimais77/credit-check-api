import datetime
import uuid
from dataclasses import dataclass

from core.enums import CheckStatus, DocumentType, IssueLevel, Program


@dataclass(frozen=True, kw_only=True, slots=True)
class NewIssue:
    level: IssueLevel
    message: str


@dataclass(frozen=True, kw_only=True, slots=True)
class NewDocument:
    id: uuid.UUID
    name: str
    detected_type: DocumentType | None
    size_bytes: int
    content_type: str | None
    storage_path: str


@dataclass(frozen=True, kw_only=True, slots=True)
class NewCheck:
    id: uuid.UUID
    program: Program
    status: CheckStatus
    reason: str | None
    checked_at: datetime.datetime
    documents: list[NewDocument]
    issues: list[NewIssue]


@dataclass(frozen=True, kw_only=True, slots=True)
class CheckSummary:
    id: uuid.UUID
    checked_at: datetime.datetime
    program: Program
    status: CheckStatus
    documents_count: int
