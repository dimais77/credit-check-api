from core.enums import CheckStatus, IssueLevel
from services.issue import Issue


def resolve_status(issues: list[Issue]) -> CheckStatus:
    if any(issue.level is IssueLevel.ERROR for issue in issues):
        return CheckStatus.REJECTED
    if any(issue.level is IssueLevel.WARNING for issue in issues):
        return CheckStatus.CHECK_IN_PROGRESS
    return CheckStatus.APPROVED


def build_reason(issues: list[Issue], status: CheckStatus) -> str | None:
    if status is CheckStatus.REJECTED:
        return next(issue.message for issue in issues if issue.level is IssueLevel.ERROR)
    if status is CheckStatus.CHECK_IN_PROGRESS:
        return next(issue.message for issue in issues if issue.level is IssueLevel.WARNING)
    return None
