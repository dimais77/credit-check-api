import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.enums import DocumentType
from models.base import Base, pg_enum
from models.mixin import UuidPkMixin

if TYPE_CHECKING:
    from models.check import Check


class Document(UuidPkMixin, Base):
    __tablename__ = "documents"

    check_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("checks.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(Text)
    detected_type: Mapped[DocumentType | None] = mapped_column(
        pg_enum(DocumentType, "document_type")
    )
    size_bytes: Mapped[int]
    content_type: Mapped[str | None] = mapped_column(Text)
    storage_path: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int]

    check: Mapped["Check"] = relationship(back_populates="documents")

    __table_args__ = (Index("ix_documents_check_id", "check_id"),)
