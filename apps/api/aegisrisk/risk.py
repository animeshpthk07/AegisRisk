"""Transparent one-year illustrative EL, not IFRS 9 ECL or regulatory capital."""

from collections import defaultdict
from decimal import Decimal


def decimal_value(value, *, probability=False):
    value = Decimal(str(value))
    if not value.is_finite() or value < 0 or (probability and value > 1):
        raise ValueError("Values must be finite, non-negative; probabilities cannot exceed one")
    return value


def expected_loss(pd, lgd, ead):
    return (
        decimal_value(pd, probability=True)
        * decimal_value(lgd, probability=True)
        * decimal_value(ead)
    )


def summarize(rows):
    total = sum((decimal_value(row.ead) for row in rows), Decimal(0))
    el = sum((expected_loss(row.pd, row.lgd, row.ead) for row in rows), Decimal(0))
    borrowers = defaultdict(Decimal)
    for row in rows:
        borrowers[row.borrower] += row.ead
    return {
        "facility_count": len(rows),
        "total_ead": float(total),
        "total_expected_loss": float(el),
        "weighted_pd": float(sum((r.pd * r.ead for r in rows), Decimal(0)) / total)
        if total
        else None,
        "weighted_lgd": float(sum((r.lgd * r.ead for r in rows), Decimal(0)) / total)
        if total
        else None,
        "borrower_hhi": float(sum(((v / total) ** 2 for v in borrowers.values()), Decimal(0)))
        if total
        else None,
    }
