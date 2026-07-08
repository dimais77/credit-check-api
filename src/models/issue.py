import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.enums import IssueLevel
from models.base import Base, pg_enum
from models.mixin import UuidPkMixin

if TYPE_CHECKING:
    from models.check import Check


class Issue(UuidPkMixin, Base):
    __tablename__ = "issues"

    check_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("checks.id", ondelete="CASCADE"))
    level: Mapped[IssueLevel] = mapped_column(pg_enum(IssueLevel, "issue_level"))
    message: Mapped[str] = mapped_column(Text)

    check: Mapped["Check"] = relationship(back_populates="issues")
