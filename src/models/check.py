import datetime
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Index, Text, func
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.enums import CheckStatus, Program
from models.base import Base, pg_enum
from models.mixin import UuidPkMixin

if TYPE_CHECKING:
    from models.document import Document
    from models.issue import Issue


class Check(UuidPkMixin, Base):
    __tablename__ = "checks"

    package_id: Mapped[uuid.UUID] = mapped_column()
    program: Mapped[Program] = mapped_column(pg_enum(Program, "program"))
    status: Mapped[CheckStatus] = mapped_column(pg_enum(CheckStatus, "check_status"))
    reason: Mapped[str | None] = mapped_column(Text)
    checked_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_by: Mapped[str | None] = mapped_column(Text)

    documents: Mapped[list["Document"]] = relationship(
        back_populates="check",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Document.position",
        collection_class=ordering_list("position"),
    )
    issues: Mapped[list["Issue"]] = relationship(
        back_populates="check",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Issue.position",
        collection_class=ordering_list("position"),
    )

    __table_args__ = (
        Index("ix_checks_checked_at_id", "checked_at", "id"),
        Index("ix_checks_package_id", "package_id"),
    )
