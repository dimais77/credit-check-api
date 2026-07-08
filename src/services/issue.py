from dataclasses import dataclass

from core.enums import IssueLevel


@dataclass(frozen=True, slots=True)
class Issue:
    level: IssueLevel
    message: str
