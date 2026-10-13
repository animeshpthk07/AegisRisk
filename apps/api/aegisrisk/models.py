from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric, String
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
