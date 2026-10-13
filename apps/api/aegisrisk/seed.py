"""Explicit, idempotent demo load; refuses to overwrite existing data."""

from decimal import Decimal

from sqlalchemy import func, select

from .database import SessionLocal
from .models import Facility


def seed():
    with SessionLocal() as session:
        if session.scalar(select(func.count()).select_from(Facility)):
            print("Existing portfolio retained; no rows modified.")
            return
        industries = ["Manufacturing", "Technology", "Healthcare", "Retail", "Energy"]
        for i in range(1, 41):
            session.add(
                Facility(
                    id=f"SYN-{i:03}",
                    borrower=f"Fictional Borrower {i:03}",
                    industry=industries[(i - 1) % 5],
                    geography=["West", "North", "South", "East"][i % 4],
                    rating=["A", "BBB", "BB", "B"][i % 4],
                    pd=Decimal(["0.01", "0.025", "0.06", "0.12"][i % 4]),
                    lgd=Decimal(["0.35", "0.45", "0.55"][i % 3]),
                    ead=Decimal(500000 + ((i * 7919) % 20) * 250000),
                )
            )
        session.commit()
        print("Loaded 40 fictional INR facilities, demo-v1, one-year horizon.")


if __name__ == "__main__":
    seed()
