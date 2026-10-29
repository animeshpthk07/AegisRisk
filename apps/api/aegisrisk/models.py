from decimal import Decimal

from sqlalchemy import CheckConstraint, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Facility(Base):
    __tablename__ = "facilities"
    __table_args__ = (
        CheckConstraint("pd >= 0 AND pd <= 1", name="valid_pd"),
        CheckConstraint("lgd >= 0 AND lgd <= 1", name="valid_lgd"),
        CheckConstraint("ead >= 0", name="valid_ead"),
    )
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    borrower: Mapped[str] = mapped_column(String(100))
    industry: Mapped[str] = mapped_column(String(50), index=True)
    geography: Mapped[str] = mapped_column(String(50))
    rating: Mapped[str] = mapped_column(String(8))
    pd: Mapped[Decimal] = mapped_column(Numeric(12, 10))
    lgd: Mapped[Decimal] = mapped_column(Numeric(12, 10))
    ead: Mapped[Decimal] = mapped_column(Numeric(20, 2))


class SavedPortfolio(Base):
    """Immutable synthetic CSV snapshot; never merged into seeded facilities."""

    __tablename__ = "saved_portfolios"
    __table_args__ = (
        CheckConstraint("row_count >= 1 AND row_count <= 1000", name="valid_row_count"),
        UniqueConstraint("workspace_id", "digest", name="uq_saved_workspace_digest"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    workspace_id: Mapped[str] = mapped_column(String(36), default="local", server_default="local")
    digest: Mapped[str] = mapped_column(String(64))
    csv_text: Mapped[str] = mapped_column(Text)
    row_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(String(32))
