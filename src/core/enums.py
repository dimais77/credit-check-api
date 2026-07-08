from enum import StrEnum


class Program(StrEnum):
    FEDERAL = "federal"
    REGIONAL = "regional"


class DocumentType(StrEnum):
    CONTRACT = "contract"
    SPECIFICATION = "specification"
    INVOICE = "invoice"
    ACT = "act"


class CheckStatus(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    CHECK_IN_PROGRESS = "check_in_progress"


class IssueLevel(StrEnum):
    ERROR = "error"
    WARNING = "warning"
